"""局部俯视补丁：严格校验版本，按字节叠加，并保留奔跑补丁。"""
import argparse
import hashlib
import struct
import base64
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
GAME = Path(r'D:\Program Files (x86)\Steam\steamapps\common\Order of the Sinking Star')
ORIGINAL_SHA = '0ae10a513dae25286fe93d0db4fa8a2df9a473bc07e1734e12bc1ad30166db1c'
RUN_SHA = 'bda4419d1f7e7a79f9aaa3e069ae32fe3e19a827afd8bfb3e21cbab534c60505'
PAYLOAD_PATH = ROOT / 'camera_payload.json'
PAYLOAD_SHA = 'd45eba9edd894df84e573b59f5ed228b8186f03086503daf2bef76e9f81e64c4'
LEGACY_PAYLOAD_PATH = ROOT / 'camera_payload_v4.json'
LEGACY_PAYLOAD_SHA = 'd18571355195603fd8280faaf859fab6dc963b088159bcfdd975864c5ab44328'
BASE_SIZE = 12327936


def split_extras(data):
    import grid_native
    import highlight_native
    import static_native
    # 无附加层时仍允许旧俯视版本，由本安装器继续严格验证。
    grid_key = highlight_key = None
    # 仅在确有外层网格标记时拆分；旧俯视版本本身不属于高亮白名单。
    if data.endswith(grid_native.MARKER) or data.endswith(static_native.MARKER):
        data, grid_key = grid_native.split(data)
    if data.endswith(highlight_native.MARKER):
        data, highlight_key = highlight_native.split(data)
    return data, highlight_key, grid_key


def add_extras(data, highlight_key, grid_key):
    import grid_native
    import highlight_native
    if highlight_key is not None:
        data = highlight_native.apply(data, highlight_key)
    if grid_key is not None:
        data = grid_native.apply(data, grid_key)
    return data


def payload(version=9):
    if version == 8:
        data = PAYLOAD_PATH.with_name('camera_payload_v8.json').read_bytes()
        if sha(data) != 'b82a5216b1df9f594d05d5a19f29ae066ffe4130672f6358d22713a565ee0f61':
            raise ValueError('旧镜头载荷校验失败')
        return json.loads(data)
    if version == 7:
        data = PAYLOAD_PATH.with_name('camera_payload_v7.json').read_bytes()
        if sha(data) != '5fd129f0aaf29b498ecf925e2bd69eb359677fecdf0b976b7aea9acd0db3977f':
            raise ValueError('旧镜头载荷校验失败')
        return json.loads(data)
    if version == 6:
        data = PAYLOAD_PATH.with_name('camera_payload_v6.json').read_bytes()
        if sha(data) != 'eeedba26a73bfdbba12f62f62568dcef6909a87dcc46af4b7729f5e08b2fa76b':
            raise ValueError('旧镜头载荷校验失败')
        return json.loads(data)
    if version == 5:
        data = PAYLOAD_PATH.with_name('camera_payload_v5.json').read_bytes()
        if sha(data) != '11c7e51852c5f0f5698818adf506c193b3a2f217c2f6e53fc1b07516022a793e':
            raise ValueError('旧镜头载荷校验失败')
        return json.loads(data)
    legacy = version in (3, 4)
    data = (LEGACY_PAYLOAD_PATH if legacy else PAYLOAD_PATH).read_bytes()
    if sha(data) != (LEGACY_PAYLOAD_SHA if legacy else PAYLOAD_SHA):
        raise ValueError('镜头载荷校验失败，拒绝安装。')
    return json.loads(data)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def jump(source, target):
    return b'\xe9' + struct.pack('<i', target - source - 5)


