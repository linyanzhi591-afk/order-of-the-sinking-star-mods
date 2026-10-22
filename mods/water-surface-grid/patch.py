"""复用已验证的水面纯变换；不读取实际游戏或旧网格项目。"""
import base64
import hashlib
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parent
WORLD_SHA = '690b758050beed3adf63d364c1dd5cda5e6e7938fe2ec02eaee373c670b0c3bd'
SHADER_BASE_SHA = '9c5ce57d8d9e40f352690fe971ff1e8f313614495ddc29f9598f1a9a9497284c'
WATER_EXE_SHA = '5d537ef6726847d39df9e786e9e087b3135c0ca18ab9f60690ec5ee567216c29'
WATER_SHADER_SHA = '641edb243e436548dee1072ac6a0de1556774d4a26af5c2521ee4b579161e820'
HOOK = 0x1fc2f2
BEFORE = bytes.fromhex('488b4e08488b8190020000')
MARKER = b'WATER_ONLY_V1\0'

def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def pe_info(data):
    require(data[:2] == b'MZ', '不是 PE 文件')
    pe = struct.unpack_from('<I', data, 60)[0]
    require(data[pe:pe+4] == b'PE\0\0', 'PE 标识错误')
    count = struct.unpack_from('<H', data, pe+6)[0]
    table = pe+24+struct.unpack_from('<H', data, pe+20)[0]
    end = struct.unpack_from('<I', data, pe+24+56)[0]
    return pe, count, table, end


def raw_offset(data, rva):
    _, count, table, _ = pe_info(data)
    for i in range(count):
        vsize, start, size, offset = struct.unpack_from('<4I', data, table+i*40+8)
        if start <= rva < start+size:
            return offset+rva-start
    raise ValueError(f'RVA 无对应文件字节：{rva:#x}')


def metadata(data, marker):
    require(data.endswith(marker), '补丁尾标识不匹配')
    end = len(data)-len(marker)-4
    size = struct.unpack_from('<I', data, end)[0]
    require(0 < size < 10000 and size < end, '补丁元数据长度异常')
    return json.loads(data[end-size:end])


def unpack(data):
    require(data[:8] == b'simp\x01\0\0\0', '着色器包格式异常')
    toc = struct.unpack_from('<Q', data, 16)[0]
    require(data[toc:toc+4] == b'toc!', '包目录异常')
    count = struct.unpack_from('<Q', data, toc+8)[0]
    require(count <= 100000, '目录条目数量异常')
    pos, entries = toc+64, []
    for _ in range(count):
        n = struct.unpack_from('<I', data, pos)[0]
        pos += 4
        require(n <= 4096 and pos+n+17 <= len(data), '目录条目越界')
        name = data[pos:pos+n].decode('utf8')
        require(data[pos+n] == 0, '名称终止符异常')
        pos += n+1
        size, offset = struct.unpack_from('<QQ', data, pos)
        pos += 16
        require(64 <= offset <= offset+size <= toc, '着色器数据越界')
        entries.append((name, size, offset))
    require(pos == len(data) and len(set(e[0] for e in entries)) == count, '目录长度或名称重复')
    return toc, entries


def apply_native(base, entry):
    require(sha(base) == WORLD_SHA, '独立载荷仅支持本次已核验的其他 mod 组合')
    pe, count, table, end = pe_info(base)
    require(table+(count+2)*40 <= 0x400 and not any(base[table+count*40:table+(count+2)*40]), '节表无空间')
    at = raw_offset(base, HOOK)
    require(base[at:at+len(BEFORE)] == BEFORE, '常量完成钩子原字节不符')
    result = bytearray(base)
    jump = b'\xe9'+struct.pack('<i', entry['symbols']['water_constants_hook']-HOOK-5)
    result[at:at+len(BEFORE)] = jump.ljust(len(BEFORE), b'\x90')
    for i, section in enumerate(entry['sections']):
        raw = base64.b64decode(section['data'])
        capacity = 0x2000 if i == 0 else 0x1000
        require(section['rva'] == end+(0 if i == 0 else 0x2000) and len(raw) <= capacity, '载荷地址或容量异常')
        offset = (len(result)+511)&~511
        result.extend(b'\0'*(offset-len(result)))
        size = (len(raw)+511)&~511
        result.extend(raw.ljust(size, b'\0'))
        struct.pack_into('<8sIIIIIIHHI', result, table+(count+i)*40,
                         section['name'].encode(), capacity, section['rva'], size, offset, 0, 0, 0, 0, section['flags'])
    struct.pack_into('<H', result, pe+6, count+2)
    struct.pack_into('<I', result, pe+24+56, end+0x3000)
    meta = json.dumps({'length': len(base), 'header': base[:0x400].hex(), 'base_sha256': sha(base)}, separators=(',', ':')).encode()
    result.extend(meta+struct.pack('<I', len(meta))+MARKER)
    return bytes(result)


def split_native(data, entry):
    meta = metadata(data, MARKER)
    base = bytearray(data[:meta['length']])
    base[:0x400] = bytes.fromhex(meta['header'])
    at = raw_offset(base, HOOK)
    base[at:at+len(BEFORE)] = BEFORE
    base = bytes(base)
    require(sha(base) == meta['base_sha256'] == WORLD_SHA and apply_native(base, entry) == data, '水面层恢复或重建失败')
    return base


