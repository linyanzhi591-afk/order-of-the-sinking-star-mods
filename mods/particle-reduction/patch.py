"""粒子减量测试版：严格校验、备份、原子安装及卸载，仅修改关卡资源包。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parent
DEFAULT_GAME = Path(r'D:\Program Files (x86)\Steam\steamapps\common\Order of the Sinking Star')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load_manifest():
    m = json.loads((ROOT/'manifest.json').read_text(encoding='utf8'))
    if m['file'] != 'data/levels.package':
        raise ValueError('补丁目标异常')
    previous_end = 0
    for p in m['patches']:
        before, after = bytes.fromhex(p['before']), bytes.fromhex(p['after'])
        if len(before) != len(after) or len(before) not in (1, 4):
            raise ValueError('补丁字段长度异常')
        if p['offset'] < previous_end or p['offset']+len(before) > m['file_size']:
            raise ValueError('补丁范围重叠或越界')
        if p['field'] not in ('particles_per_second', 'enable_burst'):
            raise ValueError('补丁包含未授权字段')
        previous_end = p['offset']+len(before)
    return m


def transform(data, m, install):
    source_hash = m['original_sha256' if install else 'patched_sha256']
    target_hash = m['patched_sha256' if install else 'original_sha256']
    if sha(data) != source_hash or len(data) != m['file_size']:
        raise ValueError('资源版本不匹配或存在其他修改，拒绝覆盖')
    out = bytearray(data)
    for p in m['patches']:
        old = bytes.fromhex(p['before' if install else 'after'])
        new = bytes.fromhex(p['after' if install else 'before'])
        pos = p['offset']
        if data[pos:pos+len(old)] != old:
            raise ValueError('目标字段校验失败')
        out[pos:pos+len(new)] = new
    if sha(out) != target_hash:
        raise ValueError('输出资源校验失败')
    return out


def running():
    result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq sinking_star.exe', '/FO', 'CSV', '/NH'],
                            capture_output=True, check=True)
    return b'sinking_star.exe' in result.stdout.lower()


def atomic_replace(target, data, previous_hash):
    temp = target.with_name(target.name+'.particle-reduction-'+uuid.uuid4().hex+'.tmp')
    try:
        with temp.open('xb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if sha(temp.read_bytes()) != sha(data):
            raise ValueError('临时文件校验失败，未替换原文件')
        if sha(target.read_bytes()) != previous_hash:
            raise ValueError('文件在预检后发生变化，拒绝覆盖')
        if running():
            raise ValueError('游戏正在运行，请退出后重试')
        os.replace(temp, target)
    finally:
        if temp.exists():
            temp.unlink()


def manage(action, game, backup_dir=None):
    m = load_manifest()
    target = game/m['file']
    data = target.read_bytes()
    actual = sha(data)
    state = '已安装' if actual == m['patched_sha256'] else '未安装' if actual == m['original_sha256'] else '未知资源版本或其他修改'
    if action in ('status', 'preview'):
        print(state)
        if action == 'preview':
            print(json.dumps(m['summary'], ensure_ascii=False))
            print('环境装饰生成率：50%；火焰、光束主体及光照参数保留。')
        return
    install = action == 'install'
    expected = m['patched_sha256' if install else 'original_sha256']
    if actual == expected:
        print('无需操作：'+state)
        return
    output = transform(data, m, install)
    if running():
        raise ValueError('游戏正在运行，请退出后重试')
    if install:
        backups = backup_dir or ROOT/'backups'
        backups.mkdir(parents=True, exist_ok=True)
        backup = backups/(m['original_sha256']+'.levels.package')
        if backup.exists():
            if sha(backup.read_bytes()) != m['original_sha256']:
                raise ValueError('已有备份校验失败，拒绝安装')
        else:
            with backup.open('xb') as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            if sha(backup.read_bytes()) != m['original_sha256']:
                raise ValueError('备份校验失败，未修改游戏')
    atomic_replace(target, output, actual)
    if sha(target.read_bytes()) != expected:
        raise ValueError('替换后校验失败，请保留备份并停止操作')
    print('安装完成' if install else '卸载完成，已精确恢复原资源')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['status', 'preview', 'install', 'uninstall'])
    parser.add_argument('--game-dir', type=Path, default=DEFAULT_GAME)
    args = parser.parse_args()
    try:
        manage(args.action, args.game_dir)
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        print('操作停止：'+str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
