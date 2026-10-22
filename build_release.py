"""按白名单构建发行包，排除游戏数据、状态目录及 Git 历史。"""
import argparse
import ast
import hashlib
from pathlib import Path
import zipfile
import bundle

ROOT = Path(__file__).resolve().parent
ROOT_FILES = ['.gitignore','.gitattributes','README.md','INTEGRATING_MODS.md','VALIDATION.md',
              'RELEASE_NOTES.md','bundle.py','bundle.json','bundle-files.json','build_release.py',
              'install.cmd','uninstall.cmd','recover.cmd','status.cmd','check.cmd','tests/test_bundle.py']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    bundle.dependency_check()
    report = bundle.read_json(ROOT/'test-results.json')
    if not report.get('passed') or not report.get('fixture_game_files_unchanged') or report.get('actual_game_used'):
        raise SystemExit('必须先通过临时副本测试 / Passing temporary-copy tests are required')
    if report.get('bundle_sha256') != bundle.file_sha(ROOT/'bundle.py'):
        raise SystemExit('测试结果不对应当前安装器 / Test results do not match the current installer')
    files = ROOT_FILES + sorted(bundle.read_json(ROOT/'bundle-files.json'))
    for name in files:
        path = ROOT/name
        if not path.is_file() or not path.resolve().is_relative_to(ROOT) or path.is_symlink():
            raise SystemExit('Invalid release file: '+name)
        if path.suffix.lower() in ('.exe','.package','.mesh_outlines','.zip') or '.git' in path.parts:
            raise SystemExit('Excluded file type: '+name)
        if path.suffix == '.py':
            ast.parse(path.read_text(encoding='utf-8-sig'),filename=name)
        if path.suffix == '.cmd':
            raw = path.read_bytes()
            assert b'\r\n' in raw and b'\n' not in raw.replace(b'\r\n',b''),name
    checksums = ''.join(f'{hashlib.sha256((ROOT/name).read_bytes()).hexdigest()}  {name}\n' for name in files)
    (ROOT/'SHA256SUMS.txt').write_text(checksums,encoding='ascii',newline='\n')
    args.output.mkdir(parents=True,exist_ok=True)
    name = f'order-of-the-sinking-star-mods-v{bundle.VERSION}-build26006400.zip'
    archive = args.output/name
    sum_path = args.output/f'order-of-the-sinking-star-mods-v{bundle.VERSION}-SHA256SUMS.txt'
    if archive.exists() or sum_path.exists():
        raise SystemExit('目标发行文件已存在，拒绝覆盖 / Release outputs already exist; refusing to overwrite')
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for item in files+['SHA256SUMS.txt']:
            z.write(ROOT/item,'order-of-the-sinking-star-mods/'+item)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for line in checksums.splitlines():
            expected,item = line.split('  ',1)
            assert hashlib.sha256(z.read('order-of-the-sinking-star-mods/'+item)).hexdigest()==expected,item
        assert not any('/.git/' in n or '/.bundle-state/' in n or n.endswith(('.exe','.package','.mesh_outlines')) for n in z.namelist())
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    sum_path.write_text(digest+'  '+name+'\n',encoding='ascii',newline='\n')
    print(archive)
    print(sum_path)
    print('SHA-256: '+digest)


if __name__ == '__main__':
    main()
