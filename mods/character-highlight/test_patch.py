"""验证原资源全部保留、职业映射范围、安装/卸载和既有补丁共存。"""
import subprocess
import sys
import tempfile
from pathlib import Path
import patch
import native_toggle
import grid_native


def test():
    base = patch.originals()
    original = base['data/materials.package']
    modified = patch.transform('data/materials.package', original)
    old_toc, old_entries = patch.unpack(original)
    new_toc, new_entries = patch.unpack(modified)
    old = {n: (s, o) for n, s, o in old_entries}
    new = {n: (s, o) for n, s, o in new_entries}
    assert len(new) == len(old)+6
    assert modified[24:old_toc] == original[24:old_toc]
    assert modified[:16] == original[:16]
    assert new_toc > old_toc
    for name, (size, offset) in old.items():
        assert new[name] == (size, offset)
        assert modified[offset:offset+size] == original[offset:offset+size]
    for role in patch.COLORS:
        size, offset = new[f'data/materials/ch_{role}_outline.material']
        assert modified[offset:offset+size] == patch.material(role)
    mapping = base['data/mesh_outlines.mesh_outlines']
    updated = patch.transform('data/mesh_outlines.mesh_outlines', mapping)
    before, after = mapping.decode().splitlines(), updated.decode().splitlines()
    assert len(before) == len(after)
    expected = {mesh: f'ch_{role}_outline' for role, (_, _, meshes) in patch.COLORS.items() for mesh in meshes}
    changed = {}
    for a, b in zip(before, after):
        if a != b:
            mesh, material = b.split()
            changed[mesh] = material
    assert changed == expected
    print(f'通过：{len(old)} 个原材质内容和位置保持一致，仅增加 6 个描边材质；仅修改 9 个角色模型映射。')
    with tempfile.TemporaryDirectory(prefix='character highlight test ') as directory:
        game = Path(directory)
        (game/'data').mkdir()
        for name, content in base.items():
            (game/name).write_bytes(content)
        # 使用实际已装奔跑+俯视的 exe，覆盖三补丁共存检查。
        exe = (patch.GAME/'sinking_star.exe').read_bytes()
        (game/'sinking_star.exe').write_bytes(exe)
        def run(action, success=True):
            result = subprocess.run([sys.executable, '-X', 'utf8', str(patch.ROOT/'patch.py'), action, '--game-dir', str(game)], capture_output=True, text=True, encoding='utf8')
            assert (result.returncode == 0) == success, result.stdout+result.stderr
            assert native_toggle.split(grid_native.split((game/'sinking_star.exe').read_bytes())[0])[0] == native_toggle.split(grid_native.split(exe)[0])[0]
        run('install')
        for name, content in base.items():
            assert (game/name).read_bytes() == patch.transform(name, content)
        run('install')
        run('status')
        run('restore')
        for name, content in base.items():
            assert (game/name).read_bytes() == content
        run('restore')
        victim = game/'data/mesh_outlines.mesh_outlines'
        victim.write_bytes(mapping+b'# unknown change\n')
        run('install', False)
        assert victim.read_bytes() == mapping+b'# unknown change\n'
        assert (game/'data/materials.package').read_bytes() == original
    print('通过：含空格路径安装、重复安装、状态检查、逐字节恢复、重复恢复、拒绝未知修改；原有主程序补丁可精确保留。')


if __name__ == '__main__':
    test()
