"""网格实时开关的 PE 叠加层；在描边开关外层安装并可独立撤销。"""
import base64
import hashlib
import json
from pathlib import Path
import struct
import highlight_native

class StaticKey(int):
    """让兼容安装器在重建外层时保留静态网格载荷版本。"""


ROOT = Path(__file__).resolve().parent
MARKER = b'GRIDSTATIC_V3\0'
HOOKS = {0xd38d7: bytes.fromhex('0f28b424b0100000')}
PAYLOAD_SHA = '636349361f05abafa71ffba70bec1fd869711a348f7d7f87aed41a2374ac8382'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def config():
    value = json.loads((ROOT/'toggle_config.json').read_text(encoding='utf8'))['key']
    if not isinstance(value, str):
        raise ValueError('key 必须是按键名称字符串')
    value = value.upper()
    if len(value) == 1 and ('A' <= value <= 'Z' or '0' <= value <= '9'):
        return ord(value)
    if value.startswith('F') and value[1:].isdigit() and 1 <= int(value[1:]) <= 12:
        return 111+int(value[1:])
    raise ValueError('网格开关键仅支持 A-Z、0-9 或 F1-F12，例如 O、F9')


def payload(rva):
    raw = (ROOT/'static_grid_payload.json').read_bytes()
    if sha(raw) != PAYLOAD_SHA:
        raise ValueError('网格开关载荷校验失败')
    return json.loads(raw)[str(rva)]


def apply(base, key):
    highlight_native.split(base)  # 完整校验原版、奔跑、俯视及新版描边的任意改键状态。
    if not isinstance(key, int) or not (48 <= key <= 57 or 65 <= key <= 90 or 112 <= key <= 123):
        raise ValueError('网格虚拟键码无效')
    result = bytearray(base)
    pe = struct.unpack_from('<I', base, 60)[0]
    count = struct.unpack_from('<H', base, pe+6)[0]
    table = pe+24+struct.unpack_from('<H', base, pe+20)[0]
    image_end = struct.unpack_from('<I', base, pe+24+56)[0]
    entries = payload(image_end)
    if table+(count+2)*40 > 0x400 or any(base[table+count*40:table+(count+2)*40]):
        raise ValueError('主程序没有可用的节表空间')
    for rva, before in HOOKS.items():
        if base[rva-0xc00:rva-0xc00+len(before)] != before:
            raise ValueError(f'网格钩子原字节不匹配：{rva:#x}')
        symbol = 'grid_copy_hook' if rva == 0xd38d7 else 'grid_water_hook'
        op = b'\xe9' if symbol == 'grid_copy_hook' else b'\xe8'
        result[rva-0xc00:rva-0xc00+len(before)] = (op+struct.pack('<i', entries['symbols'][symbol]-rva-5)).ljust(len(before), b'\x90')
    for i, section in enumerate(entries['sections']):
        raw = bytearray(base64.b64decode(section['data']))
        if section['name'] == '.grdata':
            struct.pack_into('<I', raw, entries['symbols']['grid_settings']-section['rva'], key)
        offset = len(result)
        # 描边使用尾部元数据，追加新 PE 节时先对齐文件偏移。
        aligned = (offset+511) & ~511
        result.extend(b'\0'*(aligned-offset))
        offset = aligned
        size = (len(raw)+511) & ~511
        result.extend(raw.ljust(size, b'\0'))
        struct.pack_into('<8sIIIIIIHHI', result, table+(count+i)*40,
                         section['name'].encode(), 0x2000 if i == 0 else 0x1000,
                         section['rva'], size, offset, 0, 0, 0, 0, section['flags'])
    struct.pack_into('<H', result, pe+6, count+2)
    struct.pack_into('<I', result, pe+24+56, image_end+0x3000)
    meta = json.dumps(dict(length=len(base), header=base[:0x400].hex(), key=key), separators=(',', ':')).encode()
    result.extend(meta+struct.pack('<I', len(meta))+MARKER)
    return bytes(result)


def split(data):
    if not data.endswith(MARKER):
        highlight_native.split(data)
        return data, None
    try:
        size = struct.unpack_from('<I', data, len(data)-len(MARKER)-4)[0]
        if size > 10000:
            raise ValueError('网格元数据长度异常')
        meta = json.loads(data[-len(MARKER)-4-size:-len(MARKER)-4])
        base = bytearray(data[:meta['length']])
        base[:0x400] = bytes.fromhex(meta['header'])
        for rva, original in HOOKS.items():
            base[rva-0xc00:rva-0xc00+len(original)] = original
        base = bytes(base)
        if apply(base, meta['key']) != data:
            raise ValueError('网格补丁含有未知修改，拒绝覆盖')
        return base, StaticKey(meta['key'])
    except (KeyError, IndexError, struct.error, UnicodeDecodeError) as error:
        raise ValueError('网格补丁元数据无效') from error
