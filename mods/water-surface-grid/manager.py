"""独立水面mod入口：安装、状态、卸载和中断恢复，不控制游戏。"""
import argparse
import os
from pathlib import Path
import struct
import sys
import subprocess
import patch
import transaction as engine

ROOT = Path(__file__).resolve().parent


def dependencies():
    if os.name != 'nt' or sys.version_info < (3,10) or struct.calcsize('P') != 8:
        raise engine.BundleError('需要 Windows x64 与64位 Python 3.10+')
    manifest = engine.read_json(ROOT/'manifest.json')
    for name, expected in manifest['runtime_files_sha256'].items():
        path = ROOT/name
        if not path.resolve().is_relative_to(ROOT) or path.is_symlink() or engine.file_sha(path) != expected:
            raise engine.BundleError('水面发行文件校验失败：'+name)


def operate(action, game):
    dependencies()
    game = engine.validate_game(game)
    folder = engine.state_dir(game)
    if action != 'status':
        engine.ensure_stopped()
    if action in ('status','check'):
        if (folder/'pending.json').exists():
            raise engine.BundleError('有未完成事务，请先运行 recover.cmd')
        state = engine.load_state(folder,game)
        current = engine.read_current(game)
        if state and state['active'] and {k:engine.sha(v) for k,v in current.items()} != state['installed']:
            raise engine.BundleError('安装后文件已被其他操作改变，拒绝覆盖')
        output, enabled = patch.plan(current['exe'],current['shaders'])
        if action == 'check':
            engine.validate_image(output['exe'])
            engine.capacity_check(game,folder,current,output)
        print('水面网格：'+('已安装' if enabled else '未安装')+'；O键切换，启动默认关闭 / Water grid: '+('installed' if enabled else 'not installed')+'; O toggles, off at startup')
        return
    with engine.operation_lock(folder):
        if action == 'recover':
            changed = engine.restore_pending(game,folder)
            print('已恢复中断操作 / Interrupted operation recovered' if changed else '无待恢复事务 / No pending recovery')
            return
        if (folder/'pending.json').exists():
            raise engine.BundleError('有未完成事务，请先运行 recover.cmd')
        state = engine.load_state(folder,game)
        current = engine.read_current(game)
        actual = {k:engine.sha(v) for k,v in current.items()}
        if state and state['active'] and actual != state['installed']:
            raise engine.BundleError('安装后存在其他修改，拒绝覆盖')
        if action == 'install':
            output, enabled = patch.plan(current['exe'],current['shaders'])
            if state and state['active']:
                print('已安装，保留首次备份，不重复写入 / Already installed; first baseline retained')
                return
            engine.validate_image(output['exe'])
        else:
            if not state or not state['active']:
                print('本目录没有活动安装，不移除其他安装器的水面mod / No active installation owned by this folder')
                return
            directory, info = engine.journal(folder,state['baseline_tx'],game)
            if info['action'] != 'install' or info['before'] != state['initial']:
                raise engine.BundleError('初始备份记录不符')
            output = {}
            for key in engine.TARGETS:
                source = directory/(key+'.before')
                engine.reject_link(source)
                output[key] = source.read_bytes()
                if engine.sha(output[key]) != state['initial'][key]:
                    raise engine.BundleError('初始备份损坏，拒绝卸载')
        engine.transaction(game,folder,current,output,state,action)
        print('水面mod安装完成 / Water mod installed' if action == 'install' else '已恢复本mod安装前状态，保留其他mod / Restored pre-install state; other mods retained')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('install','uninstall','recover','status','check'),nargs='?',default='install')
    parser.add_argument('--game-dir',type=Path)
    args = parser.parse_args()
    try:
        operate(args.action,args.game_dir or engine.discover_game())
    except (engine.BundleError,OSError,ValueError,KeyError,TypeError,subprocess.SubprocessError,struct.error) as error:
        print('操作停止 / Operation stopped: '+str(error),file=sys.stderr)
        return 1
    return 0


if __name__=='__main__':
    sys.exit(main())
