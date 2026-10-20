"""从本地程序类型描述重建粒子字段编号，排除联合体别名及非序列化字段。"""
import re
import struct
from research import GAME


def schema():
    data = (GAME/'sinking_star.exe').read_bytes()
    pe = struct.unpack_from('<I', data, 60)[0]
    opt = pe+24
    base = struct.unpack_from('<Q', data, opt+24)[0]
    section = opt+struct.unpack_from('<H', data, pe+20)[0]
    sections = [struct.unpack_from('<8sIIII', data, section+40*i)
                for i in range(struct.unpack_from('<H', data, pe+6)[0])]

    def raw(address):
        rva = address-base
        return next(offset+rva-va for _, _, va, size, offset in sections
                    if va <= rva < va+size)

    def string(n, ptr):
        return data[raw(ptr):raw(ptr)+n].decode('utf8')

    def members(address):
        count, ptr = struct.unpack_from('<QQ', data, raw(address)+64)
        assert count < 1000
        result = []
        for i in range(count):
            n, s, tp, off, flags, c, attrs, _ = struct.unpack_from('<8Q', data, raw(ptr)+64*i)
            if off == 2**64-1 or flags & 0x20:
                continue
            attributes = [string(*struct.unpack_from('<QQ', data, raw(attrs)+16*j))
                          for j in range(c)]
            if 'NoSerialize' in attributes:
                continue
            version = next((int(a[1:]) for a in attributes if re.fullmatch(r'v\d+', a)), 0)
            result.append((string(n, s), tp, off, version))
        return result

    fields = []

    def walk(name, tp, offset, version):
        kind = struct.unpack_from('<I', data, raw(tp))[0]
        if kind == 7:
            for child, subtype, off, stamp in members(tp):
                walk(name+'.'+child, subtype, offset+off, max(version, stamp))
        else:
            fields.append((version, name, offset, kind))

    for name, tp, offset, version in members(base+0x6838c8):
        if name != 'entity':
            walk(name, tp, offset, version)
    return fields


if __name__ == '__main__':
    for i, (version, name, offset, kind) in enumerate(schema()):
        if any(s in name for s in ['particles_per_second', 'burst', 'render_texture', 'producing', 'particle_emissive']):
            print(hex(0x1000+i), version, name, hex(offset), kind)
