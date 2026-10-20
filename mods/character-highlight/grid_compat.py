"""网格与描边的资源兼容层；两个发行包各自携带同一份文件。"""
import hashlib
import re
import struct

BASE_SHA = 'dffd12a4f1002dc2f309d5b85205b432c1d7213764c798ccb693cd0ef5f1afc6'
KNOWN_SHA = {
    '6ec74fbc74051ee4a4b241a2edba79322398102959ad63493d00fef1c34fa54b',
    BASE_SHA,
    '42cc6b62b3c672c08b37fd8abb060edf372e443121f9b691250185110113fc67',
    '1b4a5c07da672c756cf5d84507771a29a22e01e5380aa14656407e813b894e95',
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def spans(base):
    if digest(base) != BASE_SHA:
        raise ValueError('网格原始材质备份校验失败')
    toc = struct.unpack_from('<Q', base, 16)[0]
    count = struct.unpack_from('<Q', base, toc+8)[0]
    pos = toc+64
    result = []
    for _ in range(count):
        length = struct.unpack_from('<I', base, pos)[0]
        pos += 4+length+1
        size, offset = struct.unpack_from('<QQ', base, pos)
        pos += 16
        content = base[offset:offset+size]
        for match in re.finditer(rb'(?m)^(?:# )?grid_opac ([0-9.]+)(?=\r?$)', content):
            # 使用空格填充原行，避免移动任何材质或目录偏移。
            old = match[0]
            new = b'grid_opac 1'.ljust(len(old), b' ')
            if len(new) != len(old):
                raise ValueError('网格参数空间不足')
            result.append((offset+match.start(), old, new))
    if len(result) != 3590:
        raise ValueError('网格参数数量不匹配')
    return result


def enable(data, base):
    if digest(data) not in KNOWN_SHA:
        raise ValueError('检测到未知材质修改，拒绝启用网格')
    result = bytearray(data)
    for offset, old, new in spans(base):
        if result[offset:offset+len(old)] != old:
            raise ValueError('网格参数位置不匹配')
        result[offset:offset+len(old)] = new
    return bytes(result)


def split(data, base):
    """返回移除网格后的已知材质和网格安装标记；拒绝部分修改。"""
    if digest(data) in KNOWN_SHA:
        return data, False
    result = bytearray(data)
    for offset, old, new in spans(base):
        if result[offset:offset+len(new)] != new:
            raise ValueError('检测到未知或不完整的材质修改，拒绝覆盖')
        result[offset:offset+len(old)] = old
    clean = bytes(result)
    if digest(clean) not in KNOWN_SHA:
        raise ValueError('检测到网格范围以外的未知材质修改，拒绝覆盖')
    return clean, True
