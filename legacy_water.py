"""仅用于识别并移除 v1.1.1-test 的旧水面层；不能生成或安装水面网格。"""
import hashlib
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parent
WORLD_SHA = '31b5d25848666ea275d6d04d3d5ca7c676e0822a88360e630ebd6f092c000e9f'
SHADER_BASE_SHA = '405510e3856cd1988fe15b53bceb1fadd3be69830f67d6faea0f6b1678627104'
WATER_EXE_SHA = 'a2433c02df3d6de2de4d3c152aa3328e778291bb7a2eea2464b7cba3b6884b5e'
WATER_SHADER_SHA = '1b6809717a8c1dd401a7d5cb8bb90b1e1e18bb586da9ca914d1076f4b23b8f16'
HOOK = 0x1ff7c2
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
    require(data[pe:pe + 4] == b'PE\0\0', 'PE 标识错误')
    count = struct.unpack_from('<H', data, pe + 6)[0]
    table = pe + 24 + struct.unpack_from('<H', data, pe + 20)[0]
    return count, table


def raw_offset(data, rva):
    count, table = pe_info(data)
    for index in range(count):
        _, start, size, offset = struct.unpack_from('<4I', data, table + index * 40 + 8)
        if start <= rva < start + size:
            return offset + rva - start
    raise ValueError(f'RVA 无对应文件字节：{rva:#x}')


def metadata(data):
    require(data.endswith(MARKER), '旧水面层尾标识不匹配')
    end = len(data) - len(MARKER) - 4
    size = struct.unpack_from('<I', data, end)[0]
    require(0 < size < 10000 and size < end, '旧水面层元数据长度异常')
    return json.loads(data[end - size:end])


def split_native(data):
    require(sha(data) == WATER_EXE_SHA, '旧水面主程序含未知修改')
    info = metadata(data)
    base = bytearray(data[:info['length']])
    header = bytes.fromhex(info['header'])
    require(len(header) == 0x400, '旧水面层 PE 头备份异常')
    base[:0x400] = header
    at = raw_offset(base, HOOK)
    base[at:at + len(BEFORE)] = BEFORE
    base = bytes(base)
    require(sha(base) == info['base_sha256'] == WORLD_SHA, '旧水面主程序恢复校验失败')
    return base


def shader_base(data):
    digest = sha(data)
    if digest == SHADER_BASE_SHA:
        return data, False
    require(digest == WATER_SHADER_SHA,
            '着色器版本不匹配：仅支持 Steam Build 26249670 原版或 v1.1.1-test 水面层')
    base = bytearray(data[:74952414])
    struct.pack_into('<Q', base, 16, 74777830)
    base = bytes(base)
    require(sha(base) == SHADER_BASE_SHA, '旧水面着色器恢复失败')
    return base, True
