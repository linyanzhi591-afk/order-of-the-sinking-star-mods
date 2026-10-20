"""六职业彩色描边与实时开关，保留已知奔跑、镜头及网格补丁。"""
import argparse
import hashlib
import os
import struct
import subprocess
from pathlib import Path
import grid_compat
import native_toggle
import grid_native

ROOT = Path(__file__).resolve().parent
GAME = Path(r'D:\Program Files (x86)\Steam\steamapps\common\Order of the Sinking Star')
FILES = {
    'data/materials.package': 'dffd12a4f1002dc2f309d5b85205b432c1d7213764c798ccb693cd0ef5f1afc6',
    'data/mesh_outlines.mesh_outlines': '363fd47bb37fd9b98e77c8c7f81a1215285ca14964b197c1dc264896f1a38107',
}
COLORS = {
    'warrior': ('战士', '#B31616', ('warrior',)),
    'thief': ('盗贼', '#16B32D', ('thief', 'thief_alt')),
    'wizard': ('法师', '#2243B3', ('wizard', 'wizard_alt')),
    'cleric': ('牧师', '#B3B316', ('cleric', 'cleric_alt')),
    'bard': ('吟游诗人', '#862DB3', ('bard',)),
    'druid': ('德鲁伊', '#546B6F', ('druid',)),
}
LEGACY_MATERIAL_SHA = '1b4a5c07da672c756cf5d84507771a29a22e01e5380aa14656407e813b894e95'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def unpack(data):
    if data[:8] != b'simp\x01\0\0\0':
        raise ValueError('不支持的资源包格式')
    toc = struct.unpack_from('<Q', data, 16)[0]
    if data[toc:toc+4] != b'toc!':
        raise ValueError('资源包目录缺失')
    count = struct.unpack_from('<Q', data, toc+8)[0]
    if count > 100000:
        raise ValueError('资源包条目过多')
    pos, entries = toc+64, []
    for _ in range(count):
        length = struct.unpack_from('<I', data, pos)[0]
        pos += 4
        name = data[pos:pos+length].decode('utf8')
        if data[pos+length] != 0:
            raise ValueError('资源名称终止符无效')
        pos += length+1
        size, offset = struct.unpack_from('<QQ', data, pos)
        pos += 16
        if offset < 64 or offset+size > toc:
            raise ValueError('资源条目越界')
        entries.append((name, size, offset))
    if pos != len(data) or len({e[0] for e in entries}) != count:
        raise ValueError('资源包目录长度或名称异常')
    return toc, entries


def material(role):
    color = COLORS[role][1].lstrip('#')
    # 材质颜色为线性空间；将指定的屏幕 sRGB 色值转换后写入。
    def linear(v):
        v = int(v, 16)/255
        return v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4
    rgb = ' '.join(f'{linear(color[i:i+2]):.7f}' for i in (0, 2, 4))
    parent = 'druid_outline' if role == 'druid' else 'entity_outline'
    # 父材质依赖确保关闭时所需的原版描边同时加载。
    return (f'# material version 1\nparent "{parent}"\nshader "entity_outline"\nflag Dynamic\n'
            f'outline_depth_modifier 1\noutline_z_cutoff 0.337423\n'
            f'outline_color ({rgb} 1)\nminimum_outline_intensity 1\n'
            f'gradient_texture "RAMP_OutlineThickness_A"\noutline_width 5\n'
            f'use_exponential_thinning false\nthinning_mode 1\n').encode('ascii')


def transform(relative, data):
    if sha(data) != FILES[relative]:
        raise ValueError(f'基础资源版本不匹配：{relative}')
    if relative.endswith('.package'):
        toc, entries = unpack(data)
        result = bytearray(data[:toc])
        for role in COLORS:
            content = material(role)
            entries.append((f'data/materials/ch_{role}_outline.material', len(content), len(result)))
            result.extend(content)
        new_toc = len(result)
        header = bytearray(data[toc:toc+64])
        struct.pack_into('<Q', header, 8, len(entries))
        result.extend(header)
        for name, size, offset in sorted(entries):
            encoded = name.encode('utf8')
            result.extend(struct.pack('<I', len(encoded))+encoded+b'\0'+struct.pack('<QQ', size, offset))
        struct.pack_into('<Q', result, 16, new_toc)
        unpack(result)
        return bytes(result)
    mappings = {mesh: f'ch_{role}_outline' for role, (_, _, meshes) in COLORS.items() for mesh in meshes}
    found, result = set(), []
    for line in data.decode('ascii').splitlines(keepends=True):
        parts = line.split()
        if parts and parts[0] in mappings:
            mesh = parts[0]
            if mesh in found or len(parts) != 2:
                raise ValueError('角色描边映射重复或无效')
            found.add(mesh)
            line = line.replace(parts[1], mappings[mesh], 1)
        result.append(line)
    if found != set(mappings):
        raise ValueError('角色模型映射缺失')
    return ''.join(result).encode('ascii')


