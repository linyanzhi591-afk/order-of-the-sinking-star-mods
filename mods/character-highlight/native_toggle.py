"""按字节叠加/撤销实时开关，保留已安装的奔跑和镜头补丁。"""
import base64
import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HOOK = 0x3c96a9
BEFORE = bytes.fromhex('ba0d000000')
MARKER = b'CHTOGGLE_V1\0'
# 完整基础 exe 校验：原版、奔跑版、俯视 v0.1.5 单独版和合并版。
BASE_HASHES = {'fb4699c1753564533b86f5f5ace7ad7a22fb233d065131bb9fef483b886abecf', 'd802098b7cb85eadfc733b88d1554042fad950c572e916febea3f669a474a549', 'ca8235abc33e9f4a593ab14acd0d17842a5de8460f0d90ae25ca10b225899f9c', 'b838fda62e2bf88ff3c61c04db4540613d461554dc3ac1afd78f99e5f656e661'}



def sha(data):
    return hashlib.sha256(data).hexdigest()


def config():
    value = json.loads((ROOT/'toggle_config.json').read_text(encoding='utf8'))['key']
    if not isinstance(value,str):
        raise ValueError('key 必须是按键名称字符串')
    value = value.upper()
    if len(value)==1 and ('A'<=value<='Z' or '0'<=value<='9'):
        return ord(value)
    if value.startswith('F') and value[1:].isdigit() and 1<=int(value[1:])<=12:
        return 111+int(value[1:])
    raise ValueError('开关键仅支持 A-Z、0-9 或 F1-F12，例如 P、F8')


def payload(rva):
    raw = (ROOT/'toggle_payload.json').read_bytes()
    if sha(raw) != PAYLOAD_SHA:
        raise ValueError('描边开关载荷校验失败')
    return json.loads(raw)[str(rva)]


def apply(base, key):
    if sha(base) not in BASE_HASHES:
        raise ValueError('主程序包含未知修改或版本不匹配，拒绝覆盖')
    result = bytearray(base)
    pe = struct.unpack_from('<I',base,60)[0]
    count = struct.unpack_from('<H',base,pe+6)[0]
    table = pe+24+struct.unpack_from('<H',base,pe+20)[0]
    image_end = struct.unpack_from('<I',base,pe+24+56)[0]
    entries = payload(image_end)
    if base[HOOK-0xc00:HOOK-0xc00+5] != BEFORE or any(base[table+count*40:table+(count+2)*40]):
        raise ValueError('描边钩子或节表空间异常')
    result[HOOK-0xc00:HOOK-0xc00+5] = b'\xe9'+struct.pack('<i',entries['symbols']['hook_outline']-HOOK-5)
    for i,section in enumerate(entries['sections']):
        raw = bytearray(base64.b64decode(section['data']))
        if section['name']=='.chdata':
            struct.pack_into('<I',raw,entries['symbols']['settings']-section['rva'],key)
        offset=len(result); size=(len(raw)+511)&~511
        result.extend(raw.ljust(size,b'\0'))
        virtual_size=0x2000 if i==0 else 0x1000
        struct.pack_into('<8sIIIIIIHHI',result,table+(count+i)*40,section['name'].encode(),virtual_size,
                         section['rva'],size,offset,0,0,0,0,section['flags'])
    struct.pack_into('<H',result,pe+6,count+2)
    struct.pack_into('<I',result,pe+24+56,image_end+0x3000)
    meta=json.dumps(dict(length=len(base),header=base[:0x400].hex(),key=key),separators=(',',':')).encode()
    result.extend(meta+struct.pack('<I',len(meta))+MARKER)
    return bytes(result)


def split(data):
    if not data.endswith(MARKER):
        if sha(data) not in BASE_HASHES:
            raise ValueError('未知游戏主程序，拒绝修改')
        return data, None
    size=struct.unpack_from('<I',data,len(data)-len(MARKER)-4)[0]
    if size>10000:
        raise ValueError('描边开关元数据异常')
    meta=json.loads(data[-len(MARKER)-4-size:-len(MARKER)-4])
    base=bytearray(data[:meta['length']]);base[:0x400]=bytes.fromhex(meta['header'])
    base[HOOK-0xc00:HOOK-0xc00+5]=BEFORE
    base=bytes(base)
    if apply(base,meta['key']) != data:
        raise ValueError('开关补丁有未知修改，拒绝覆盖')
    return base,meta['key']


PAYLOAD_SHA = '86cbfd8bfc49a35064ac07c04f2013f327bbd464ba63cce1a5597b8298fe4165'
