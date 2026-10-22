"""复用合集已验证的备份、事务和恢复机制，仅管理水面程序与着色器。"""
import ctypes
import hashlib
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
STATE_ROOT = ROOT/'.bundle-state'
TARGETS = {'exe':'sinking_star.exe','shaders':'data/shaders.package'}
VERSION = '0.1.0'
MARGIN = 64*1024*1024

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


def game_running():
    # 查询失败也会阻止写入；不启动、关闭或控制游戏。
    result = subprocess.run(['tasklist.exe', '/FI', 'IMAGENAME eq sinking_star.exe', '/FO', 'CSV', '/NH'],
                            capture_output=True, check=True, timeout=30)
    return b'"sinking_star.exe"' in result.stdout.lower()


def ensure_stopped():
    if game_running():
        raise BundleError('游戏正在运行，请自行退出后重试 / Game is running; exit it yourself before retrying')


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