def originals(game=None):
    result = {}
    for name, digest in FILES.items():
        backup = ROOT/'original'/Path(name).name
        if backup.exists():
            data = backup.read_bytes()
        elif game is not None:
            # 公开包不携带原版资源；首次安装从玩家自己的游戏读取。
            data = (game/name).read_bytes()
        else:
            raise ValueError('缺少本机原始资源备份；首次安装请指定未修改资源的游戏目录')
        if sha(data) != digest:
            raise ValueError(f'原始资源校验失败：{name}；首次安装须使用原版资源，旧版用户请先用旧安装器卸载，或保留其 original 备份')
        result[name] = data
    return result


def save_originals(base):
    folder = ROOT/'original'
    folder.mkdir(exist_ok=True)
    for name, data in base.items():
        backup = folder/Path(name).name
        if not backup.exists():
            with backup.open('xb') as stream:
                stream.write(data)
        if sha(backup.read_bytes()) != FILES[name]:
            raise ValueError(f'原始资源备份校验失败：{name}')


def state(game, base):
    current, enabled = {}, []
    grid_enabled = False
    for name in FILES:
        data = (game/name).read_bytes()
        actual = data
        if name.endswith('.package'):
            data, grid_enabled = grid_compat.split(data, base[name])
        patched = transform(name, base[name])
        legacy = name.endswith('.package') and sha(data) in (LEGACY_MATERIAL_SHA, '42cc6b62b3c672c08b37fd8abb060edf372e443121f9b691250185110113fc67')
        if data not in (base[name], patched) and not legacy:
            raise ValueError(f'检测到未知资源修改，拒绝覆盖：{name}')
        current[name] = actual
        enabled.append(data == patched or legacy)
    return current, enabled, grid_enabled


def write_pair(game, replacements, previous):
    # 全部预检后写入；第二个文件失败时恢复本次已写入的文件。
    written = []
    try:
        for name, data in replacements.items():
            path = game/name
            if path.read_bytes() != previous[name]:
                raise ValueError(f'资源文件在预检后发生变化，拒绝覆盖：{name}')
            temp = path.with_name(path.name+'.character-highlight.tmp')
            with temp.open('xb') as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            try:
                os.replace(temp, path)
            finally:
                if temp.exists():
                    temp.unlink()
            written.append(name)
    except Exception:
        for name in reversed(written):
            (game/name).write_bytes(previous[name])
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('install', 'restore', 'status'))
    parser.add_argument('--game-dir', type=Path, default=GAME)
    args = parser.parse_args()
    base = originals(args.game_dir)
    current, enabled, grid_enabled = state(args.game_dir, base)
    exe = (args.game_dir/'sinking_star.exe').read_bytes()
    exe_without_grid, grid_key = grid_native.split(exe)
    exe_base, toggle_key = native_toggle.split(exe_without_grid)
    if args.action == 'status':
        if sha(grid_compat.split(current['data/materials.package'], base['data/materials.package'])[0]) == LEGACY_MATERIAL_SHA:
            print('六职业描边：已安装旧版 v0.1.0，可运行 install 升级')
            return
        print('六职业描边：'+('已安装' if all(enabled) else '未安装' if not any(enabled) else '部分安装，请重新安装或恢复'))
        print('实时开关：'+('未安装' if toggle_key is None else f'已安装，虚拟键码 {toggle_key}'))
        return
    # 游戏运行期间禁止修改资源，避免缓存与文件状态不一致。
    processes = subprocess.run(['powershell', '-NoProfile', '-Command',
        "$ErrorActionPreference='Stop'; if (Get-Process -Name sinking_star -ErrorAction SilentlyContinue) { exit 10 }; exit 0"], capture_output=True)
    if processes.returncode not in (0, 10):
        raise ValueError('无法查询游戏进程，拒绝修改资源')
    if processes.returncode == 10:
        raise ValueError('请正常退出游戏后再安装或卸载')
    replacements = {name: transform(name, data) if args.action == 'install' else data for name, data in base.items()}
    if grid_enabled:
        name = 'data/materials.package'
        replacements[name] = grid_compat.enable(replacements[name], base[name])
    # 主程序与资源作为同一事务写入，失败时恢复本次输入。
    current['sinking_star.exe'] = exe
    new_key = native_toggle.config() if args.action == 'install' else None
    if new_key is not None and new_key == grid_key:
        raise ValueError('高亮按键与网格按键相同，请修改 toggle_config.json 后重新安装')
    replacements['sinking_star.exe'] = native_toggle.apply(exe_base, new_key) if new_key is not None else exe_base
    if grid_key is not None:
        replacements['sinking_star.exe'] = grid_native.apply(replacements['sinking_star.exe'], grid_key)
    save_originals(base)
    write_pair(args.game_dir, replacements, current)
    for name, data in replacements.items():
        if (args.game_dir/name).read_bytes() != data:
            raise ValueError(f'写入验证失败：{name}')
    assert native_toggle.split(grid_native.split((args.game_dir/'sinking_star.exe').read_bytes())[0])[0] == exe_base
    print('六职业彩色描边及实时开关'+('安装完成' if args.action == 'install' else '已卸载')+'；保留网格状态及原有奔跑、俯视 mod。')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, struct.error) as error:
        print('操作失败：', error)
        raise SystemExit(1)
