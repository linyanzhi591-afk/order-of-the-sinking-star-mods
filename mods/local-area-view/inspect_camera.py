"""只读检查当前游戏镜头，不写入进程、游戏文件或存档。"""
import ctypes as C
import json
import struct
import subprocess


def snapshot():
    info = json.loads(subprocess.check_output([
        'powershell', '-NoProfile', '-Command',
        "Get-Process sinking_star | Select-Object Id,@{n='Base';e={$_.MainModule.BaseAddress.ToInt64()}} | ConvertTo-Json -Compress",
    ]))
    kernel = C.WinDLL('kernel32', use_last_error=True)
    kernel.OpenProcess.argtypes = [C.c_uint32, C.c_int, C.c_uint32]
    kernel.OpenProcess.restype = C.c_void_p
    kernel.ReadProcessMemory.argtypes = [C.c_void_p, C.c_void_p, C.c_void_p, C.c_size_t, C.c_void_p]
    kernel.CloseHandle.argtypes = [C.c_void_p]
    handle = kernel.OpenProcess(0x1010, False, info['Id'])
    if not handle:
        raise C.WinError(C.get_last_error())
    def read(address, size):
        buf = C.create_string_buffer(size)
        if not kernel.ReadProcessMemory(handle, address, buf, size, None):
            raise C.WinError(C.get_last_error())
        return buf.raw
    def pointer(address):
        return struct.unpack('<Q', read(address, 8))[0]
    try:
        state = pointer(info['Base'] + 0xB69600)
        grid = pointer(state + 0x50)
        window = pointer(info['Base'] + 0x802C88)
        print('地图宽高', struct.unpack('<2q', read(grid, 16)))
        print('窗口宽高', struct.unpack('<2i', read(window+0x38, 8)))
        levels = pointer(state+0xdd8)
        for i in range(min(pointer(state+0xdd0), 4)):
            item = pointer(levels+8*i)
            print('关卡', i, '屏格/原点', struct.unpack('<6i', read(item+0x3a8, 24)))
        camera = read(state + 0x3D98, 0xE8)
        print('进程', info['Id'], '模式', camera[0x3C])
        print('跟随点', struct.unpack('<3f', read(state + 0x6820, 12)))
        for off in range(0, 0xE8, 16):
            data = camera[off:off + 16]
            print(f'camera+{off:02x}', tuple(round(x, 6) for x in struct.unpack('<'+'f'*(len(data)//4), data)))
        count = pointer(state + 0x538)
        array = pointer(state + 0x540)
        print('普通镜头数量', count)
        for i in range(min(count, 4)):
            obj = pointer(array + 8*i)
            print('普通镜头', i, '位置', struct.unpack('<3f', read(obj, 12)),
                  '旋转', struct.unpack('<4f', read(obj+0x18, 16)))
            print('参数 344..380', struct.unpack('<15f', read(obj+0x344, 60)))
    finally:
        kernel.CloseHandle(handle)


if __name__ == '__main__':
    snapshot()
