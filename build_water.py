"""从只读样本重建新版水面载荷、32 个已签名着色器及差量；不安装游戏。"""
import argparse
import base64
from collections import defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
ROOT = Path(__file__).resolve().parent/'mods/water-surface-grid'
sys.path.insert(0, str(ROOT))
from patch import require, sha, pe_info, apply_native, apply_shaders, unpack
from water_shader import inject
from dxil import decode, assemble
import dxil
BIN = Path(r'C:\Program Files (x86)\mingw64\bin')
DXC = None
FAMILIES = {'water_flow':'water_flow','water_ripple':'water_ripple','water_simple':'water_simple','ocean_D':'ocean'}
FLAGS = {'100352','104448','2048','34816','38912','6144','67584','71680'}

def run(command):
    return subprocess.check_output([str(x) for x in command], stderr=subprocess.STDOUT)


def build_native(base, temp):
    rva = pe_info(base)[3]
    for source in ('water_grid.c', 'water_hook.S'):
        run([BIN/'gcc.exe', '-c', '-O2', '-mcmodel=small', '-ffreestanding',
             '-fno-stack-protector', '-fno-asynchronous-unwind-tables', '-fno-ident',
             ROOT/source, '-o', temp/(source+'.o')])
    layout = temp/'layout.ld'
    layout.write_text(f'SECTIONS {{ .text {rva:#x} : {{ *(.text*) *(.rdata*) }} '
                      f'.data {rva+0x2000:#x} : {{ *(.data*) *(.bss*) }} '
                      '/DISCARD/ : { *(.eh_frame*) *(.pdata*) *(.xdata*) } }')
    definitions = {'material_capacity': 0x10d3958, 'material_table': 0x10d3960,
                   'render_context': 0x8042a0, 'upload_buffer_view': 0xc8b70,
                   'iat_module': 0x7bf1f8, 'iat_proc': 0x7bf200,
                   'iat_pid': 0x7bf190, 'iat_key': 0x7bef90, 'water_constants_return': 0x1ff7cd}
    exe = temp/'payload.exe'
    command = [BIN/'ld.exe', '-mi386pep', '--image-base', '0', '-T', layout]
    for name, address in definitions.items():
        command.extend(['--defsym', f'{name}={address:#x}'])
    command.extend(['--entry', 'water_constants_hook', '--disable-auto-import',
                    temp/'water_grid.c.o', temp/'water_hook.S.o', '-o', exe])
    run(command)
    raw = exe.read_bytes()
    pe, count, table, _ = pe_info(raw)
    require(struct.unpack_from('<II', raw, pe+24+112+5*8) == (0, 0), '不允许运行时重定位')
    sections = []
    for i in range(count):
        at = table+i*40
        name, size, address, rawsize, offset = struct.unpack_from('<8sIIII', raw, at)
        name = name.rstrip(b'\0').decode()
        if name == '.idata':
            require(not any(raw[offset:offset+size]), '不允许新增导入')
            continue
        require(name in ('.text', '.data'), '未知载荷节')
        # 全零状态由链接器放入 BSS，其文件偏移为零；必须显式补零，不能读取 PE 头。
        content = raw[offset:offset+min(size, rawsize)] if rawsize and offset else b''
        content = content.ljust(size, b'\0')
        flags = 0x60000020 if name == '.text' else 0xc0000040
        sections.append({'name': {'.text': '.waterc', '.data': '.waterd'}[name],
                         'rva': address, 'size': size, 'flags': flags,
                         'data': base64.b64encode(content).decode()})
    symbols = {}
    for line in run([BIN/'nm.exe', exe]).decode().splitlines():
        fields = line.split()
        if len(fields) == 3 and fields[2] in ('water_constants_hook', 'water_after_constants', 'water_state'):
            symbols[fields[2]] = int(fields[0], 16)
    require(len(symbols) == 3 and len(sections) == 2, '载荷节或符号缺失')
    return {'sections': sections, 'symbols': symbols}


def literal(data):
    output = bytearray([min(len(data), 15) << 4])
    if len(data) >= 15:
        remaining = len(data)-15
        while remaining >= 255:
            output.append(255)
            remaining -= 255
        output.append(remaining)
    output.extend(data)
    require(decode(output) == data, 'LZ4 编码回读失败')
    return bytes(output)


