import sys,unittest,tempfile,json,hashlib, shutil
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).parent/'tools'))
import apply_poc, easy_poc

SHA=lambda b:hashlib.sha256(b).hexdigest()

class FixTests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup)
        self.root=Path(self.t.name)
        self.game=self.root/'EOA3-VietHoa-TEST-Existing'
        self.stage=self.root/'stage'
        self.stage.mkdir()
        self.game.mkdir()
        self.originals={
          'AngelSLG.exe':b'MZ-ORIGINAL-FOR-SYNTHETIC-TEST',
          'Data/stage1.bin':b'ANGELSCRIPT-stage1-synthetic',
          'Data/DataBase.bin':b'ANGELSCRIPT-DataBase-synthetic',
        }
        self.patched={r:b+b'-patched' for r,b in self.originals.items()}
        for r,b in self.originals.items():
            p=self.game/r;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
        for r,b in self.patched.items():
            p=self.stage/r;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
        (self.stage/'VV.ttf').write_bytes(b'fake local font')
        self.manifest={
          'status':'experimental_vietnamese_glyph_poc_NOT_verified_in_game',
          'exe_original_sha256':SHA(self.originals['AngelSLG.exe']),
          'output_files':{r:SHA(b) for r,b in self.patched.items()},
          'changed_script_fields':[
            {'id':'stage1:1','original_sha256':SHA(self.originals['Data/stage1.bin'])},
            {'id':'DataBase:1','original_sha256':SHA(self.originals['Data/DataBase.bin'])},
          ]
        }
        (self.stage/'manifest.json').write_text(json.dumps(self.manifest),encoding='utf-8')
        self.p=patch.object(apply_poc,'EXE_SHA',SHA(self.originals['AngelSLG.exe']))
        self.p.start();self.addCleanup(self.p.stop)

    def test_installs_verified_patch_and_repairs_v02_launcher(self):
        self.assertIsNotNone(apply_poc.inspect_installed_copy(self.game))
        apply_poc.install(self.stage,self.game,True)
        self.assertIsNone(apply_poc.inspect_installed_copy(self.game))
        launcher=self.game/'EOA3-RUN-VIET-POC.cmd'
        self.assertIn('--game-copy .',launcher.read_text())
        self.assertNotIn('--game-copy "%~dp0"',launcher.read_text())
        launcher.write_text('py -3 run_poc.py --game-copy "%~dp0"\n')
        repaired=apply_poc.repair_launcher_if_installed(self.game)
        self.assertEqual(repaired,launcher)
        self.assertIn('--game-copy .',launcher.read_text())
        self.assertEqual(self.originals['AngelSLG.exe'],(self.game/apply_poc.BACKUP_DIR/'AngelSLG.exe').read_bytes())
        apply_poc.restore(self.game)
        for r,b in self.originals.items():self.assertEqual(b,(self.game/r).read_bytes())
        self.assertFalse((self.game/apply_poc.BACKUP_DIR).exists())

    def test_incomplete_copy_rejects_repair_without_changes(self):
        apply_poc.install(self.stage,self.game,True)
        launcher=self.game/'EOA3-RUN-VIET-POC.cmd'
        original_launcher=launcher.read_bytes()
        (self.game/'_EOA3_VIET_POC_LOCAL_FONT'/'VV.ttf').unlink()
        self.assertIn('VV.ttf',apply_poc.inspect_installed_copy(self.game))
        with self.assertRaisesRegex(ValueError,'VV.ttf'):
            apply_poc.repair_launcher_if_installed(self.game)
        self.assertEqual(original_launcher,launcher.read_bytes())

    def test_tampered_exe_or_backup_blocks_repair(self):
        apply_poc.install(self.stage,self.game,True)
        (self.game/'AngelSLG.exe').write_bytes(b'BAD')
        self.assertIn('AngelSLG.exe',apply_poc.inspect_installed_copy(self.game))
        with self.assertRaisesRegex(ValueError,'AngelSLG.exe'):
            apply_poc.repair_launcher_if_installed(self.game)

    def test_copy_isolated_and_makes_no_change_to_original(self):
        original_folder=self.root/'Original'
        shutil.copytree(self.game,original_folder)
        target=self.root/'Downloads'/'EOA3-VietHoa-TEST-2'
        target.parent.mkdir()
        with patch.object(easy_poc,'verify_baseline',return_value=original_folder),\
             patch.object(easy_poc.build_poc,'make_poc',side_effect=lambda game,font,stage:shutil.copytree(self.stage,stage)):
            easy_poc.perform(original_folder,target,self.root/'fake-font.ttf')
        self.assertIsNone(apply_poc.inspect_installed_copy(target))
        self.assertEqual((original_folder/'AngelSLG.exe').read_bytes(),self.originals['AngelSLG.exe'])

if __name__=='__main__':unittest.main(verbosity=2)
