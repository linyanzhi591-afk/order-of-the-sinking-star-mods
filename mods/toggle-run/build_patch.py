"""为已验证版本生成仅修改奔跑回调的原生补丁。"""
import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent
GAME = Path(r'D:\Program Files (x86)\Steam\steamapps\common\Order of the Sinking Star')
ORIGINAL_SHA = 'd802098b7cb85eadfc733b88d1554042fad950c572e916febea3f669a474a549'
RVA = 0x9D890
OFFSET = RVA - 0x1000 + 0x400
SIZE = 56


def make_callback():
    code = bytearray()

    def rip(op, target, tail=b''):
        code.extend(op + struct.pack('<i', target - (RVA + len(code) + len(op) + 4 + len(tail))) + tail)

    # 保留原函数的模式检查；输入系统已在每个绑定处过滤长按重复。
    rip(b'\x48\x83\x3d', 0xB69810, b'\x01')
    code.extend(b'\x74\x00')
    first_jump = len(code) - 1
    code.extend(b'\x84\xd2\x74\x00')
    release_jump = len(code) - 1
    rip(b'\x80\x35', 0xB69200, b'\x01')  # 翻转奔跑状态
    rip(b'\x0f\xb6\x05', 0xB69200)
    rip(b'\x88\x05', 0xB69208)  # 本次按下标记与新状态一致
    rip(b'\xc6\x05', 0xB69209, b'\x00')
    rip(b'\xc7\x05', 0xB69204, b'\x00' * 4)
    end = len(code)
    code.append(0xC3)
    for jump in (first_jump, release_jump):
        code[jump] = end - (jump + 1)
    assert len(code) <= SIZE
    return bytes(code).ljust(SIZE, b'\x90')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    original = (GAME / 'sinking_star.exe').read_bytes()
    if sha(original) != ORIGINAL_SHA:
        raise SystemExit('原程序版本不匹配，拒绝生成补丁。')
    patched = bytearray(original)
    patch = make_callback()
    patched[OFFSET:OFFSET + SIZE] = patch
    (ROOT / 'sinking_star.toggle-run.exe').write_bytes(patched)
    manifest = {
        'build_id': 26249670,
        'original_sha256': sha(original),
        'patched_sha256': sha(patched),
        'file_offset': OFFSET,
        'rva': RVA,
        'size': SIZE,
        'original_bytes': original[OFFSET:OFFSET + SIZE].hex(),
        'patched_bytes': patch.hex(),
        'changed_byte_count': sum(a != b for a, b in zip(original, patched)),
    }
    (ROOT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