def definitions(version=9):
    if version in (3, 4, 5, 6, 7, 8, 9):
        symbols = payload(version)['symbols']
        return [
            (0x23A820, bytes.fromhex('415741564154'), jump(0x23A820, symbols['hook_toggle']) + b'\x90'),
            (0x25D7C0, bytes.fromhex('415741564155'), jump(0x25D7C0, symbols['hook_begin']) + b'\x90'),
            (0x276B66, bytes.fromhex('4c8b742478'), jump(0x276B66, symbols['hook_end'])),
        ]
    # Q 的原有序言和输入锁保留，随后直接进入原生局部视图的 0/2 切换分支。
    # 被跳过的 Q 专用扫描代码中放置辅助代码，不扩展 PE 节或改动重定位。
    cave = 0x23A880
    hook = 0x26A0F9
    original_load = bytes.fromhex('0fb6b6a2030000')
    helper = original_load + bytes.fromhex('4180bdd43d0000027505be01000000')
    helper += jump(cave + len(helper), hook + 7)
    patches = [
        (0x23A840, bytes.fromhex('4c8d442440'), jump(0x23A840, 0x23A950)),
        (cave, bytes.fromhex('488d44243848894424204889f94889f24531c04531c9e8158c0400488b5c2438'), helper.ljust(32, b'\x90')),
        (hook, original_load, jump(hook, cave) + b'\x90\x90'),
    ]
    if version == 2:
        # 缺少专用镜头时，仅保留局部模式 2；远距离模式 1 仍按原逻辑重置。
        patches.append((0x43D53C, b'\x77', b'\x73'))
    elif version != 1:
        raise ValueError('未知补丁版本')
    return patches


def transform(data, enable, version=9):
    result = bytearray(data)
    for rva, before, after in definitions(version):
        off = rva - 0xC00
        expected, replacement = (before, after) if enable else (after, before)
        if result[off:off + len(expected)] != expected:
            raise ValueError(f'补丁字节不匹配：RVA {rva:#x}')
        result[off:off + len(expected)] = replacement
    if version in (3, 4, 5, 6, 7, 8, 9):
        # 新版完全撤销旧版的原生局部相机补丁，单独添加显示变换代码。
        # 保留原节及其全部内容；卸载时恢复原 PE 头和文件长度。
        if enable:
            if len(result) != BASE_SIZE or result[0x2C0:0x338] != bytes(120):
                raise ValueError('PE 节表或文件长度不匹配。')
            sections = payload(version)['sections']
            for i, section in enumerate(sections):
                raw = base64.b64decode(section['data'])
                offset = len(result)
                rawsize = (len(raw)+511) & ~511
                result += raw.ljust(rawsize, b'\0')
                # Windows 映像加载器要求虚拟节范围连续；覆盖链接时留下的对齐空隙。
                virtual_size = section['size']
                if version >= 4 and i + 1 < len(sections):
                    virtual_size = sections[i+1]['rva'] - section['rva']
                struct.pack_into('<8sIIIIIIHHI', result, 0x2C0+i*40,
                                 section['name'].encode(), virtual_size, section['rva'],
                                 rawsize, offset, 0, 0, 0, 0, section['flags'])
            struct.pack_into('<H', result, 0x7E, 11)
            struct.pack_into('<I', result, 0xC8, 0x1140000)
        else:
            result = result[:BASE_SIZE]
            result[0x2C0:0x338] = bytes(120)
            struct.pack_into('<H', result, 0x7E, 8)
            struct.pack_into('<I', result, 0xC8, 0x113C000)
    return bytes(result)


def detect_version(data):
    digest = sha(data)
    if digest in (ORIGINAL_SHA, RUN_SHA):
        return 0, digest == RUN_SHA
    for version in (9, 8, 7, 6, 5, 4, 3, 2, 1):
        try:
            baseline = transform(data, False, version)
        except ValueError:
            continue
        digest = sha(baseline)
        if digest in (ORIGINAL_SHA, RUN_SHA):
            if version in (3, 4, 5, 6, 7, 8, 9) and transform(baseline, True, version) != data:
                continue
            return version, digest == RUN_SHA
    raise ValueError('未知游戏版本或补丁以外的程序字节不匹配，拒绝操作。')


