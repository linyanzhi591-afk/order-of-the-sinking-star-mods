"""只读分析粒子资源；不会修改游戏文件或进程。"""
from collections import Counter
from pathlib import Path
import re
import struct

GAME = Path(r'D:\Program Files (x86)\Steam\steamapps\common\Order of the Sinking Star')


def package(data):
    assert data[:8] == b'simp\x01\0\0\0'
    toc = struct.unpack_from('<Q', data, 16)[0]
    assert data[toc:toc+4] == b'toc!'
    count = struct.unpack_from('<Q', data, toc+8)[0]
    pos = toc+64
    entries = []
    for _ in range(count):
        length = struct.unpack_from('<I', data, pos)[0]
        pos += 4
        name = data[pos:pos+length].decode('utf8')
        assert data[pos+length] == 0
        pos += length+1
        size, offset = struct.unpack_from('<QQ', data, pos)
        pos += 16
        assert 64 <= offset <= offset+size <= toc
        entries.append((name, size, offset))
    assert pos == len(data)
    return entries


def entities(data):
    assert data[:6] == b'enty\x07\0'
    count = struct.unpack_from('<Q', data, 14)[0]
    pos = 22
    types = []
    for _ in range(count):
        length = struct.unpack_from('<Q', data, pos)[0]
        pos += 8
        name = data[pos:pos+length].decode('ascii')
        pos += length+8
        types.append(name)
    count = struct.unpack_from('<I', data, pos)[0]
    pos += 4
    records = []
    for _ in range(count):
        eid, tid, size = struct.unpack_from('<IHI', data, pos)
        pos += 10
        assert tid < len(types) and size <= len(data)-pos
        blob = data[pos:pos+size]
        records.append(dict(id=eid, type=types[tid], offset=pos, data=blob))
        pos += size
    assert pos == len(data), (pos, len(data))
    return records


def string_field(blob, field):
    pattern = b'\xfd'+struct.pack('<H', field)+b'\0'*8
    hits = list(re.finditer(re.escape(pattern), blob))
    if not hits:
        return ''
    assert len(hits) == 1
    pos = hits[0].end()
    length = struct.unpack_from('<Q', blob, pos)[0]
    assert length < 1024
    return blob[pos+8:pos+8+length].decode('utf8')


def field_value(blob, field, default):
    pattern = b'\xfd'+struct.pack('<H', field)+default
    hits = list(re.finditer(re.escape(pattern), blob))
    assert len(hits) <= 1
    return hits[0].end() if hits else None


def describe(records):
    by_id = {r['id']: r for r in records}
    for r in records:
        r['name'] = string_field(r['data'], 11)
        p = field_value(r['data'], 12, b'\0'*4)
        r['parent'] = struct.unpack_from('<I', r['data'], p)[0] if p is not None else 0
    for r in records:
        chain = []
        parent = r['parent']
        while parent in by_id:
            assert parent not in chain
            chain.append(parent)
            parent = by_id[parent]['parent']
        r['groups'] = [by_id[i]['name'] for i in reversed(chain)]
        if r['type'] == 'Particle_Source':
            r['texture'] = string_field(r['data'], 0x109c)
            p = field_value(r['data'], 0x1002, struct.pack('<f', 150))
            r['pps'] = struct.unpack_from('<f', r['data'], p)[0] if p is not None else None
    return records


def main():
    data = (GAME/'data/levels.package').read_bytes()
    regular = []
    errors = []
    for name, size, offset in package(data):
        if not name.endswith('.entities'):
            continue
        try:
            records = describe(entities(data[offset:offset+size]))
        except (AssertionError, UnicodeError, struct.error) as error:
            errors.append((name, str(error)))
            continue
        for r in records:
            if r['type'] != 'Particle_Source':
                continue
            summary = ('/'.join(r['groups']+[r['name']]), r['texture'], r['pps'])
            if name.endswith('/ingame_particles.entities'):
                if re.search('fire|flame|beam|dragon|water_specks', summary[0], re.I):
                    print('TEMPLATE', hex(r['id']), *summary)
            else:
                regular.append((name, r, summary))
    print('PARSE_ERRORS', len(errors), errors[:4])
    print('REGULAR_PARTICLES', len(regular))
    print('TEXTURES', Counter(r['texture'] for _, r, _ in regular).most_common(35))
    print('NAMES', Counter(r['name'] for _, r, _ in regular).most_common(45))
    for name, r, summary in regular:
        if re.search('dust|ambient|mist|snow|insect|leaf|smoke', str(summary), re.I):
            print('ENV', name, hex(r['id']), *summary)


if __name__ == '__main__':
    main()
