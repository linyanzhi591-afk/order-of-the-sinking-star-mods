"""以已验证程序组合及原版着色器样本的临时副本验证发行入口。"""
from contextlib import redirect_stdout
import io
from pathlib import Path
import shutil
import tempfile
from unittest.mock import patch as mock
import manager
import patch
import transaction as e


def run(fixtures):
    before = {k:e.file_sha(fixtures/n) for k,n in e.TARGETS.items()}
    with tempfile.TemporaryDirectory(prefix='water-release-tests-',dir=e.ROOT) as directory:
        root=Path(directory).resolve(); assert root.is_relative_to(e.ROOT)
        game=root/'game with spaces'; (game/'data').mkdir(parents=True)
        for name in e.TARGETS.values(): shutil.copyfile(fixtures/name,game/name)
        sentinel=game/'data/materials.package'; sentinel.write_bytes(b'other mods unchanged')
        with mock.object(e,'STATE_ROOT',root/'state'),mock.object(e,'game_running',return_value=False):
            def call(action):
                with redirect_stdout(io.StringIO()): manager.operate(action,game)
            call('check'); call('install')
            assert e.current_hashes(game)=={'exe':patch.WATER_EXE_SHA,'shaders':patch.WATER_SHADER_SHA}
            receipt=e.load_state(e.state_dir(game),game)
            call('install'); assert e.load_state(e.state_dir(game),game)==receipt
            call('uninstall'); call('uninstall'); call('recover')
            assert e.current_hashes(game)==before
            real_replace=e.os.replace; fired=[]
            def fail(source,target):
                if Path(target)==game/'data/shaders.package' and not fired:
                    fired.append(True); raise OSError('模拟第二文件写入失败')
                return real_replace(source,target)
            with mock.object(e.os,'replace',side_effect=fail):
                try: call('install')
                except e.BundleError: pass
                else: raise AssertionError('未触发失败')
            assert e.current_hashes(game)==before
            fired.clear()
            def interrupt(source,target):
                real_replace(source,target)
                if Path(target)==game/'sinking_star.exe' and not fired:
                    fired.append(True); raise KeyboardInterrupt('模拟中断')
            with mock.object(e.os,'replace',side_effect=interrupt):
                try: call('install')
                except KeyboardInterrupt: pass
                else: raise AssertionError('未触发中断')
            call('recover'); call('recover'); assert e.current_hashes(game)==before
            target=game/'data/shaders.package'; data=target.read_bytes(); target.write_bytes(data+b'unknown')
            try: call('install')
            except ValueError: pass
            else: raise AssertionError('未拒绝未知资源')
            assert target.read_bytes()==data+b'unknown'
            assert sentinel.read_bytes()==b'other mods unchanged'
        assert {k:e.file_sha(fixtures/n) for k,n in e.TARGETS.items()}==before
    print('独立水面发行：安装、重复、精确卸载、失败回滚、中断恢复、未知资源拒绝、其他资源保留：PASS')


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(); parser.add_argument('--fixtures',type=Path,required=True)
    run(parser.parse_args().fixtures)