def identify(data):
    version, running = detect_version(data)
    return version != 0, running


def game_running():
    # 使用进程查询，避免安装时覆盖运行中的游戏。
    import subprocess
    result = subprocess.run(['powershell', '-NoProfile', '-Command',
                             "$ErrorActionPreference='Stop'; if (Get-Process -Name sinking_star -ErrorAction SilentlyContinue) { exit 10 }; exit 0"],
                            capture_output=True)
    if result.returncode not in (0, 10):
        raise RuntimeError('无法查询游戏进程，拒绝写入。')
    return result.returncode == 10


def validate_windows_image(data):
    """写入游戏前让 Windows 检查映像；不启动程序。"""
    import ctypes as C
    import tempfile
    kernel = C.WinDLL('kernel32', use_last_error=True)
    kernel.GetBinaryTypeW.argtypes = [C.c_wchar_p, C.POINTER(C.c_uint32)]
    with tempfile.TemporaryDirectory(dir=ROOT, prefix='tmp-image-') as directory:
        path = Path(directory) / 'image.exe'
        path.write_bytes(data)
        kind = C.c_uint32()
        if not kernel.GetBinaryTypeW(str(path), C.byref(kind)) or kind.value != 6:
            raise ValueError(f'Windows 拒绝加载生成的程序，未安装。错误码：{C.get_last_error()}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['status', 'install', 'restore', 'build'])
    parser.add_argument('--game-dir', type=Path, default=GAME)
    parser.add_argument('--source', type=Path)
    args = parser.parse_args()
    target = args.source or args.game_dir / 'sinking_star.exe'
    data = target.read_bytes()
    core, highlight_key, grid_key = split_extras(data)
    version, running = detect_version(core)
    enabled = version != 0
    if args.action == 'status':
        status = '已安装 v0.1.9' if version == 9 else ('已安装旧版（需要升级）' if version else '未安装')
        print(f'局部俯视：{status}；奔跑切换：{"已安装" if running else "未安装"}')
        return
    if args.action == 'build':
        baseline = transform(core, False, version) if enabled else core
        output = add_extras(transform(baseline, True), highlight_key, grid_key)
        validate_windows_image(output)
        dest = ROOT / ('sinking_star.local-area-and-run.exe' if running else 'sinking_star.local-area.exe')
        dest.write_bytes(output)
        print(f'已生成：{dest.name}；SHA-256：{sha(output)}')
        return
    if args.source:
        parser.error('--source 仅适用于 status/build')
    desired = args.action == 'install'
    if (desired and version == 9) or (not desired and version == 0):
        print('已处于目标状态，未修改文件。')
        return
    if game_running():
        raise SystemExit('请先关闭游戏。')
    baseline = transform(core, False, version) if enabled else core
    output = transform(baseline, True) if desired else baseline
    assert identify(output) == (desired, running)
    output = add_extras(output, highlight_key, grid_key)
    validate_windows_image(output)
    backup = ROOT / f'sinking_star.backup-{sha(data)}.exe'
    if backup.exists():
        if backup.read_bytes() != data:
            raise SystemExit('现有备份内容异常，拒绝覆盖。')
    else:
        with backup.open('xb') as stream:
            stream.write(data)
    if target.read_bytes() != data:
        raise SystemExit('游戏文件已变化，拒绝写入。')
    # 保持文件身份和权限；先备份，失败时仅尝试恢复本次输入。
    try:
        with target.open('r+b') as stream:
            stream.write(output)
            stream.truncate()
            stream.flush()
        if target.read_bytes() != output:
            raise OSError('写入校验失败')
    except Exception:
        target.write_bytes(data)
        raise
    print(f'{"安装" if desired else "卸载"}完成；奔跑切换状态已保留。备份：{backup.name}')


if __name__ == '__main__':
    main()
