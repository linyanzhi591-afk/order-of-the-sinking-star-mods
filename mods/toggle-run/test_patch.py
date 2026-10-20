"""在隔离内存中执行游戏原输入分发器及补丁回调，不启动游戏。"""
import ctypes as C
import struct
from pathlib import Path
from build_patch import GAME, ROOT, OFFSET, SIZE, make_callback, sha, ORIGINAL_SHA


def main():
    original = (GAME / 'sinking_star.exe').read_bytes()
    assert sha(original) == ORIGINAL_SHA
    patched = (ROOT / 'sinking_star.toggle-run.exe').read_bytes()
    assert patched[:OFFSET] == original[:OFFSET]
    assert patched[OFFSET + SIZE:] == original[OFFSET + SIZE:]
    assert patched[OFFSET:OFFSET + SIZE] == make_callback()
    kernel = C.WinDLL('kernel32', use_last_error=True)
    kernel.VirtualAlloc.restype = C.c_void_p
    kernel.VirtualAlloc.argtypes = [C.c_void_p, C.c_size_t, C.c_uint32, C.c_uint32]
    kernel.VirtualFree.argtypes = [C.c_void_p, C.c_size_t, C.c_uint32]
    base = kernel.VirtualAlloc(None, 0x1140000, 0x3000, 0x40)
    if not base:
        raise C.WinError(C.get_last_error())
    try:
        C.memmove(base + 0x1000, original[0x400:0x400 + 0x65FD96], 0x65FD96)
        callback = C.CFUNCTYPE(None, C.c_void_p, C.c_uint8)(base + 0x9BFF0)
        dispatch = C.CFUNCTYPE(None, C.c_void_p, C.c_void_p, C.c_void_p)(base + 0x14E8D0)
        keymap = C.create_string_buffer(0x78)
        bindings = C.create_string_buffer(0x50)
        commands = C.create_string_buffer(0x20)
        struct.pack_into('<Q', keymap, 8, C.addressof(commands))
        struct.pack_into('<Q', keymap, 0x28, 2)
        struct.pack_into('<Q', keymap, 0x30, C.addressof(bindings))
        struct.pack_into('<Q', commands, 0x18, base + 0x9BFF0)
        # 两个独立绑定代表键盘与手柄，均指向原有 HoldToRun 回调。
        for index, key in enumerate((16, 200)):
            struct.pack_into('<I', bindings, index * 0x28, key)
        consumed = C.c_uint8()

        def event(key, down):
            data = C.create_string_buffer(0x68)
            struct.pack_into('<III', data, 0, 1, int(down), key)
            dispatch(keymap, data, C.byref(consumed))
            assert consumed.value == 1
            return C.c_uint8.from_address(base + 0xB6A1F8).value

        assert event(16, True) == 1
        assert event(16, False) == 0
        print('PASS: 原版输入分发器/回调基线，松开停止奔跑')
        C.memmove(base + 0x9BFF0, make_callback(), SIZE)
        for key in (16, 200):
            assert event(key, True) == 1
            for _ in range(100):
                assert event(key, True) == 1
            assert event(key, False) == 1
            assert event(key, True) == 0
            for _ in range(100):
                assert event(key, True) == 0
            assert event(key, False) == 0
        print('PASS: 两个独立绑定均实现按下开启/松开保持/再次按下关闭；长按重复不切换')
        assert event(16, True) == 1
        assert event(200, True) == 0
        assert event(16, False) == 0
        assert event(200, False) == 0
        print('PASS: 两个绑定交替和重叠操作，共享奔跑状态')
        C.c_uint64.from_address(base + 0xB6A808).value = 1
        callback(None, 1)
        assert C.c_uint8.from_address(base + 0xB6A1F8).value == 0
        C.c_uint64.from_address(base + 0xB6A808).value = 0
        callback(None, 1)
        assert C.c_uint8.from_address(base + 0xB6A1F8).value == 1
        callback(None, 0)
        assert C.c_uint8.from_address(base + 0xB6A1F8).value == 1
        assert C.c_uint8.from_address(base + 0xB6A200).value == 1
        assert C.c_uint32.from_address(base + 0xB6A1FC).value == 0
        print('PASS: 原模式保护、按下标记、计数器及松开保持；RIP 相对寻址在重定位后正常')
        print('PASS: 补丁范围仅为原回调 56 字节，文件长度和其余字节一致')
    finally:
        kernel.VirtualFree(base, 0, 0x8000)


if __name__ == '__main__':
    main()
