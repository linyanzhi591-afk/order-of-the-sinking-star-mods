"""真实资源结构审计及隔离安装回归，不修改游戏目录。"""
from collections import Counter
import contextlib
import io
from pathlib import Path
import shutil
import struct
from unittest.mock import patch as mock
import uuid
import json

import patch
from build_patch import PROTECTED_TEXTURES
from research import GAME, package, entities, describe
from research_schema import schema


def main():
    m = patch.load_manifest()
    source = (GAME/m['file']).read_bytes()
    assert patch.sha(source) == m['original_sha256'], '测试要求未安装本补丁的已知原资源'
    output = patch.transform(source, m, True)
    assert patch.transform(output, m, False) == source
    assert len(output) == len(source)
    field_map = {name: 0x1000+i for i, (_, name, _, _) in enumerate(schema())}
    assert field_map['particles_per_second'] == 0x1002
    assert field_map['enable_burst'] == 0x10d9
    points = {p['offset']: p for p in m['patches']}
    audited, untouched_types = set(), Counter()
    affected_records, protected = 0, 0
    entries = package(source)
    assert entries == package(output), '资源目录、条目位置和长度必须不变'
    for name, size, off in entries:
        before = source[off:off+size]
        after = output[off:off+size]
        if not name.endswith('.entities'):
            assert before == after
            continue
        old_records = describe(entities(before))
        new_records = describe(entities(after))
        assert len(old_records) == len(new_records)
        for old, new in zip(old_records, new_records):
            assert (old['id'], old['type'], old['offset']) == (new['id'], new['type'], new['offset'])
            if old['data'] == new['data']:
                untouched_types[old['type']] += 1
                if old.get('texture') in PROTECTED_TEXTURES:
                    protected += 1
                continue
            assert old['type'] == 'Particle_Source'
            assert old['texture'] not in PROTECTED_TEXTURES
            restored = bytearray(new['data'])
            for local, (a, b) in enumerate(zip(old['data'], new['data'])):
                if a == b:
                    continue
                absolute = off+old['offset']+local
                candidates = [p for pos, p in points.items()
                              if pos <= absolute < pos+len(bytes.fromhex(p['before']))]
                assert len(candidates) == 1
                p = candidates[0]
                start = p['offset']-off-old['offset']
                if p['field'] == 'particles_per_second':
                    assert old['data'][start-7:start] == b'\xfd\x02\x10'+struct.pack('<f', 150)
                else:
                    assert old['data'][start-4:start] == b'\xfd\xd9\x10\0'
                assert p['entry'] == name and p['entity_id'] == old['id']
                audited.add(p['offset'])
                original = bytes.fromhex(p['before'])
                restored[start:start+len(original)] = original
            assert restored == old['data'], '亮度、材质、光源及其他字段必须逐字节不变'
            affected_records += 1
    assert audited == set(points)
    assert affected_records == len(m['affected'])
    assert untouched_types['Point_Light'] > 0

    workspace = Path(__file__).resolve().parent
    work = workspace/'test-work'/uuid.uuid4().hex
    assert work.resolve().is_relative_to((workspace/'test-work').resolve())
    (work/'data').mkdir(parents=True)
    target = work/m['file']
    target.write_bytes(source)
    protected_files = ['sinking_star.exe', 'data/materials.package', 'data/mesh_outlines.mesh_outlines']
    for name in protected_files:
        shutil.copyfile(GAME/name, work/name)
    protected_hashes = {name: patch.sha((work/name).read_bytes()) for name in protected_files}
    backup = work/'backups'
    checks = []

    def call(action, running=False):
        with mock.object(patch, 'running', return_value=running), contextlib.redirect_stdout(io.StringIO()):
            patch.manage(action, work, backup)

    try:
        call('preview')
        assert target.read_bytes() == source
        checks.append('预览只读')
        try:
            call('install', running=True)
            raise AssertionError('未拒绝游戏运行中的安装')
        except ValueError as error:
            assert '正在运行' in str(error)
        assert target.read_bytes() == source and not backup.exists()
        checks.append('运行中拒绝安装')
        with mock.object(patch.os, 'replace', side_effect=OSError('模拟替换失败')):
            try:
                call('install')
                raise AssertionError('未报告替换失败')
            except OSError:
                pass
        assert target.read_bytes() == source
        assert not list((work/'data').glob('*.tmp'))
        checks.append('替换失败保留原文件及备份')
        call('install')
        assert patch.sha(target.read_bytes()) == m['patched_sha256']
        assert (backup/(m['original_sha256']+'.levels.package')).read_bytes() == source
        checks.append('安装与完整备份')
        call('install')
        checks.append('重复安装幂等')
        try:
            call('uninstall', running=True)
            raise AssertionError('未拒绝游戏运行中的卸载')
        except ValueError as error:
            assert '正在运行' in str(error)
        assert patch.sha(target.read_bytes()) == m['patched_sha256']
        checks.append('运行中拒绝卸载')
        call('uninstall')
        assert target.read_bytes() == source
        call('uninstall')
        checks.append('卸载精确恢复及重复卸载')
        corrupted = bytearray(source)
        corrupted[60] ^= 1
        target.write_bytes(corrupted)
        for action in ['install', 'uninstall']:
            try:
                call(action)
                raise AssertionError('未保护未知修改')
            except ValueError:
                assert target.read_bytes() == corrupted
        checks.append('未知资源修改保护')
        target.write_bytes(source)
        backup_file = backup/(m['original_sha256']+'.levels.package')
        backup_file.write_bytes('故障备份'.encode('utf8'))
        try:
            call('install')
            raise AssertionError('未拒绝损坏备份')
        except ValueError as error:
            assert '备份校验失败' in str(error)
        assert target.read_bytes() == source
        checks.append('损坏备份保护')
        assert all(patch.sha((work/name).read_bytes()) == digest for name, digest in protected_hashes.items())
        assert patch.sha((GAME/m['file']).read_bytes()) == m['original_sha256']
        assert all(patch.sha((GAME/name).read_bytes()) == digest for name, digest in protected_hashes.items())
        checks.append('现有四 mod 的程序与材质文件保持原样')
    finally:
        # 仅删除本次生成且已知的准确文件，不递归删除目录。
        for file in [target, *(work/name for name in protected_files),
                     backup/(m['original_sha256']+'.levels.package')]:
            if file.exists():
                file.unlink()
        for directory in [backup, work/'data', work]:
            if directory.exists():
                directory.rmdir()
    result = dict(structure='通过', changed_emitters=affected_records, audited_fields=len(audited),
                  protected_emitters=protected, point_lights_unchanged=untouched_types['Point_Light'],
                  checks=checks, compatibility_hashes=protected_hashes,
                  actual_game_files_changed=False, runtime_visuals='未验证', performance='未测量')
    (workspace/'test-results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    m['validation'] = '资源结构与隔离安装卸载通过；实机视觉及帧率未验证'
    (workspace/'manifest.json').write_text(json.dumps(m, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
