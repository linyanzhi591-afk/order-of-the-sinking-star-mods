"""使用本机 MinGW 构建无导入、无重定位的镜头代码。日常安装不需要编译器。"""
import base64
import json
import struct
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BIN = Path(r'C:\Program Files (x86)\mingw64\bin')


def build():
    with tempfile.TemporaryDirectory(dir=ROOT, prefix='tmp-build-') as tmp:
        tmp = Path(tmp)
        for name in ('camera_hooks.S', 'camera_view.c'):
            subprocess.run([str(BIN/'gcc.exe'), '-c', '-O2', '-ffreestanding',
                            '-fno-stack-protector', '-fno-asynchronous-unwind-tables',
                            '-fno-ident', '-fno-tree-loop-distribute-patterns',
                            str(ROOT/name), '-o', str(tmp/(name+'.o'))], check=True)
        exe = tmp/'payload.exe'
        subprocess.run([str(BIN/'ld.exe'), '-mi386pep', '--image-base', '0',
                        '--section-start', '.text=0x113c000',
                        '--section-start', '.data=0x113e000',
                        '--section-start', '.rdata=0x113f000',
                        '--defsym', 'game_state=0xb69600',
                        '--defsym', 'return_begin=0x25d7c6',
                        '--defsym', 'return_end=0x276b6b',
                        '--defsym', 'return_toggle=0x23a826',
                        '--defsym', 'current_level=0x2e21e0',
                        '--entry', 'hook_toggle', '--disable-auto-import',
                        str(tmp/'camera_hooks.S.o'), str(tmp/'camera_view.c.o'),
                        '-o', str(exe)], check=True)
        b = exe.read_bytes()
        pe = struct.unpack_from('<I', b, 60)[0]
        count = struct.unpack_from('<H', b, pe+6)[0]
        # 未解析导入及绝对地址重定位都不允许进入载荷。
        assert struct.unpack_from('<II', b, pe+24+112+5*8) == (0, 0)
        table = pe+24+struct.unpack_from('<H', b, pe+20)[0]
        sections = []
        names = {'.text': '.lvcode', '.data': '.lvdata', '.rdata': '.lvconst'}
        for i in range(count):
            off = table+i*40
            name, size, rva, rawsize, raw = struct.unpack_from('<8sIIII', b, off)
            name = name.rstrip(b'\0').decode()
            if name == '.idata':
                assert not any(b[raw:raw+size])
                continue
            assert name in names
            sections.append(dict(name=names[name], rva=rva, size=size,
                                 flags=struct.unpack_from('<I', b, off+36)[0],
                                 data=base64.b64encode(b[raw:raw+size]).decode()))
        symbols = {}
        for line in subprocess.check_output([str(BIN/'nm.exe'), str(exe)], text=True).splitlines():
            fields = line.split()
            if len(fields) == 3 and fields[2] in (
                    'hook_toggle', 'hook_begin', 'hook_end', 'toggle_view', 'frame_begin', 'frame_end', 'view'):
                symbols[fields[2]] = int(fields[0], 16)
        assert len(symbols) == 7
        (ROOT/'camera_payload.json').write_text(json.dumps(
            dict(sections=sections, symbols=symbols), indent=2)+'\n', encoding='utf-8')
        print('载荷已生成，无外部导入或绝对地址重定位。')


if __name__ == '__main__':
    build()
