"""构建无新增导入的描边开关载荷，仅开发时需要 MinGW。"""
import base64
import hashlib
import json
import struct
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BIN = Path(r'C:\Program Files (x86)\mingw64\bin')


def build():
    variants = {}
    with tempfile.TemporaryDirectory(dir=ROOT, prefix='tmp-build-') as directory:
        tmp = Path(directory)
        for source in ('toggle.c', 'toggle.S'):
            subprocess.run([str(BIN/'gcc.exe'), '-c', '-O2', '-mcmodel=small', '-ffreestanding', '-fno-stack-protector',
                '-fno-asynchronous-unwind-tables', '-fno-ident', str(ROOT/source), '-o', str(tmp/(source+'.o'))], check=True)
        for rva in (0x113c000, 0x1140000):
            script = tmp/'layout.ld'
            script.write_text(f'SECTIONS {{ .text {rva:#x} : {{ *(.text*) *(.rdata*) }} .data {rva+0x2000:#x} : {{ *(.data*) *(.bss*) }} /DISCARD/ : {{ *(.eh_frame*) *(.pdata*) *(.xdata*) }} }}')
            exe = tmp/'payload.exe'
            subprocess.run([str(BIN/'ld.exe'), '-mi386pep', '--image-base', '0', '-T', str(script),
                '--defsym', 'material_capacity=0x10d4938', '--defsym', 'material_table=0x10d4960',
                '--defsym', 'iat_module=0x7c0258', '--defsym', 'iat_proc=0x7c0260',
                '--defsym', 'iat_pid=0x7c01f8', '--defsym', 'iat_key=0x7c0000',
                '--defsym', 'return_outline=0x3ca951', '--entry', 'hook_outline', '--disable-auto-import',
                str(tmp/'toggle.c.o'), str(tmp/'toggle.S.o'), '-o', str(exe)], check=True)
            b = exe.read_bytes(); pe = struct.unpack_from('<I', b, 60)[0]
            assert struct.unpack_from('<II', b, pe+24+112+5*8) == (0, 0)
            table = pe+24+struct.unpack_from('<H', b, pe+20)[0]
            sections = []
            for i in range(struct.unpack_from('<H', b, pe+6)[0]):
                off = table+i*40
                name, size, address, rawsize, raw = struct.unpack_from('<8sIIII', b, off)
                name = name.rstrip(b'\0').decode()
                if name == '.idata':
                    assert not any(b[raw:raw+size]); continue
                assert name in ('.text', '.data')
                sections.append(dict(name={'.text':'.chcode','.data':'.chdata'}[name], rva=address,
                    size=size, flags=struct.unpack_from('<I', b, off+36)[0], data=base64.b64encode(b[raw:raw+size]).decode()))
            symbols = {}
            for line in subprocess.check_output([str(BIN/'nm.exe'), str(exe)], text=True).splitlines():
                fields = line.split()
                if len(fields)==3 and fields[2] in ('hook_outline','select_outline','settings'):
                    symbols[fields[2]] = int(fields[0],16)
            assert len(symbols)==3 and len(sections)==2 and sections[0]['size']<0x2000
            variants[str(rva)] = dict(sections=sections, symbols=symbols)
    path = ROOT/'toggle_payload.json'
    path.write_text(json.dumps(variants,indent=2)+'\n', encoding='utf8')
    print('载荷 SHA-256：',hashlib.sha256(path.read_bytes()).hexdigest())


if __name__ == '__main__':
    build()