def stages(source):
    data = decode(source[24:])
    require(struct.unpack_from('<I', source, 8)[0] == len(data)+24, '解压尺寸错误')
    first = data.index(b'DXBC')
    sizes = struct.unpack_from('<4Q', data, first-32)
    vsize, psize = sizes[:2]
    start = first+vsize
    require(data[start:start+4] == b'DXBC' and struct.unpack_from('<I', data, start+24)[0] == psize, '像素容器尺寸异常')
    return data, first, start, psize


def replace_pixel(source, family, temp):
    data, first, start, size = stages(source)
    path = temp/'pixel.dxil'
    path.write_bytes(data[start:start+size])
    text = run([DXC/'dxc.exe', '-dumpbin', path]).decode('utf8').replace('\r\n', '\n').replace('\r', '')
    pixel = assemble(inject(text, family))
    path.write_bytes(pixel)
    run([DXC/'dxv.exe', path])
    require(any(pixel[4:20]), 'DXIL 无有效签名')
    output = bytearray(data[:start]+pixel+data[start+size:])
    struct.pack_into('<Q', output, first-24, len(pixel))
    header = bytearray(source[:24])
    struct.pack_into('<I', header, 8, len(output)+24)
    return bytes(header)+literal(output)

def delta(source, target):
    """只携带新增字节，其余通过原版解压资源内的复制区间重建。"""
    index = defaultdict(list)
    for pos in range(0,len(source)-31,8):
        block = source[pos:pos+32]
        if len(index[block]) < 8:
            index[block].append(pos)
    result, added, at = [], bytearray(), 0
    while at < len(target):
        best_size, best_pos = 0, 0
        for offset in index.get(target[at:at+32],()):
            size = 32
            while at+size < len(target) and offset+size < len(source) and target[at+size] == source[offset+size]:
                size += 1
            if size > best_size:
                best_size,best_pos = size,offset
        if best_size:
            if added:
                result.append(base64.b64encode(added).decode())
                added.clear()
            result.append([best_pos,best_size])
            at += best_size
        else:
            added.append(target[at]); at += 1
    if added:
        result.append(base64.b64encode(added).decode())
    rebuilt = b''.join(source[x[0]:x[0]+x[1]] if isinstance(x,list) else base64.b64decode(x) for x in result)
    assert rebuilt == target
    return result


def main():
    global DXC
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe',type=Path,required=True)
    parser.add_argument('--shaders',type=Path,required=True)
    parser.add_argument('--dxc',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    DXC=args.dxc.resolve();dxil.DXC=DXC
    base=args.exe.read_bytes();shaders=args.shaders.read_bytes()
    args.output.mkdir(parents=True,exist_ok=False)
    with tempfile.TemporaryDirectory(dir=args.output) as directory:
        temp=Path(directory)
        native=build_native(base,temp)
        replacements={};patches={}
        for name,size,offset in unpack(shaders)[1]:
            stem=Path(name).stem
            if '--' not in stem: continue
            family,flag=stem.split('--',1)
            if family not in FAMILIES or flag not in FLAGS: continue
            before=shaders[offset:offset+size]
            after=replace_pixel(before,FAMILIES[family],temp)
            replacements[name]=after
            old,new=decode(before[24:]),decode(after[24:])
            patches[name]=dict(source_sha256=sha(before),decoded_sha256=sha(old),
                               result_sha256=sha(after),decoded_size=len(new),ops=delta(old,new))
            print('已签名并通过 dxv：'+name,flush=True)
        require(len(replacements)==32,'必须恰好修改 32 个水面变体')
    exe=apply_native(base,native);output=apply_shaders(shaders,replacements)
    (args.output/'native_payload.json').write_text(json.dumps(native,indent=2)+'\n',encoding='utf8')
    (args.output/'shader_patch.json').write_text(json.dumps(dict(schema=1,entries=patches),separators=(',',':'))+'\n',encoding='utf8')
    (args.output/'water.exe').write_bytes(exe)
    (args.output/'water.package').write_bytes(output)
    report=dict(steam_build=26249670,base_exe_sha256=sha(base),base_shaders_sha256=sha(shaders),
                output_exe_sha256=sha(exe),output_shaders_sha256=sha(output),
                native_payload_sha256=sha((args.output/'native_payload.json').read_bytes()),
                changed_entries=sorted(replacements),signed_dxv_passed=32,gameplay_validation=False)
    (args.output/'build_manifest.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':
    main()
