"""执行新版镜头载荷和原奔跑分发器；在临时目录验证迁移和卸载。"""
import base64
import ctypes as C
import math
import struct
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch as mock
import patch as p


def main():
    original = (p.ROOT.parent/'toggle-run/sinking_star.original.exe').read_bytes()
    running = (p.ROOT.parent/'toggle-run/sinking_star.toggle-run.exe').read_bytes()
    assert p.sha(original) == p.ORIGINAL_SHA and p.sha(running) == p.RUN_SHA
    for source in (original, running):
        for version in (1, 2, 3, 4, 5, 6, 7, 8, 9):
            output = p.transform(source, True, version)
            assert p.detect_version(output) == (version, source == running)
            assert p.transform(output, False, version) == source
        output = p.transform(source, True)
        allowed = set(range(0x2c0, 0x338)) | {0x7e, 0x7f} | set(range(0xc8, 0xcc))
        for rva, before, after in p.definitions():
            allowed.update(range(rva-0xc00, rva-0xc00+len(before)))
        assert all(i in allowed for i, (a, b) in enumerate(zip(source, output)) if a != b)
        assert output[0x9b3f0:0x9b428] == source[0x9b3f0:0x9b428]
    for offset in (0x500, len(output)-1, p.BASE_SIZE+10):
        bad = bytearray(output); bad[offset] ^= 1
        try:
            p.identify(bad)
        except ValueError:
            pass
        else:
            raise AssertionError('未拒绝篡改')
    print('PASS：九个版本识别与逐字节卸载；新版仅修改三处钩子、PE头和追加节；篡改拒绝')
    k = C.WinDLL('kernel32', use_last_error=True)
    k.VirtualAlloc.argtypes = [C.c_void_p, C.c_size_t, C.c_uint32, C.c_uint32]
    k.VirtualAlloc.restype = C.c_void_p
    k.VirtualFree.argtypes = [C.c_void_p, C.c_size_t, C.c_uint32]
    k.GetBinaryTypeW.argtypes = [C.c_wchar_p, C.POINTER(C.c_uint32)]
    k.LoadLibraryExW.argtypes = [C.c_wchar_p, C.c_void_p, C.c_uint32]
    k.LoadLibraryExW.restype = C.c_void_p
    k.FreeLibrary.argtypes = [C.c_void_p]
    with tempfile.TemporaryDirectory(dir=p.ROOT, prefix='tmp-loader-') as directory:
        path = Path(directory)/'image.exe'
        for source in (original, running):
            path.write_bytes(p.transform(source, True, 3))
            kind = C.c_uint32()
            assert not k.GetBinaryTypeW(str(path), C.byref(kind))
            assert C.get_last_error() == 193
            path.write_bytes(p.transform(source, True))
            assert k.GetBinaryTypeW(str(path), C.byref(kind)) and kind.value == 6
            # 按映像映射并应用重定位，但不执行入口、TLS 或加载依赖 DLL。
            mapped = k.LoadLibraryExW(str(path), None, 1)
            assert mapped, C.get_last_error()
            assert k.FreeLibrary(mapped)
    print('PASS：Windows 复现 v0.1.3 错误193；新版被识别为64位程序并成功按映像加载')
    base = k.VirtualAlloc(None, 0x1150000, 0x3000, 0x40)
    assert base
    state = C.create_string_buffer(0x8000)
    sp = C.addressof(state)
    camera = sp+0x3d98
    data = p.payload()
    symbols = data['symbols']
    try:
        C.memmove(base+0x1000, original[0x400:0x660196], 0x65fd96)
        for section in data['sections']:
            raw = base64.b64decode(section['data'])
            C.memmove(base+section['rva'], raw, len(raw))
        for rva, before, after in p.definitions():
            C.memmove(base+rva, after, len(after))
        C.c_uint64.from_address(base+0xb69600).value = sp
        # 入口后只退出测试桩，仍执行寄存器保存/恢复和真实镜头载荷。
        C.memmove(base+0x25d7c6, bytes.fromhex('415d415e415fc3'), 7)
        begin = C.CFUNCTYPE(None)(base+0x25d7c0)
        toggle = C.CFUNCTYPE(None, C.c_void_p)(base+0x23a820)
        thunk = bytes.fromhex('415541564881ec880000004989cd')
        thunk += b'\x48\xb8'+struct.pack('<Q', base+0x276b66)+bytes.fromhex('ffe0')
        C.memmove(base+0x1141000, thunk, len(thunk))
        tail = bytes.fromhex('4881c488000000415e415dc3')
        C.memmove(base+0x276b6b, tail, len(tail))
        end = C.CFUNCTYPE(None, C.c_void_p)(base+0x1141000)
        active = C.c_uint32.from_address(base+symbols['view']+16)
        def set_normal(yaw, pitch):
            # 游戏镜头局部 +X 向前、+Y 向右、+Z 向上。
            sy, cy = math.sin(yaw/2), math.cos(yaw/2)
            st, ct = math.sin(pitch/2), math.cos(pitch/2)
            q = (-sy*st, cy*st, sy*ct, cy*ct)
            struct.pack_into('<3f', state, 0x6820, 1, 1, 2)
            struct.pack_into('<13f', state, 0x3d98,
                             4, 6, 16, 4, 6, 16, *q, 0.61, 0.2, 200)
            return C.string_at(camera, 52)
        count = 0
        for yaw in [i*math.pi/12 for i in range(-12, 13)]:
            for pitch in (0.15, 0.4, 0.8, 1.2, math.pi/2):
                normal = set_normal(yaw, pitch)
                toggle(None); assert active.value == 1
                for _ in range(3):
                    end(sp)
                    vals = struct.unpack('<13f', C.string_at(camera, 52))
                    x,y,z,w = vals[6:10]
                    forward = (1-2*(y*y+z*z), 2*(x*y+z*w), 2*(x*z-y*w))
                    right = (2*(x*y-z*w), 1-2*(x*x+z*z), 2*(y*z+x*w))
                    assert max(abs(a-b) for a,b in zip(forward, (0,0,-1))) < 2e-5
                    assert max(abs(a-b) for a,b in zip(right, (-math.sin(yaw), math.cos(yaw),0))) < 2e-5
                    distance = 14/math.sin(pitch)*1.17
                    focus_run = 14/math.tan(pitch) if pitch < math.pi/2 else 0
                    shift = distance*math.tan(0.61/2)*0.12
                    expected_x = 4+math.cos(yaw)*(focus_run+shift)
                    expected_y = 6+math.sin(yaw)*(focus_run+shift)
                    assert abs(vals[0]-expected_x) < max(1,abs(expected_x))*3e-5
                    assert abs(vals[1]-expected_y) < max(1,abs(expected_y))*3e-5
                    assert abs(vals[2]-2-distance) < distance*2e-5
                    assert vals[10:13] == struct.unpack('<3f', normal[40:52])
                    begin(); assert C.string_at(camera,52) == normal
                end(sp)
                toggle(None)
                assert active.value == 0 and C.string_at(camera,52) == normal
                count += 1
        print(f'PASS：{count}组朝向/俯仰实际机器码验证：距离增加17%、画面向下偏移6%，退出逐字节恢复')
        # 用户关卡实测四元数。
        normal = struct.pack('<13f', 1.50234,6.464662,14.165462,1.531527,6.473608,14.161679,
                             .3960472047,.3920821548,-.5900656581,.5841581821,.610865,.2,200)
        C.memmove(camera, normal,52)
        struct.pack_into('<f',state,0x6828,0)
        toggle(None); assert active.value
        for _ in range(120):
            end(sp); begin()
            assert C.string_at(camera,52) == normal
        end(sp); first = struct.unpack('<13f',C.string_at(camera,52)); begin()
        C.c_float.from_address(camera).value += 3
        end(sp); second = struct.unpack('<13f',C.string_at(camera,52)); begin()
        assert abs(second[0]-first[0]-3) < 1e-5
        assert second[2] == first[2] and second[6:] == first[6:]
        toggle(None)
        state[0x7f60] = b'\x01'
        toggle(None); assert not active.value
        state[0x7f60] = b'\0'
        toggle(None); assert active.value
        state[0x3dd4] = b'\x01'
        end(sp); assert not active.value
        state[0x3dd4] = b'\0'
        normal = set_normal(0,0)
        toggle(None); assert not active.value
        end(sp); assert C.string_at(camera,52) == normal
        print('PASS：实测关卡数据连续120次无累计漂移；镜头跟随；输入锁、Tab退出及水平镜头保护')
        # 当前关卡查询替身返回指定对象，原版 Q 的其余机器码完整执行。
        level = C.create_string_buffer(0x500)
        levels = C.create_string_buffer(8)
        controls = C.create_string_buffer(24)
        struct.pack_into('<Q', levels, 0, C.addressof(level))
        struct.pack_into('<QQ', state, 0xdd0, 1, C.addressof(levels))
        struct.pack_into('<QQ', state, 0x7e28, 1, C.addressof(controls))
        query = b'\x48\xb8'+struct.pack('<Q',C.addressof(level))+bytes.fromhex('498900c3')
        C.memmove(base+0x2e21e0,query,len(query))
        level[0x3a2]=b'\x01'
        entry, before_hook, after_hook = p.definitions()[0]
        for mode in (0,2):
            for fov in (0.35,0.61,1.2):
                set_normal(1.1,0.8)
                struct.pack_into('<f',state,0x3dc0,fov)
                state[0x3dd4]=bytes([mode])
                before_state=state.raw
                C.memmove(base+entry,before_hook,len(before_hook))
                toggle(None)
                expected=state.raw
                C.memmove(sp,before_state,len(state))
                C.memmove(base+entry,after_hook,len(after_hook))
                toggle(None)
                assert state.raw==expected and not active.value
                end(sp); begin()
                assert state.raw==expected
        # 带原生 per_screen 标记但明确禁用 Q 的关卡继续使用新扩展。
        state[0x3dd4]=b'\0'
        level[0x42e]=b'\x01'
        normal=set_normal(0.3,0.7)
        toggle(None); assert active.value
        end(sp); begin(); toggle(None)
        assert not active.value and C.string_at(camera,52)==normal
        # 大地图不会触发整图适配；与无地图时固定 17% 的结果一致。
        grid = C.create_string_buffer(32)
        struct.pack_into('<2q',grid,0,1000,1000)
        struct.pack_into('<Q',state,0x50,C.addressof(grid))
        normal=set_normal(0.7,0.9)
        toggle(None); end(sp)
        values=struct.unpack('<13f',C.string_at(camera,52))
        fitted=14/math.sin(0.9)*1.17
        shift=fitted*math.tan(0.61/2)*0.12
        assert abs(values[2]-2-fitted)<1e-4
        assert abs(values[0]-4-math.cos(0.7)*(14/math.tan(0.9)+shift))<1e-4
        assert abs(values[1]-6-math.sin(0.7)*(14/math.tan(0.9)+shift))<1e-4
        begin(); toggle(None)
        assert C.string_at(camera,52)==normal
        struct.pack_into('<Q',state,0x50,0)
        print('PASS：大地图仍只增加17%距离，不执行整图适配；退出完整恢复')
        struct.pack_into('<QQ',state,0xdd0,0,0)
        struct.pack_into('<QQ',state,0x7e28,0,0)
        print('PASS：原生支持关卡6组开启/退出与不同FOV结果逐字节等同原版Q；显示钩子不修改其镜头；禁用关卡仍可扩展')
        # 奔跑仍执行原有真实输入分发器。
        C.memmove(base+0x9bff0, running[0x9b3f0:0x9b428], 56)
        dispatch = C.CFUNCTYPE(None,C.c_void_p,C.c_void_p,C.c_void_p)(base+0x14e8d0)
        keymap = C.create_string_buffer(0x78); bindings=C.create_string_buffer(0x50)
        commands=C.create_string_buffer(0x20)
        struct.pack_into('<Q',keymap,8,C.addressof(commands))
        struct.pack_into('<QQ',keymap,0x28,2,C.addressof(bindings))
        struct.pack_into('<Q',commands,0x18,base+0x9bff0)
        for i,key in enumerate((16,200)): struct.pack_into('<I',bindings,i*0x28,key)
        def event(key,down):
            e=C.create_string_buffer(0x68); consumed=C.c_uint8()
            struct.pack_into('<III',e,0,1,down,key)
            dispatch(keymap,e,C.byref(consumed))
            assert consumed.value == 1
            return C.c_uint8.from_address(base+0xb6a1f8).value
        for key in (16,200):
            set_normal(0.3,0.7)
            assert event(key,1)==1
            for _ in range(100): assert event(key,1)==1
            assert event(key,0)==1
            toggle(None); end(sp); begin()
            assert active.value and C.c_uint8.from_address(base+0xb6a1f8).value==1
            assert event(key,1)==0 and active.value
            assert event(key,0)==0
            toggle(None); assert not active.value
        print('PASS：两个奔跑绑定、长按、松开保持和新视图切换互不修改状态')
    finally:
        k.VirtualFree(base,0,0x8000)
    with tempfile.TemporaryDirectory(dir=p.ROOT,prefix='tmp-test-') as directory:
        root=Path(directory); target=root/'sinking_star.exe'
        def action(name, process=False):
            with mock.object(sys,'argv',['patch.py',name,'--game-dir',directory]), \
                 mock.object(p,'ROOT',root), mock.object(p,'game_running',return_value=process):
                p.main()
        target.write_bytes(running)
        try:
            action('install',True)
        except SystemExit:
            pass
        else:
            raise AssertionError('未拦截运行中的游戏')
        assert target.read_bytes()==running
        for source in (original,running):
            for version in (0,1,2,3,4,5,6,7,8,9):
                before=p.transform(source,True,version) if version else source
                target.write_bytes(before)
                action('install'); action('install')
                assert target.read_bytes()==p.transform(source,True)
                action('restore'); action('restore')
                assert target.read_bytes()==source
    print('PASS：原版/奔跑版及两个旧版迁移、重复安装、卸载精确恢复和运行中保护')
    print('限制：上述帧为隔离调用桩，实际游戏画面和实体手柄仍待确认。')


if __name__ == '__main__':
    main()
