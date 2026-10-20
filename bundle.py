"""五 mod 合集：先离线生成和完整备份，再以可恢复事务写入。"""
import argparse
import ctypes
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import uuid
from contextlib import contextmanager

ROOT = Path(__file__).resolve().parent
STATE_ROOT = ROOT / '.bundle-state'
TARGETS = {'exe': 'sinking_star.exe', 'materials': 'data/materials.package',
           'outlines': 'data/mesh_outlines.mesh_outlines', 'levels': 'data/levels.package'}
ORDER = ['toggle-run', 'local-area-view', 'character-highlight', 'particle-reduction', 'world-step']
VERSION = '1.0.0-test'
MARGIN = 64 * 1024 * 1024


class BundleError(Exception):
    pass


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest() if hasattr(hashlib, 'file_digest') else _stream_sha(stream)


def _stream_sha(stream):
    digest = hashlib.sha256()
    for block in iter(lambda: stream.read(1024 * 1024), b''):
        digest.update(block)
    return digest.hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sync_write(path, data):
    with path.open('xb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def atomic_json(path, value):
    reject_link(path)
    temp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        sync_write(temp, (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf8'))
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def reject_link(path):
    if path.exists() and (path.is_symlink() or getattr(path.stat(), 'st_file_attributes', 0) & 0x400):
        raise BundleError(f'拒绝链接或重解析点 / Link or reparse point rejected: {path}')


def validate_game(path):
    game = Path(path).expanduser().absolute()
    for part in (game, game/'data', *(game/name for name in TARGETS.values())):
        reject_link(part)
    game = game.resolve(strict=True)
    for name in TARGETS.values():
        if not (game/name).is_file():
            raise BundleError(f'游戏文件缺失 / Missing game file: {name}')
    return game


def state_dir(game):
    reject_link(STATE_ROOT)
    result = STATE_ROOT / sha(os.path.normcase(str(game)).encode('utf8'))[:24]
    reject_link(result)
    return result


def validate_state(value, game):
    if value is None:
        return
    if value.get('schema') != 1 or value.get('game') != str(game) or type(value.get('active')) is not bool:
        raise BundleError('合集记录损坏或路径不符 / Invalid bundle receipt or game path')
    valid_id(value['baseline_tx'])
    for mapping in ('initial', 'installed'):
        validate_hashes(value[mapping])


def validate_hashes(mapping):
    if set(mapping) != set(TARGETS) or any(not isinstance(s, str) or not re.fullmatch('[0-9a-f]{64}', s) for s in mapping.values()):
        raise BundleError('记录的文件哈希异常 / Invalid recorded hashes')


def valid_id(value):
    if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{32}', value):
        raise BundleError('事务编号异常 / Invalid transaction ID')
    return value


def load_state(folder, game):
    path = folder/'state.json'
    reject_link(path)
    state = read_json(path) if path.exists() else None
    validate_state(state, game)
    return state


def dependency_check():
    if os.name != 'nt' or sys.version_info < (3, 10) or struct.calcsize('P') != 8:
        raise BundleError('需要 Windows x64 和 64 位 Python 3.10+ / Requires Windows x64 and 64-bit Python 3.10+')
    registry = read_json(ROOT/'bundle.json')
    if [entry['id'] for entry in registry['mods']] != ORDER or registry['version'] != VERSION:
        raise BundleError('合集清单与适配器不一致 / Registry and adapters do not match')
    lock = read_json(ROOT/'bundle-files.json')
    actual = {p.relative_to(ROOT).as_posix() for p in (ROOT/'mods').rglob('*') if p.is_file()
              and '.git' not in p.parts and '__pycache__' not in p.parts}
    if actual != set(lock):
        raise BundleError('mod 文件缺失或多出文件；请重新解压完整合集 / Mod file list differs; extract a clean complete bundle')
    for name, expected in lock.items():
        path = ROOT/name
        if path.resolve().is_relative_to((ROOT/'mods').resolve()) and not path.is_symlink() and file_sha(path) == expected:
            continue
        raise BundleError(f'发行文件校验失败 / Bundle file checksum failed: {name}')


def module(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT/relative)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def load_logic():
    # 仅载入发行目录中的原补丁逻辑，不调用其写游戏的 main。
    sys.path.insert(0, str(ROOT/'mods/character-highlight'))
    camera = module('_bundle_camera', 'mods/local-area-view/patch.py')
    highlight = module('_bundle_highlight', 'mods/character-highlight/patch.py')
    particle = module('_bundle_particle', 'mods/particle-reduction/patch.py')
    world = module('_bundle_world', 'mods/world-step/patch.py')
    return camera, highlight, particle, world


def game_running():
    # 查询失败也会阻止写入；不启动、关闭或控制游戏。
    result = subprocess.run(['tasklist.exe', '/FI', 'IMAGENAME eq sinking_star.exe', '/FO', 'CSV', '/NH'],
                            capture_output=True, check=True, timeout=30)
    return b'"sinking_star.exe"' in result.stdout.lower()


def ensure_stopped():
    if game_running():
        raise BundleError('游戏正在运行，请自行退出后重试 / Game is running; exit it yourself before retrying')


def original_highlight_resource(key, data, high):
    relative = TARGETS[key]
    if sha(data) == high.FILES[relative]:
        return data, False
    manifest = read_json(ROOT/'mods/character-highlight/manifest.json')
    if sha(data) != manifest['files'][relative]['patched_sha256']:
        raise BundleError(f'未知描边资源或网格修改 / Unknown outline resource or grid modification: {relative}')
    if key == 'materials':
        toc, entries = high.unpack(data)
        added = {f'data/materials/ch_{role}_outline.material' for role in high.COLORS}
        removed = [(n, s, o) for n, s, o in entries if n in added]
        if len(removed) != 6:
            raise BundleError('描边材质条目异常 / Invalid highlight entries')
        original_toc = min(o for n, s, o in removed)
        kept = [(n, s, o) for n, s, o in entries if n not in added]
        result = bytearray(data[:original_toc])
        header = bytearray(data[toc:toc+64])
        struct.pack_into('<Q', header, 8, len(kept))
        result.extend(header)
        for name, size, offset in kept:
            encoded = name.encode('utf8')
            result.extend(struct.pack('<I', len(encoded))+encoded+b'\0'+struct.pack('<QQ', size, offset))
        struct.pack_into('<Q', result, 16, original_toc)
        original = bytes(result)
    else:
        original = data
        for role in high.COLORS:
            original = original.replace(('ch_'+role+'_outline').encode(), b'druid_outline' if role == 'druid' else b'entity_outline')
    if sha(original) != high.FILES[relative] or high.transform(relative, original) != data:
        raise BundleError('描边资源不能精确逆变换 / Outline resources cannot be reversed exactly')
    return original, True


def toggle_run(original):
    manifest = read_json(ROOT/'mods/toggle-run/manifest.json')
    if sha(original) != manifest['original_sha256']:
        raise BundleError('基础程序版本不符 / Unsupported base executable')
    offset, size = manifest['file_offset'], manifest['size']
    before, after = bytes.fromhex(manifest['original_bytes']), bytes.fromhex(manifest['patched_bytes'])
    if len(before) != size or len(after) != size or original[offset:offset+size] != before:
        raise BundleError('奔跑补丁字段异常 / Invalid toggle-run patch bytes')
    result = original[:offset] + after + original[offset+size:]
    if sha(result) != manifest['patched_sha256']:
        raise BundleError('奔跑补丁输出校验失败 / Toggle-run output checksum failed')
    return result


def build_plan(current):
    camera, high, particle, world = load_logic()
    core = current['exe']
    world_keys = None
    if core.endswith(world.MARKER):
        core, world_keys = world.split(core)
        if world_keys != (78, 77):
            raise BundleError('合集只支持默认 N/M 按键 / Bundle requires default N/M keys')
    highlight_key = None
    if core.endswith(high.native_toggle.MARKER):
        core, highlight_key = high.native_toggle.split(core)
        if highlight_key != 80:
            raise BundleError('合集只支持默认 P 按键 / Bundle requires default P key')
    camera_version, run_enabled = camera.detect_version(core)
    if camera_version not in (0, 9):
        raise BundleError('请先用独立安装器升级或卸载旧镜头版本 / Upgrade or remove the older camera version first')
    base = camera.transform(core, False, camera_version) if camera_version else core
    run_manifest = read_json(ROOT/'mods/toggle-run/manifest.json')
    if run_enabled:
        off = run_manifest['file_offset']
        base = base[:off]+bytes.fromhex(run_manifest['original_bytes'])+base[off+run_manifest['size']:]
    if sha(base) != camera.ORIGINAL_SHA:
        raise BundleError('基础游戏版本不符或含未知修改 / Unsupported game version or unknown modifications')
    originals, outline_states = {}, []
    for key in ('materials', 'outlines'):
        originals[key], enabled = original_highlight_resource(key, current[key], high)
        outline_states.append(enabled)
    if outline_states != [highlight_key is not None]*2:
        raise BundleError('描边程序与资源状态不一致；请先用原安装器修复 / Inconsistent highlight executable/resources; repair with its original installer first')
    particle_manifest = particle.load_manifest()
    levels_hash = sha(current['levels'])
    if levels_hash not in (particle_manifest['original_sha256'], particle_manifest['patched_sha256']):
        raise BundleError('未知关卡资源版本或修改 / Unknown level package version or modification')
    particle_enabled = levels_hash == particle_manifest['patched_sha256']
    # 顺序固定：奔跑 → 镜头 → 描边 → 粒子 → 世界单步。
    exe = toggle_run(base)
    exe = camera.transform(exe, True)
    output = {key: high.transform(TARGETS[key], originals[key]) for key in originals}
    exe = high.native_toggle.apply(exe, 80)
    output['levels'] = current['levels'] if particle_enabled else particle.transform(current['levels'], particle_manifest, True)
    output['exe'] = world.apply(exe, (78, 77))
    if world.split(output['exe']) != (exe, (78, 77)):
        raise BundleError('世界单步输出不能精确撤销 / World-step output cannot be reversed exactly')
    return output, dict(zip(ORDER, [run_enabled, camera_version == 9, highlight_key is not None, particle_enabled, world_keys is not None]))


def validate_image(data):
    # 不调用可执行文件入口，也不启动游戏。
    import tempfile
    with tempfile.TemporaryDirectory(prefix='bundle-image-', dir=ROOT) as directory:
        folder = Path(directory).resolve()
        if not folder.is_relative_to(ROOT):
            raise BundleError('临时映像路径异常 / Invalid temporary image path')
        path = folder/'image.exe'
        path.write_bytes(data)
        kind = ctypes.c_uint32()
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.GetBinaryTypeW.argtypes = [ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_uint32)]
        if not kernel.GetBinaryTypeW(str(path), ctypes.byref(kind)) or kind.value != 6:
            raise BundleError('Windows 拒绝生成的 x64 映像 / Windows rejected the generated x64 image')


def read_current(game):
    return {key: (game/name).read_bytes() for key, name in TARGETS.items()}


def current_hashes(game):
    return {key: file_sha(game/name) for key, name in TARGETS.items()}


def capacity_check(game, folder, current, output):
    parent = folder
    while not parent.exists():
        parent = parent.parent
    if not os.access(parent, os.W_OK):
        raise BundleError('备份目录不可写 / Backup directory is not writable')
    changed = [key for key in TARGETS if sha(current[key]) != sha(output[key])]
    backup_need = sum(len(v) for v in current.values()) + sum(len(output[k]) for k in changed) + MARGIN
    game_need = max((len(output[k]) for k in changed), default=0) + MARGIN
    if parent.anchor.lower() == game.anchor.lower():
        if shutil.disk_usage(parent).free < backup_need + game_need:
            raise BundleError('备份和临时文件空间不足 / Insufficient backup/staging space')
    elif shutil.disk_usage(parent).free < backup_need or shutil.disk_usage(game).free < game_need:
        raise BundleError('备份盘或游戏盘空间不足 / Insufficient backup-drive or game-drive space')
    for name in TARGETS.values():
        if not os.access(game/name, os.W_OK) or not os.access((game/name).parent, os.W_OK):
            raise BundleError(f'游戏路径不可写 / Game path is not writable: {name}')


@contextmanager
def operation_lock(folder):
    import msvcrt
    folder.mkdir(parents=True, exist_ok=True)
    lock = folder/'operation.lock'
    reject_link(lock)
    with lock.open('a+b') as stream:
        stream.seek(0, 2)
        if stream.tell() == 0:
            stream.write(b'0')
            stream.flush()
        stream.seek(0)
        try:
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as error:
            raise BundleError('另一个合集操作正在运行 / Another bundle operation is running') from error
        try:
            yield
        finally:
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)


def journal(folder, txid, game):
    txid = valid_id(txid)
    directory = folder/'transactions'/txid
    reject_link(folder/'transactions')
    reject_link(directory)
    value = read_json(directory/'journal.json')
    if value.get('schema') != 1 or value.get('id') != txid or value.get('game') != str(game):
        raise BundleError('事务记录不符 / Invalid transaction journal')
    for field in ('before', 'after'):
        validate_hashes(value[field])
    validate_state(value['previous_state'], game)
    return directory, value


def replace_from(target, source, expected, desired, txid, key):
    reject_link(target)
    reject_link(source)
    temp = target.with_name(target.name+'.bundle-'+txid+'-'+key+'.tmp')
    created = False
    try:
        with source.open('rb') as inp, temp.open('xb') as out:
            created = True
            shutil.copyfileobj(inp, out, 1024*1024)
            out.flush()
            os.fsync(out.fileno())
        if file_sha(temp) != desired or file_sha(target) != expected:
            raise BundleError('写入前文件发生变化 / File changed during write preflight')
        ensure_stopped()
        os.replace(temp, target)
        if file_sha(target) != desired:
            raise BundleError('写入后校验失败 / Post-write checksum failed')
    finally:
        if created:
            temp.unlink(missing_ok=True)


def restore_pending(game, folder):
    pending_path = folder/'pending.json'
    reject_link(pending_path)
    if not pending_path.exists():
        return False
    txid = read_json(pending_path)['id']
    directory, info = journal(folder, txid, game)
    ensure_stopped()
    actual = current_hashes(game)
    for key in TARGETS:
        source = directory/(key+'.before')
        reject_link(source)
        if file_sha(source) != info['before'][key]:
            raise BundleError('恢复备份损坏；拒绝写入 / Recovery backup damaged; refusing to write')
        if actual[key] not in (info['before'][key], info['after'][key]):
            raise BundleError('中断后文件含未知修改；保留备份并停止 / Unknown post-interruption changes; backups retained')
    required = max((directory/(key+'.before')).stat().st_size for key in TARGETS) + MARGIN
    if shutil.disk_usage(game).free < required:
        raise BundleError('恢复所需游戏盘空间不足 / Insufficient game-drive space for recovery')
    for key, relative in TARGETS.items():
        scratch = (game/relative).with_name(Path(relative).name+'.bundle-'+txid+'-'+key+'.tmp')
        reject_link(scratch)
        # 仅清理此未完成事务在游戏目标旁创建的准确临时文件名。
        scratch.unlink(missing_ok=True)
    # 全部备份和全部当前文件通过验证后才恢复；可安全重复执行。
    for key in reversed(list(TARGETS)):
        if actual[key] != info['before'][key]:
            replace_from(game/TARGETS[key], directory/(key+'.before'), actual[key], info['before'][key], txid, key)
    if current_hashes(game) != info['before']:
        raise BundleError('恢复结果不符 / Recovery verification failed')
    atomic_json(folder/'state.json', info['previous_state'])
    info['phase'] = 'rolled_back'
    atomic_json(directory/'journal.json', info)
    pending_path.unlink()
    return True


def transaction(game, folder, current, output, state, action):
    ensure_stopped()
    before = {k: sha(v) for k, v in current.items()}
    after = {k: sha(v) for k, v in output.items()}
    capacity_check(game, folder, current, output)
    txid = uuid.uuid4().hex
    directory = folder/'transactions'/txid
    reject_link(folder/'transactions')
    directory.mkdir(parents=True, exist_ok=False)
    for key in TARGETS:
        sync_write(directory/(key+'.before'), current[key])
        if before[key] != after[key]:
            sync_write(directory/(key+'.after'), output[key])
        if file_sha(directory/(key+'.before')) != before[key] or (
                before[key] != after[key] and file_sha(directory/(key+'.after')) != after[key]):
            raise BundleError('写入前备份或暂存校验失败 / Backup or staging verification failed')
    info = dict(schema=1, id=txid, game=str(game), action=action, before=before, after=after,
                previous_state=state, phase='prepared')
    atomic_json(directory/'journal.json', info)
    if current_hashes(game) != before:
        raise BundleError('游戏文件在预检后变化，未写入 / Game changed after preflight; no game files written')
    ensure_stopped()
    atomic_json(folder/'pending.json', {'id': txid})
    try:
        for key in TARGETS:
            if before[key] != after[key]:
                replace_from(game/TARGETS[key], directory/(key+'.after'), before[key], after[key], txid, key)
        if current_hashes(game) != after:
            raise BundleError('事务最终文件校验失败 / Final transaction verification failed')
        if action == 'install':
            next_state = dict(schema=1, game=str(game), version=VERSION, active=True,
                              baseline_tx=txid, initial=before, installed=after)
        else:
            next_state = dict(state, active=False)
        atomic_json(folder/'state.json', next_state)
        info['phase'] = 'committed'
        atomic_json(directory/'journal.json', info)
        (folder/'pending.json').unlink()
    except Exception as error:
        try:
            restore_pending(game, folder)
        except Exception as recovery_error:
            raise BundleError(f'操作中断，自动恢复未完成；退出游戏后运行 recover.cmd。保留整个合集目录。 / Operation interrupted; recovery pending. Exit the game and run recover.cmd. Keep the complete bundle folder.\n{recovery_error}') from error
        raise BundleError(f'安装或卸载失败，已精确恢复本次操作前状态 / Operation failed; the pre-operation state was restored.\n{error}') from error


def operate(action, game):
    dependency_check()
    game = validate_game(game)
    folder = state_dir(game)
    if action in ('install', 'uninstall', 'recover', 'check'):
        ensure_stopped()
    # status 和 check 不创建目录、锁、备份或收据。
    if action in ('status', 'check'):
        if (folder/'pending.json').exists():
            raise BundleError('存在未完成事务，请退出游戏后运行 recover.cmd / Unfinished transaction; exit the game and run recover.cmd')
        state = load_state(folder, game)
        current = read_current(game)
        if state and state['active'] and {k: sha(v) for k, v in current.items()} != state['installed']:
            raise BundleError('安装后文件已改变；拒绝覆盖 / Files changed after bundle installation; refusing to overwrite')
        output, installed = build_plan(current)
        if action == 'check':
            validate_image(output['exe'])
            capacity_check(game, folder, current, output)
        print(json.dumps({'game': str(game), 'bundle_active': bool(state and state['active']),
                          'installed_mods': installed, 'action': action, 'result': 'OK'}, ensure_ascii=False, indent=2))
        return
    with operation_lock(folder):
        if action == 'recover':
            changed = restore_pending(game, folder)
            print('中断事务已恢复 / Interrupted operation restored' if changed else '无待恢复事务 / No pending recovery')
            return
        if (folder/'pending.json').exists():
            raise BundleError('存在未完成事务；先运行 recover.cmd / Recover the unfinished operation first')
        state = load_state(folder, game)
        current = read_current(game)
        actual = {k: sha(v) for k, v in current.items()}
        if state and state['active'] and actual != state['installed']:
            raise BundleError('安装后文件已变化；拒绝覆盖 / Files changed since installation; refusing to overwrite')
        if action == 'install':
            output, installed = build_plan(current)
            if state and state['active']:
                if {k: sha(v) for k, v in output.items()} != actual:
                    raise BundleError('已安装收据与当前合集不符 / Receipt does not match this bundle version')
                print('合集已完整安装，未重复写入或替换首次备份 / Already installed; no writes and original baseline retained')
                return
            validate_image(output['exe'])
            print('预检通过；已存在 / Preflight passed; already present: '+', '.join(k for k,v in installed.items() if v))
        else:
            if not state or not state['active']:
                print('本目录没有活动合集安装；未改动独立 mod / No active bundle installation here; standalone mods unchanged')
                return
            directory, baseline = journal(folder, state['baseline_tx'], game)
            if baseline['action'] != 'install' or baseline['before'] != state['initial']:
                raise BundleError('初始备份记录不符 / Initial backup record mismatch')
            output = {}
            for key in TARGETS:
                source = directory/(key+'.before')
                reject_link(source)
                output[key] = source.read_bytes()
                if sha(output[key]) != state['initial'][key]:
                    raise BundleError('初始备份损坏，拒绝卸载 / Initial backup damaged; refusing to uninstall')
        transaction(game, folder, current, output, state, action)
        print('合集安装完成 / Bundle installed' if action == 'install' else '已精确恢复合集安装前状态（保留先前已有 mod） / Restored exact pre-bundle state, including previously installed mods')


def discover_game():
    candidates = [Path(r'D:\Program Files (x86)\Steam\steamapps\common\Order of the Sinking Star')]
    steam_roots = []
    try:
        import winreg
        for hive, subkey, name in ((winreg.HKEY_CURRENT_USER, r'Software\Valve\Steam', 'SteamPath'),
                                  (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\WOW6432Node\Valve\Steam', 'InstallPath')):
            try:
                with winreg.OpenKey(hive, subkey) as key:
                    steam_roots.append(Path(winreg.QueryValueEx(key, name)[0]))
            except OSError:
                pass
    except ImportError:
        pass
    for steam in steam_roots:
        candidates.append(steam/'steamapps/common/Order of the Sinking Star')
        libraries = steam/'steamapps/libraryfolders.vdf'
        if libraries.is_file():
            for value in re.findall(r'"path"\s+"([^"\r\n]+)"', libraries.read_text(encoding='utf8')):
                candidates.append(Path(value.replace('\\\\', '\\'))/'steamapps/common/Order of the Sinking Star')
    found = {os.path.normcase(str(p.resolve())): p.resolve() for p in candidates if (p/'sinking_star.exe').is_file()}
    if len(found) == 1:
        return next(iter(found.values()))
    if sys.stdin.isatty():
        return Path(input('请输入游戏目录 / Enter the game directory: ').strip().strip('"'))
    raise BundleError('未能唯一定位游戏；请指定 --game-dir / Specify --game-dir to identify the game')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('install','uninstall','recover','status','check'), nargs='?', default='install')
    parser.add_argument('--game-dir', type=Path)
    args = parser.parse_args()
    try:
        operate(args.action, args.game_dir or discover_game())
    except (BundleError, OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError, struct.error) as error:
        print('操作停止 / Operation stopped: '+str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