def apply_shaders(base, replacements):
    require(sha(base) == SHADER_BASE_SHA, '着色器基础不匹配')
    toc, entries = unpack(base)
    result, updated = bytearray(base), []
    require(set(replacements) <= {e[0] for e in entries}, '缺少着色器条目')
    for name, size, offset in entries:
        if name in replacements:
            offset, size = len(result), len(replacements[name])
            result.extend(replacements[name])
        updated.append((name, size, offset))
    new_toc = len(result)
    result.extend(base[toc:toc+64])
    for name, size, offset in updated:
        encoded = name.encode('utf8')
        result.extend(struct.pack('<I', len(encoded))+encoded+b'\0'+struct.pack('<QQ', size, offset))
    struct.pack_into('<Q', result, 16, new_toc)
    unpack(result)
    return bytes(result)

def decode(src):
    """解码资源使用的原始 LZ4 块，不依赖第三方模块。"""
    result, pos = bytearray(), 0
    while pos < len(src):
        token = src[pos]
        pos += 1
        length = token >> 4
        if length == 15:
            while True:
                value = src[pos]
                pos += 1
                length += value
                if value != 255:
                    break
        result.extend(src[pos:pos+length])
        pos += length
        if pos == len(src):
            break
        offset = int.from_bytes(src[pos:pos+2], 'little')
        pos += 2
        if not 0 < offset <= len(result):
            raise ValueError('LZ4 回引越界')
        length = (token & 15)+4
        if (token & 15) == 15:
            while True:
                value = src[pos]
                pos += 1
                length += value
                if value != 255:
                    break
        for _ in range(length):
            result.append(result[-offset])
    return bytes(result)


def native_payload():
    raw = (ROOT/'native_payload.json').read_bytes()
    require(sha(raw) == 'fa284eb615895523fcaf0c336d87b8277fdf197febc1f662e8ba12fa5e0457dd', '水面原生载荷校验失败')
    return json.loads(raw)


def shader_base(data):
    if sha(data) == SHADER_BASE_SHA:
        return data, False
    require(sha(data) == WATER_SHADER_SHA, '着色器包含未知修改或未完成网格，拒绝覆盖')
    base = bytearray(data[:75155416])
    struct.pack_into('<Q', base, 16, 74981376)
    base = bytes(base)
    require(sha(base) == SHADER_BASE_SHA, '水面着色器基础恢复失败')
    return base, True


def shader_output(base):
    require(sha(base) == SHADER_BASE_SHA, '着色器基础版本不符')
    recipe = json.loads((ROOT/'shader_patch.json').read_text(encoding='utf8'))
    require(recipe['schema'] == 1 and len(recipe['entries']) == 32, '水面差量清单异常')
    originals = {name:base[offset:offset+size] for name,size,offset in unpack(base)[1]}
    replacements = {}
    for name, item in recipe['entries'].items():
        source = originals[name]
        require(sha(source) == item['source_sha256'], '原始水面条目校验失败')
        decoded = decode(source[24:])
        require(sha(decoded) == item['decoded_sha256'] and 0 < item['decoded_size'] < 16*1024*1024, '水面解压输入或长度异常')
        result = bytearray()
        for op in item['ops']:
            if isinstance(op,list):
                require(len(op) == 2 and all(type(n) is int for n in op) and 0 <= op[0] < op[0]+op[1] <= len(decoded), '差量复制区间越界')
                result.extend(decoded[op[0]:op[0]+op[1]])
            else:
                require(isinstance(op,str), '差量新增数据类型异常')
                result.extend(base64.b64decode(op,validate=True))
            require(len(result) <= item['decoded_size'], '差量输出越界')
        require(len(result) == item['decoded_size'], '差量输出长度不符')
        literal = bytearray([min(len(result),15) << 4])
        if len(result) >= 15:
            remaining = len(result)-15
            while remaining >= 255:
                literal.append(255); remaining -= 255
            literal.append(remaining)
        literal.extend(result)
        header = bytearray(source[:24])
        struct.pack_into('<I',header,8,len(result)+24)
        replacements[name] = bytes(header+literal)
        require(sha(replacements[name]) == item['result_sha256'], '签名水面着色器重建哈希不符')
    output = apply_shaders(base,replacements)
    require(sha(output) == WATER_SHADER_SHA, '水面着色器最终哈希不符')
    return output


def plan(exe, shaders):
    entry = native_payload()
    enabled = exe.endswith(MARKER)
    if enabled:
        require(sha(exe) == WATER_EXE_SHA, '水面主程序含未知修改')
        base_exe = split_native(exe,entry)
    else:
        require(sha(exe) == WORLD_SHA, '此水面版本只支持已验证的奔跑＋俯视0.1.9＋描边P＋世界单步N/M组合；请使用六mod合集补齐')
        base_exe = exe
    base_shaders, shaders_enabled = shader_base(shaders)
    require(enabled == shaders_enabled, '水面程序和着色器安装状态不一致，拒绝覆盖')
    result_exe = exe if enabled else apply_native(base_exe,entry)
    result_shaders = shaders if enabled else shader_output(base_shaders)
    require(sha(result_exe) == WATER_EXE_SHA and sha(result_shaders) == WATER_SHADER_SHA, '水面产物与已验证候选不一致')
    return {'exe':result_exe,'shaders':result_shaders}, enabled
