"""按字节叠加/撤销实时开关，保留已安装的奔跑和镜头补丁。"""
import base64
import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HOOK = 0x3ca94c
BEFORE = bytes.fromhex('ba0d000000')
MARKER = b'CHTOGGLE_V1\0'
# 完整基础 exe 校验：原版、奔跑版、俯视 v0.1.5 单独版和合并版。
BASE_HASHES = {
    # 俯视 v0.1.9：拉远17%，画面向下偏移6%。
    'd52ed111a966c78b106ee85825eb8a94cdbcd158c5cde2387bc27ce03d9c8697',
    '49840668932e74f8549cd47fa0d70bbed2cb61e4cf03ff86aeca4926d104503f',

    # 俯视 v0.1.8：保持15%拉远，并使画面向下偏移5%。
    '10b562b86e75b2e74c25193ca518830f1daaa489bb6570967430d9993598a519',
    '66aec030ac3ae923a2000605985c6d8c53f845d2e90d620b420ce446048c826e',

    # 俯视 v0.1.7：固定增加15%距离。
    '891db690b6f2daff7e9f7e4a10eaaf8121c3a77b9e0a5e9a6290c51ad3f558dc',
    '851f8b4d13b56b6fb514b152cbbb896e0245b4169ea6d573ce013a04eb1564df',

    # 俯视 v0.1.6：保持原高亮载荷不变，仅增加已验证基础版本。
    'a426f1c1071761379e4a2c8cc5e0c35bb7020436bf5ed84aba1c1672c4b3d493',
    'bbd4d42d0b94d6481afd953e5240bdc69e85968e152d1cab78398ed410b8f8e4',

    '0ae10a513dae25286fe93d0db4fa8a2df9a473bc07e1734e12bc1ad30166db1c',
    'bda4419d1f7e7a79f9aaa3e069ae32fe3e19a827afd8bfb3e21cbab534c60505',
    '977b15d562b797c7134f69779b608d9563a4a81aa5b087539b214f9d234981f0',
    'f25d733340cf9079303d8c3128718f5c85f3d6475173a65ca2b80a7b55a02f76',
}


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
    raw = (ROOT/'highlight_payload.json').read_bytes()
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


PAYLOAD_SHA = '8c0ff416704cac90b055a26a83d506370a3d3a8c6548265ed0fa37fc95833a3e'
