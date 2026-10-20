"""在临时目录验证俯视升级、卸载保留高亮和网格原载荷与按键。"""
import contextlib
import io
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch as mock
import patch as p
import static_native


def main():
    count = 0
    with tempfile.TemporaryDirectory(dir=p.ROOT, prefix='tmp-compat-') as directory:
        root = Path(directory)
        target = root/'sinking_star.exe'
        for name in ('sinking_star.original.exe', 'sinking_star.toggle-run.exe'):
            baseline = (p.ROOT.parent/'toggle-run'/name).read_bytes()
            for highlight_key in (None, 80):
                for grid_key in (None, 79, static_native.StaticKey(79)):
                    before = p.add_extras(p.transform(baseline, True, 8), highlight_key, grid_key)
                    target.write_bytes(before)
                    for action in ('install', 'restore'):
                        with mock.object(sys, 'argv', ['patch.py', action, '--game-dir', directory]), \
                             mock.object(p, 'ROOT', root), mock.object(p, 'game_running', return_value=False), \
                             contextlib.redirect_stdout(io.StringIO()):
                            p.main()
                        expected_core = p.transform(baseline, True) if action == 'install' else baseline
                        expected = p.add_extras(expected_core, highlight_key, grid_key)
                        assert target.read_bytes() == expected
                        assert p.split_extras(expected) == (expected_core, highlight_key, grid_key)
                        p.validate_windows_image(expected)
                        count += 1
    print(f'PASS：{count}次组合升级/卸载，保留奔跑、高亮、旧网格或静态网格及按键；Windows 格式验证通过')


if __name__ == '__main__':
    main()
