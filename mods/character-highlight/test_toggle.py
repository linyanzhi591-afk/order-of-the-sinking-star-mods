"""隔离执行实际 x64 载荷，验证按键边沿、焦点、职业材质与卸载。"""
import base64
import ctypes as C
import struct
from pathlib import Path
import native_toggle as native


def main():
    root=Path(__file__).resolve().parent
    for name in ('sinking_star.original.exe','sinking_star.toggle-run.exe'):
        original=(root.parent/'toggle-run'/name).read_bytes()
        for key in (80,119):
            result=native.apply(original,key)
            assert native.split(result)==(original,key)
            bad=bytearray(result);bad[-100]^=1
            try:native.split(bytes(bad))
            except (ValueError,KeyError,UnicodeDecodeError):pass
            else:raise AssertionError('未拒绝篡改')
    k=C.WinDLL('kernel32',use_last_error=True)
    k.VirtualAlloc.argtypes=[C.c_void_p,C.c_size_t,C.c_uint32,C.c_uint32];k.VirtualAlloc.restype=C.c_void_p
    k.VirtualFree.argtypes=[C.c_void_p,C.c_size_t,C.c_uint32]
    k.GetBinaryTypeW.argtypes=[C.c_wchar_p,C.POINTER(C.c_uint32)]
    k.LoadLibraryExW.argtypes=[C.c_wchar_p,C.c_void_p,C.c_uint32];k.LoadLibraryExW.restype=C.c_void_p
    k.FreeLibrary.argtypes=[C.c_void_p]
    import tempfile
    with tempfile.TemporaryDirectory(dir=root) as directory:
        exe=Path(directory)/'image.exe';exe.write_bytes(result)
        kind=C.c_uint32();assert k.GetBinaryTypeW(str(exe),C.byref(kind)) and kind.value==6
        mapped=k.LoadLibraryExW(str(exe),None,1);assert mapped,C.get_last_error();k.FreeLibrary(mapped)
    base=k.VirtualAlloc(None,0x1150000,0x3000,0x40);assert base
    refs=[]
    try:
        payload=native.payload(0x1140000)
        for s in payload['sections']:
            b=base64.b64decode(s['data']);C.memmove(base+s['rva'],b,len(b))
        setting=(C.c_uint32*4).from_address(base+payload['symbols']['settings'])
        context={'down':False,'pid':77,'key':80}
        fg=C.CFUNCTYPE(C.c_void_p)(lambda:123)
        def window(hwnd,out):C.c_uint32.from_address(out).value=context['pid'];return 1
        wp=C.CFUNCTYPE(C.c_uint32,C.c_void_p,C.c_void_p)(window)
        def proc(module,name):return C.cast(fg if name==b'GetForegroundWindow' else wp,C.c_void_p).value
        callbacks={0x7c0258:C.CFUNCTYPE(C.c_void_p,C.c_void_p)(lambda _:1),
                   0x7c0260:C.CFUNCTYPE(C.c_void_p,C.c_void_p,C.c_char_p)(proc),
                   0x7c01f8:C.CFUNCTYPE(C.c_uint32)(lambda:77),
                   0x7c0000:C.CFUNCTYPE(C.c_short,C.c_int)(lambda key: -32768 if context['down'] and key==context['key'] else 0)}
        for address,callback in callbacks.items():C.c_void_p.from_address(base+address).value=C.cast(callback,C.c_void_p).value
        table=C.create_string_buffer(32*32);refs.append(table)
        C.c_uint64.from_address(base+0x10d4938).value=32
        C.c_void_p.from_address(base+0x10d4960).value=C.addressof(table)
        def resource(name):
            namebuf=C.create_string_buffer(name.encode());record=C.create_string_buffer(80);refs.extend((namebuf,record))
            struct.pack_into('<QQ',record,0,len(name),C.addressof(namebuf));record[32]=b'\x01'
            h=0x1505
            for c in name.encode():h=((h^c)*0x1b3)&0xffffffff
            h=h|2 if h<2 else h
            index=h&31;step=1
            while struct.unpack_from('<I',table,index*32)[0]:index=(index+step)&31;step+=1
            struct.pack_into('<I4xQQQ',table,index*32,h,len(name),C.addressof(namebuf),C.addressof(record))
            return C.addressof(record)
        originals={role:resource(role) for role in ('entity_outline','druid_outline')}
        custom={role:resource(f'ch_{role}_outline') for role in ('warrior','thief','wizard','cleric','bard','druid')}
        # 从真实钩子进入，执行寄存器保存/恢复和 select_outline，再由返回桩退出。
        wrapper=bytes.fromhex('56534883ec284889ce4889d3')
        wrapper+=b'\xe9'+struct.pack('<i',payload['symbols']['hook_outline']-(0x1148000+len(wrapper)+5))
        C.memmove(base+0x1148000,wrapper,len(wrapper))
        tail=bytes.fromhex('4889d84883c4285b5ec3');C.memmove(base+0x3ca951,tail,len(tail))
        call=C.CFUNCTYPE(C.c_void_p,C.c_void_p,C.c_void_p)(base+0x1148000)
        def select(mesh,current):
            name=C.create_string_buffer(mesh.encode());record=C.create_string_buffer(32);obj=C.create_string_buffer(0x90)
            struct.pack_into('<QQ',record,0,len(mesh),C.addressof(name));struct.pack_into('<Q',obj,0x88,C.addressof(record))
            return call(C.addressof(obj),current)
        setting[0]=80
        assert select('warrior',custom['warrior'])==custom['warrior']
        context['down']=True
        assert select('warrior',custom['warrior'])==originals['entity_outline']
        for _ in range(100):assert select('warrior',custom['warrior'])==originals['entity_outline']
        context['down']=False
        for role in custom:
            for suffix in ('','_alt') if role in ('thief','wizard','cleric') else ('',):
                assert select(role+suffix,custom[role])==originals['druid_outline' if role=='druid' else 'entity_outline']
        assert select('goblin',custom['warrior'])==custom['warrior']
        assert select('warrior',originals['druid_outline'])==originals['druid_outline']
        context.update(pid=99,down=True)
        assert select('warrior',custom['warrior'])==originals['entity_outline']
        context.update(pid=77,down=False);select('warrior',custom['warrior'])
        context['down']=True;assert select('warrior',custom['warrior'])==custom['warrior']
        context['down']=False;select('warrior',custom['warrior'])
        setting[0]=119;context['down']=True
        assert select('warrior',custom['warrior'])==custom['warrior']
        context['key']=119;assert select('warrior',custom['warrior'])==originals['entity_outline']
        print('通过：真实钩子机器码、P键双向切换、100次长按去重、失焦保护、F8改键、9个模型、德鲁伊原描边、其他模型及实体覆盖材质保留。')
        print('通过：原版/奔跑基础程序叠加与精确卸载、篡改拒绝及 Windows 映像加载。')
    finally:k.VirtualFree(base,0,0x8000)


if __name__=='__main__':main()
