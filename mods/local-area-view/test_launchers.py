"""验证真实 cmd 入口的编码、路径、暂停及退出码，不操作游戏文件。"""
import os
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    with tempfile.TemporaryDirectory(prefix='launcher test ', dir=ROOT) as directory:
        folder = Path(directory)
        # 替身只返回指定退出码，测试不调用实际安装器。
        (folder / 'patch.py').write_text(
            'import os, sys\nprint("LAUNCHER_ACTION=" + sys.argv[1])\nsys.exit(int(os.environ["LAUNCHER_TEST_EXIT"]))\n',
            encoding='ascii',
        )
        for action in ('install', 'restore', 'status'):
            source = (ROOT / f'{action}.cmd').read_bytes()
            assert b'\r\n' in source and b'\n' not in source.replace(b'\r\n', b'')
            script = folder / f'{action}.cmd'
            script.write_bytes(source)
            for code in (0, 7):
                result = subprocess.run(
                    ['cmd.exe', '/d', '/c', str(script)], input=b'\r\n',
                    capture_output=True, cwd=ROOT.parent,
                    env=dict(os.environ, LAUNCHER_TEST_EXIT=str(code)),
                )
                assert result.returncode == code, (action, code, result.stdout, result.stderr)
                assert f'LAUNCHER_ACTION={action}'.encode() in result.stdout
                assert not result.stderr, result.stderr
                assert b'continue' in result.stdout.lower() or '按任意键'.encode() in result.stdout
                if code:
                    assert '失败'.encode() in result.stdout
            print(f'PASS：{action}.cmd，CRLF、含空格路径、成功/失败退出码和暂停提示')


if __name__ == '__main__':
    main()
