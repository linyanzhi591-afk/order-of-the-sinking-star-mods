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
MARKER = b'GRIDCONST_V4\0'
HOOKS = {0x1fc2f2: bytes.fromhex('488b4e08488b8190020000')}
PAYLOAD_SHA = 'f1f11455021c3db9721a279b72713f794838e076e68c27325a389273cacfd749'
# 仅接受已逐字节验证的当前世界单步组合，禁止放宽未知程序校验。
WORLD_MARKER = b'WORLDSTEP_V3\0'
WORLD_SHA = '690b758050beed3adf63d364c1dd5cda5e6e7938fe2ec02eaee373c670b0c3bd'


def underlying_highlight(data):
    """验证底层组合并取得高亮层；世界单步的完整原字节仍作为网格底层保留。"""
    if not data.endswith(WORLD_MARKER):
        highlight_native.split(data)
        return data, ()
    if sha(data) != WORLD_SHA:
        raise ValueError('世界单步组合尚未验证，拒绝覆盖')
    size = struct.unpack_from('<I', data, len(data)-len(WORLD_MARKER)-4)[0]
    meta = json.loads(data[-len(WORLD_MARKER)-4-size:-len(WORLD_MARKER)-4])
    base = bytearray(data[:meta['length']])
    base[:0x400] = bytes.fromhex(meta['header'])
    for rva, original in ((0x262462, 'f30f1105ae1b5a00'), (0x263ffc, '0f837b020000')):
        raw = bytes.fromhex(original)
        base[rva-0xc00:rva-0xc00+len(raw)] = raw
    base = bytes(base)
    if sha(base) != meta['base_sha']:
        raise ValueError('世界单步底层校验失败')
    highlight_native.split(base)
    return base, tuple(meta['keys'])


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
    raw = (ROOT/'constant_grid_payload.json').read_bytes()
    if sha(raw) != PAYLOAD_SHA:
        raise ValueError('网格开关载荷校验失败')
    return json.loads(raw)[str(rva)]


def apply(base, key):
    _, world_keys = underlying_highlight(base)
    if not isinstance(key, int) or not (48 <= key <= 57 or 65 <= key <= 90 or 112 <= key <= 123):
        raise ValueError('网格虚拟键码无效')
    if key in world_keys:
        raise ValueError('网格按键与世界暂停／单步按键冲突')
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
        symbol = 'grid_constants_hook'
        op = b'\xe9'
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
        underlying_highlight(data)
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
