"""Safety QA for one-click workflow. No real game, font files or Windows needed."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import easy_poc

class EasyPoCTests(unittest.TestCase):
    def test_create_copy_writes_only_new_folder_and_keeps_original(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            src=root/'GAME';(src/'Data').mkdir(parents=True)
            (src/'AngelSLG.exe').write_bytes(b'fake game binary')
            (src/'Data'/'test.bin').write_bytes(b'base')
            target=root/'Downloads'/'EOA3-VietHoa-TEST';target.parent.mkdir()
            original={str(p.relative_to(src)):p.read_bytes() for p in src.rglob('*') if p.is_file()}
            easy_poc.create_copy(src,target)
            for name,data in original.items():
                self.assertEqual((src/name).read_bytes(),data)
                self.assertEqual((target/name).read_bytes(),data)
            with self.assertRaises(FileExistsError):
                easy_poc.create_copy(src,target)

    def test_destination_never_reuses_an_existing_or_original_folder(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);src=p/'Source';src.mkdir();downloads=p/'Downloads';downloads.mkdir()
            a=easy_poc.choose_destination(src,downloads,'v02')
            a.mkdir()
            b=easy_poc.choose_destination(src,downloads,'v02')
            self.assertNotEqual(a,b)
            with self.assertRaisesRegex(ValueError,'nằm trong game gốc'):
                easy_poc.choose_destination(src,src/'Downloads','v02')

    def test_symlink_tree_is_rejected_before_copy(self):
        with tempfile.TemporaryDirectory() as td:
            src=Path(td)/'Source';src.mkdir();(src/'good.txt').write_text('ok')
            try:(src/'secret').symlink_to('/tmp')
            except (OSError,NotImplementedError):self.skipTest('symlink unavailable')
            with self.assertRaisesRegex(ValueError,'liên kết/junction'):
                easy_poc.safe_scan(src)

    def test_auto_workflow_failure_never_changes_source_and_cleans_copy(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);src=p/'Original';src.mkdir();(src/'AngelSLG.exe').write_bytes(b'original')
            dst=p/'EOA3-TEST';out=[]
            with patch.object(easy_poc,'verify_baseline',return_value=src),\
                 patch.object(easy_poc.build_poc,'make_poc',side_effect=RuntimeError('artificial failed')):
                with self.assertRaisesRegex(RuntimeError,'artificial failed'):
                    easy_poc.perform(src,dst,p/'fake.ttf',out.append)
            self.assertEqual((src/'AngelSLG.exe').read_bytes(),b'original')
            self.assertFalse(dst.exists())
            self.assertTrue(any('sao chép' in s for s in out))

    def test_fonttools_available_from_vendor_or_environment(self):
        # Release ZIP vendors the library; GitHub source checks use pip install.
        from fontTools.ttLib import TTFont
        self.assertIsNotNone(TTFont)

if __name__=='__main__':unittest.main()
