"""仅以调用者提供的合法原版样本创建临时副本，绝不操作实际游戏。"""
import argparse
from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bundle as b

FIXTURES = None


class BundleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workspace = Path(tempfile.mkdtemp(prefix='bundle-tests-', dir=b.ROOT)).resolve()
        assert cls.workspace.is_relative_to(b.ROOT)
        cls.pristine = b.read_current(FIXTURES)
        b.dependency_check()
        output, _ = b.build_plan(cls.pristine)
        cls.expected = {k: b.sha(v) for k,v in output.items()}
        cls.original_hashes = {k: b.sha(v) for k,v in cls.pristine.items()}
        cls.final = {k: v for k,v in output.items() if k != 'levels'}
        cls.levels_final = cls.workspace/'levels-final.bin'
        cls.levels_final.write_bytes(output['levels'])
        # 大资源只保留原版一份内存，补丁版存于私有测试目录。
        cls.camera, cls.high, cls.particle, cls.world = b.load_logic()

    @classmethod
    def tearDownClass(cls):
        assert cls.workspace.is_relative_to(b.ROOT) and cls.workspace.name.startswith('bundle-tests-')
        shutil.rmtree(cls.workspace)

    def setUp(self):
        self.work = Path(tempfile.mkdtemp(prefix='case-', dir=self.workspace))
        self.game = self.work/'game with spaces'
        (self.game/'data').mkdir(parents=True)
        self.write_game(self.pristine)
        self.state_patch = patch.object(b, 'STATE_ROOT', self.work/'bundle state')
        self.running_patch = patch.object(b, 'game_running', return_value=False)
        self.state_patch.start()
        self.running_mock = self.running_patch.start()

    def tearDown(self):
        self.running_patch.stop()
        self.state_patch.stop()
        assert self.work.resolve().is_relative_to(self.workspace)
        shutil.rmtree(self.work)

    def write_game(self, data):
        for key, value in data.items():
            (self.game/b.TARGETS[key]).write_bytes(value)

    def install_final_fixture(self):
        self.write_game(self.final)
        shutil.copyfile(self.levels_final, self.game/b.TARGETS['levels'])

    def call(self, action):
        with redirect_stdout(io.StringIO()):
            b.operate(action, self.game)

    def folder(self):
        return b.state_dir(self.game.resolve())

    def assert_original(self):
        self.assertEqual(b.current_hashes(self.game), self.original_hashes)

    def test_01_all_partial_plans(self):
        """16 种四 mod 子组合及有世界单步的 6 种已验证组合。"""
        for mask in range(16):
            run, camera, highlight, particle = [bool(mask & (1 << i)) for i in range(4)]
            exe = b.toggle_run(self.pristine['exe']) if run else self.pristine['exe']
            if camera:
                exe = self.camera.transform(exe, True)
            if highlight:
                exe = self.high.native_toggle.apply(exe, 80)
            current = dict(self.pristine, exe=exe)
            if highlight:
                current.update({k:self.final[k] for k in ('materials','outlines')})
            if particle:
                current['levels'] = self.levels_final.read_bytes()
            output, states = b.build_plan(current)
            self.assertEqual(list(states.values()), [run,camera,highlight,particle,False,False])
            self.assertEqual({k:b.sha(v) for k,v in output.items()}, self.expected)
        water = b.water_logic()
        final_world = water.split_native(self.final['exe'],water.native_payload())
        for exe in (self.pristine['exe'], b.toggle_run(self.pristine['exe']), self.world.split(final_world)[0]):
            is_high = exe.endswith(self.high.native_toggle.MARKER)
            for particles in (False, True):
                current = dict(self.pristine, exe=self.world.apply(exe,(78,77)))
                if is_high:
                    current.update({k:self.final[k] for k in ('materials','outlines')})
                if particles:
                    current['levels'] = self.levels_final.read_bytes()
                output, states = b.build_plan(current)
                self.assertTrue(states['world-step'])
                self.assertEqual({k:b.sha(v) for k,v in output.items()}, self.expected)
        output, states = b.build_plan(dict(self.final,levels=self.levels_final.read_bytes()))
        self.assertTrue(all(states.values()))
        self.assertEqual({k:b.sha(v) for k,v in output.items()},self.expected)

    def test_02_install_repeat_uninstall(self):
        self.call('check')
        self.assertFalse(b.STATE_ROOT.exists())
        original_replace = b.replace_from
        observations = []
        def inspect_backups(target, source, expected, desired, txid, key):
            folder = self.folder()
            directory, info = b.journal(folder, txid, self.game.resolve())
            self.assertTrue((folder/'pending.json').is_file())
            for item in b.TARGETS:
                self.assertEqual(b.file_sha(directory/(item+'.before')), info['before'][item])
            observations.append(key)
            return original_replace(target, source, expected, desired, txid, key)
        with patch.object(b, 'replace_from', side_effect=inspect_backups):
            self.call('install')
        self.assertEqual(set(observations), set(b.TARGETS))
        self.assertEqual(b.current_hashes(self.game), self.expected)
        first = b.load_state(self.folder(),self.game.resolve())
        self.call('install')
        self.assertEqual(b.load_state(self.folder(),self.game.resolve()), first)
        self.assertEqual(len(list((self.folder()/'transactions').iterdir())), 1)
        self.call('status')
        self.call('uninstall')
        self.assert_original()
        self.call('uninstall')
        self.assert_original()
        self.call('recover')
        self.call('install')
        self.assertEqual(b.current_hashes(self.game), self.expected)

    def test_03_existing_partial_preserved(self):
        exe = self.high.native_toggle.apply(self.camera.transform(self.pristine['exe'],True),80)
        self.write_game(dict(exe=exe,materials=self.final['materials'],outlines=self.final['outlines']))
        before = b.current_hashes(self.game)
        self.call('install')
        self.assertEqual(b.current_hashes(self.game), self.expected)
        self.call('uninstall')
        self.assertEqual(b.current_hashes(self.game), before)

    def test_04_existing_complete_is_adopted(self):
        self.install_final_fixture()
        with patch.object(b, 'replace_from', side_effect=AssertionError('不应重写游戏')):
            self.call('install')
            self.call('install')
            self.call('uninstall')
        self.assertEqual(b.current_hashes(self.game), self.expected)

    def test_05_running_and_query_failure(self):
        self.running_mock.return_value = True
        with self.assertRaises(b.BundleError):
            self.call('install')
        self.running_mock.side_effect = subprocess.SubprocessError('query failed')
        with self.assertRaises(subprocess.SubprocessError):
            self.call('install')
        self.assert_original()
        self.assertFalse(b.STATE_ROOT.exists())

    def test_06_unknown_and_inconsistent_states(self):
        target = self.game/b.TARGETS['exe']
        target.write_bytes(self.pristine['exe']+b'unknown')
        with self.assertRaises((b.BundleError,ValueError)):
            self.call('install')
        self.assertEqual(target.read_bytes(),self.pristine['exe']+b'unknown')
        self.write_game({'exe':self.pristine['exe'],'materials':self.final['materials']})
        with self.assertRaises(b.BundleError):
            self.call('install')
        self.assertEqual((self.game/b.TARGETS['materials']).read_bytes(),self.final['materials'])

    def test_07_custom_keys_and_grid_rejected(self):
        current = dict(self.pristine, exe=self.high.native_toggle.apply(self.pristine['exe'],119),
                       materials=self.final['materials'],outlines=self.final['outlines'])
        with self.assertRaises(b.BundleError):
            b.build_plan(current)
        water = b.water_logic()
        core, _ = self.world.split(water.split_native(self.final['exe'],water.native_payload()))
        with self.assertRaises(b.BundleError):
            b.build_plan(dict(self.pristine,exe=self.world.apply(core,(117,118))))
        with self.assertRaises(ValueError):
            b.build_plan(dict(self.pristine,exe=self.pristine['exe']+b'GRIDCONST_V4\0'))
        self.assert_original()

    def test_08_disk_backup_and_payload_preflight(self):
        with patch.object(b.shutil,'disk_usage',return_value=shutil._ntuple_diskusage(0,0,0)):
            with self.assertRaises(b.BundleError):
                self.call('install')
        real_write = b.sync_write
        def fail_backup(path,data):
            if path.name.endswith('.before'):
                raise OSError('injected backup failure')
            return real_write(path,data)
        with patch.object(b,'sync_write',side_effect=fail_backup):
            with self.assertRaises(OSError):
                self.call('install')
        self.assert_original()
        self.assertFalse((self.folder()/'pending.json').exists())
        broken = self.work/'broken bundle'
        shutil.copytree(b.ROOT/'mods',broken/'mods')
        for name in ('bundle.json','bundle-files.json'):
            shutil.copy2(b.ROOT/name,broken/name)
        payload = broken/'mods/world-step/payload.json'
        payload.write_bytes(payload.read_bytes()+b' ')
        with patch.object(b,'ROOT',broken):
            with self.assertRaises(b.BundleError):
                self.call('install')
        self.assert_original()

    def fail_on_write(self, interrupt=False):
        actual_replace = b.os.replace
        fired = []
        def replace(source,target):
            target = Path(target)
            if target == self.game/b.TARGETS['materials'] and not fired:
                fired.append(True)
                if interrupt:
                    actual_replace(source,target)
                    raise KeyboardInterrupt('simulated interruption after second file')
                raise OSError('simulated second-file replace failure')
            return actual_replace(source,target)
        return patch.object(b.os,'replace',side_effect=replace)

    def test_09_write_failure_auto_rollback(self):
        with self.fail_on_write():
            with self.assertRaises(b.BundleError):
                self.call('install')
        self.assert_original()
        self.assertFalse((self.folder()/'pending.json').exists())
        self.assertIsNone(b.load_state(self.folder(),self.game.resolve()))

    def test_10_interrupt_recovery_and_unknown_guard(self):
        with self.fail_on_write(interrupt=True):
            with self.assertRaises(KeyboardInterrupt):
                self.call('install')
        self.assertTrue((self.folder()/'pending.json').exists())
        target = self.game/b.TARGETS['outlines']
        target.write_bytes(self.pristine['outlines']+b'unknown after interruption')
        hashes = b.current_hashes(self.game)
        with self.assertRaises(b.BundleError):
            self.call('recover')
        self.assertEqual(b.current_hashes(self.game),hashes)
        target.write_bytes(self.pristine['outlines'])
        self.call('recover')
        self.assert_original()
        self.call('recover')

    def test_11_pending_corrupt_backup(self):
        with self.fail_on_write(interrupt=True):
            with self.assertRaises(KeyboardInterrupt):
                self.call('install')
        txid = b.read_json(self.folder()/'pending.json')['id']
        backup = self.folder()/'transactions'/txid/'outlines.before'
        backup.write_bytes(b'corrupt backup')
        hashes = b.current_hashes(self.game)
        with self.assertRaises(b.BundleError):
            self.call('recover')
        self.assertEqual(b.current_hashes(self.game),hashes)
        backup.write_bytes(self.pristine['outlines'])
        self.call('recover')
        self.assert_original()

    def test_12_uninstall_backup_and_external_change_guard(self):
        self.call('install')
        target = self.game/b.TARGETS['outlines']
        target.write_bytes(self.final['outlines']+b'unknown')
        hashes = b.current_hashes(self.game)
        with self.assertRaises(b.BundleError):
            self.call('uninstall')
        self.assertEqual(b.current_hashes(self.game),hashes)
        target.write_bytes(self.final['outlines'])
        state = b.load_state(self.folder(),self.game.resolve())
        backup = self.folder()/'transactions'/state['baseline_tx']/'outlines.before'
        backup.write_bytes(b'broken')
        with self.assertRaises(b.BundleError):
            self.call('uninstall')
        self.assertEqual(b.current_hashes(self.game),self.expected)

    def test_13_uninstall_interruption_restores_installed_state(self):
        self.call('install')
        with self.fail_on_write(interrupt=True):
            with self.assertRaises(KeyboardInterrupt):
                self.call('uninstall')
        self.call('recover')
        self.assertEqual(b.current_hashes(self.game),self.expected)
        self.assertTrue(b.load_state(self.folder(),self.game.resolve())['active'])
        self.call('uninstall')
        self.assert_original()

    def test_14_lock_and_scratch_guard(self):
        with b.operation_lock(self.folder()):
            with self.assertRaises(b.BundleError):
                with b.operation_lock(self.folder()):
                    pass
        txid = '0'*32
        target = self.game/b.TARGETS['exe']
        temp = target.with_name(target.name+'.bundle-'+txid+'-exe.tmp')
        temp.write_bytes(b'preexisting data')
        with self.assertRaises(FileExistsError):
            b.replace_from(target, FIXTURES/'sinking_star.exe',self.original_hashes['exe'],self.original_hashes['exe'],txid,'exe')
        self.assertEqual(temp.read_bytes(),b'preexisting data')
        self.assert_original()

    def test_15_real_cmd_launchers(self):
        folder = self.work/'launchers with spaces'
        folder.mkdir()
        (folder/'bundle.py').write_text('import os,sys\nprint("ACTION="+sys.argv[1])\nprint("PATH="+sys.argv[3])\nsys.exit(int(os.environ["BUNDLE_TEST_EXIT"]))\n',encoding='ascii')
        for action in ('install','uninstall','recover','status','check'):
            raw = (b.ROOT/(action+'.cmd')).read_bytes()
            self.assertNotIn(b'\n',raw.replace(b'\r\n',b''))
            script = folder/(action+'.cmd')
            script.write_bytes(raw)
            for code in (0,7):
                command = f'cmd.exe /d /s /c ""{script}" --game-dir "{self.game}""'
                result = subprocess.run(command,
                                        capture_output=True,input=b'\r\n',cwd=self.work,
                                        env=dict(os.environ,BUNDLE_TEST_EXIT=str(code),
                                                 PATH=str(Path(sys.executable).parent)+os.pathsep+os.environ.get('PATH','')))
                self.assertEqual(result.returncode,code,result.stdout+result.stderr)
                self.assertIn(('ACTION='+action).encode(),result.stdout)
                self.assertIn(('PATH='+str(self.game)).encode(),result.stdout)

    def test_16_water_unknown_and_old_receipt(self):
        target = self.game/b.TARGETS['shaders']
        target.write_bytes(self.pristine['shaders']+b'unknown')
        before = b.current_hashes(self.game)
        with self.assertRaises(ValueError):
            self.call('install')
        self.assertEqual(b.current_hashes(self.game),before)
        target.write_bytes(self.pristine['shaders'])
        self.write_game(dict(exe=self.final['exe']))
        before = b.current_hashes(self.game)
        with self.assertRaises(b.BundleError):
            self.call('install')
        self.assertEqual(b.current_hashes(self.game),before)
        self.write_game({'exe':self.pristine['exe']})
        folder=self.folder(); folder.mkdir(parents=True,exist_ok=True)
        fake=dict(schema=1,version='1.0.0-test',game=str(self.game.resolve()),active=True,
                  baseline_tx='0'*32,initial={k:v for k,v in self.original_hashes.items() if k!='shaders'},
                  installed={k:v for k,v in self.original_hashes.items() if k!='shaders'})
        b.atomic_json(folder/'state.json',fake)
        with self.assertRaisesRegex(b.BundleError,'原版本合集'):
            self.call('install')
        self.assert_original()
        self.assertEqual(b.read_json(folder/'state.json'),fake)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--fixtures',type=Path,required=True,help='合法原版游戏样本副本，只读 / Read-only pristine game fixture copy')
    parser.add_argument('--report',type=Path)
    parser.add_argument('--only',choices=unittest.defaultTestLoader.getTestCaseNames(BundleTests))
    args = parser.parse_args()
    FIXTURES = b.validate_game(args.fixtures)
    suite = unittest.TestSuite([BundleTests(args.only)]) if args.only else unittest.defaultTestLoader.loadTestsFromTestCase(BundleTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if args.report:
        args.report.write_text(json.dumps({'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
                                          'passed':result.wasSuccessful(),'fixture_game_files_unchanged':b.current_hashes(FIXTURES)==BundleTests.original_hashes,
                                          'actual_game_used':False,'gameplay_validation':False,'selected_test':args.only,
                                          'bundle_sha256':b.file_sha(b.ROOT/'bundle.py')},indent=2)+'\n',encoding='utf8')
    sys.exit(0 if result.wasSuccessful() else 1)
