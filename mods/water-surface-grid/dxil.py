"""本项目使用的 LZ4 解码和微软 DXIL 组装、签名工具。"""
import ctypes as C
import os
from pathlib import Path
import struct
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parent
DXC = Path(os.environ['TEMP']) / 'sinking-star-grid-dxc/bin/x64'


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


def method(obj, index, restype, *types):
    vtable = C.cast(obj, C.POINTER(C.POINTER(C.c_void_p))).contents
    return C.WINFUNCTYPE(restype, C.c_void_p, *types)(vtable[index])


def check(hr):
    if hr < 0:
        raise RuntimeError(f'DXC HRESULT={hr & 0xffffffff:#x}')


def blob_data(blob):
    ptr = method(blob, 3, C.c_void_p)(blob)
    size = method(blob, 4, C.c_size_t)(blob)
    return C.string_at(ptr, size)


def assemble(source):
    """通过官方 IDxcAssembler 组装 LLVM 文本；不关闭验证。"""
    dll = C.WinDLL(str(DXC/'dxcompiler.dll'))
    create = dll.DxcCreateInstance
    create.argtypes = [C.c_void_p, C.c_void_p, C.POINTER(C.c_void_p)]
    create.restype = C.c_long

    def instance(clsid, iid):
        result = C.c_void_p()
        check(create(uuid.UUID(clsid).bytes_le, uuid.UUID(iid).bytes_le, C.byref(result)))
        return result

    library = instance('6245d6af-66e0-48fd-80b4-4d271796748c',
                       'e5204dc7-d18c-4c3c-bdfb-851673980fe7')
    assembler = instance('d728db68-f903-4f80-94cd-dccf76ec7151',
                         '091f7a26-1c1f-4948-904b-e6e3a8a771d5')
    source_blob, operation, result_blob, errors = (C.c_void_p() for _ in range(4))
    objects = [library, assembler, source_blob, operation, result_blob, errors]
    try:
        raw = source.encode('utf8')
        check(method(library, 7, C.c_long, C.c_void_p, C.c_uint, C.c_uint,
                     C.POINTER(C.c_void_p))(library, raw, len(raw), 65001, C.byref(source_blob)))
        check(method(assembler, 3, C.c_long, C.c_void_p, C.POINTER(C.c_void_p))(
            assembler, source_blob, C.byref(operation)))
        status = C.c_long()
        check(method(operation, 3, C.c_long, C.POINTER(C.c_long))(operation, C.byref(status)))
        if status.value < 0:
            check(method(operation, 5, C.c_long, C.POINTER(C.c_void_p))(
                operation, C.byref(errors)))
            raise ValueError(blob_data(errors).decode('utf8', errors='replace'))
        check(method(operation, 4, C.c_long, C.POINTER(C.c_void_p))(
            operation, C.byref(result_blob)))
        # 组装器只创建容器；必须调用微软验证器签名，不能把零校验和交给驱动。
        validator_dll = C.WinDLL(str(DXC/'dxil.dll'))
        factory = validator_dll.DxcCreateInstance
        factory.argtypes = create.argtypes
        factory.restype = C.c_long
        validator, validated, signed = C.c_void_p(), C.c_void_p(), C.c_void_p()
        objects.extend((validator, validated, signed))
        check(factory(uuid.UUID('8ca3e215-f728-4cf3-8cdd-88af917587a1').bytes_le,
                      uuid.UUID('a6e82bd2-1fd7-4826-9811-2857e797f49a').bytes_le,
                      C.byref(validator)))
        check(method(validator, 3, C.c_long, C.c_void_p, C.c_uint,
                     C.POINTER(C.c_void_p))(validator, result_blob, 1, C.byref(validated)))
        check(method(validated, 3, C.c_long, C.POINTER(C.c_long))(validated, C.byref(status)))
        if status.value < 0:
            check(method(validated, 5, C.c_long, C.POINTER(C.c_void_p))(
                validated, C.byref(errors)))
            raise ValueError(blob_data(errors).decode('utf8', errors='replace'))
        check(method(validated, 4, C.c_long, C.POINTER(C.c_void_p))(
            validated, C.byref(signed)))
        output = blob_data(signed)
        if not any(output[4:20]):
            raise ValueError('DXIL 容器未获得验证器签名')
        return output
    finally:
        for obj in reversed(objects):
            if obj:
                method(obj, 2, C.c_ulong)(obj)
