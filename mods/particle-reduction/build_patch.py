"""为 Build 26006400 生成保守的粒子减量补丁清单。"""
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import struct
from research import GAME, package, entities, describe, field_value
from research_schema import schema

ROOT = Path(__file__).resolve().parent
ENV_NAMES = {
    'falling petals', 'falling petals sm', 'falling leaves', 'floating petals',
    'flies', 'gnats', 'firefly scattered', 'firefly cluster', 'firefly general',
    'fireflies', 'drifting sand', 'ambient sand', 'snow_A', 'drifting embers',
    'spores', 'spores outer', 'drifting glows', 'drifting lights',
    'atmospheric spray', 'waterfall_mist_A', 'water_specks',
}
ENV_TEXTURES = {
    'vfx_leaf', 'vfx_insect', 'particle_butterfly', 'vfx_spark', 'contrail',
    'ParticleTest_MASKS_A', 'vfx_smokeFlipbook_02', 'vfx_smokeFlipbook',
}
DRAGON_NAMES = {
    'DrgBrMid_Sparks', 'DrgBrMid_Smoke', 'DrgBrEnd_Smoke',
    'DrgBrStart_Sparks', 'DrgActive_Sparks',
}
BEAM_GROUPS = {
    'GemBeamRadialParticles', 'EndpointBeam', 'GemBeam',
    'DoubleBeamSource', 'DoubleBeamTarget',
}
BEAM_DECOR = {
    'vfx_spark', 'vfx_longSpark', 'vfx_glint',
    'vfx_wizardPoofSm_burst', 'vfx_wizardPoof_burst',
}
PROTECTED_TEXTURES = {
    'vfx_dragonbreath', 'vfx_fireParticle_loop', 'vfx_softGlow',
    'vfx_softSquare', 'vfxTxr_ring_alpha', 'vfxTxr_zap01_alpha',
    'vfxTxr_zap02_alpha', 'vfxTxr_zap03_alpha',
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def policy(record, template):
    name, texture = record['name'], record['texture']
    groups = set(record['groups'])
    if texture in PROTECTED_TEXTURES:
        return None
    if (name in DRAGON_NAMES and texture in {
            'vfx_spark', 'vfx_smokeFlipbook_01'}) or (
            name == 'torchsmoke' and texture in {'vfx_softeningCircle', 'vfx_smokeFlipbook'}):
        return '移除火焰附属粒子', 0.0
    if template and groups & BEAM_GROUPS and texture in BEAM_DECOR:
        return '移除光束附属粒子', 0.0
    if name in ENV_NAMES and texture in ENV_TEXTURES:
        return '环境装饰粒子减半', 0.5
    return None


def build():
    fields = {name: (0x1000+i, offset, kind)
              for i, (_, name, offset, kind) in enumerate(schema())}
    assert fields['particles_per_second'] == (0x1002, 0x338, 1)
    assert fields['enable_burst'] == (0x10d9, 0x7a5, 2)
    assert fields['render_texture'] == (0x109c, 0x668, 4)
    assert fields['particle_emissive'] == (0x10a8, 0x69c, 1)
    source = (GAME/'data/levels.package').read_bytes()
    result = bytearray(source)
    patches, affected, skipped = [], [], []
    entity_count = 0
    for entry, size, offset in package(source):
        if not entry.endswith('.entities'):
            continue
        template = entry.endswith('/ingame_particles.entities')
        records = describe(entities(source[offset:offset+size]))
        entity_count += len(records)
        for r in records:
            if r['type'] != 'Particle_Source':
                continue
            selected = policy(r, template)
            if selected is None:
                continue
            reason, factor = selected
            pps = r['pps']
            base = offset+r['offset']
            field_changes = []

            def change(field, pos, new):
                old = source[base+pos:base+pos+len(new)]
                if old == new:
                    return
                assert result[base+pos:base+pos+len(new)] == old
                result[base+pos:base+pos+len(new)] = new
                patches.append(dict(offset=base+pos, before=old.hex(), after=new.hex(),
                                    entry=entry, entity_id=r['id'], field=field))
                field_changes.append(field)

            if pps is None:
                skipped.append(dict(entry=entry, entity_id=r['id'], reason='生成率字段省略，保守跳过'))
                continue
            assert math.isfinite(pps) and 0 <= pps < 1000000
            p = field_value(r['data'], 0x1002, struct.pack('<f', 150))
            change('particles_per_second', p, struct.pack('<f', pps*factor))
            p = field_value(r['data'], 0x10d9, b'\0')
            if p is not None:
                assert r['data'][p] in (0, 1)
                if factor == 0:
                    change('enable_burst', p, b'\0')
                elif r['data'][p]:
                    # 环境中的突发效果未减量：避免误改带触发语义的反馈。
                    skipped.append(dict(entry=entry, entity_id=r['id'], reason='保留环境突发发射'))
            if field_changes:
                affected.append(dict(entry=entry, entity_id=r['id'], name=r['name'],
                                     groups=r['groups'], texture=r['texture'], reason=reason,
                                     old_pps=pps, new_pps=pps*factor, fields=field_changes))
    patches.sort(key=lambda item: item['offset'])
    for a, b in zip(patches, patches[1:]):
        assert a['offset']+len(bytes.fromhex(a['before'])) <= b['offset']
    assert len(source) == len(result)
    manifest = dict(version='0.1.0-test', build=26006400, file='data/levels.package',
                    original_sha256=sha(source), patched_sha256=sha(result), file_size=len(source),
                    environment_factor=0.5, parsed_entities=entity_count,
                    summary=dict(Counter(r['reason'] for r in affected)),
                    affected=affected, skipped=skipped, patches=patches,
                    validation='结构与安装卸载待验证；实机视觉及帧率未验证')
    (ROOT/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    print(json.dumps({k: manifest[k] for k in ['original_sha256', 'patched_sha256', 'summary']}, ensure_ascii=False))
    print('字段修改', len(patches), '覆盖关卡/模板', len({r['entry'] for r in affected}), '保守跳过', len(skipped))


if __name__ == '__main__':
    build()
