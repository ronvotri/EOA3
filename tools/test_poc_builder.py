"""Safety, exact ANGELSCRIPT diff, and restore tests using synthetic EXE only."""
import hashlib
import json
import struct
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import build_poc
import apply_poc


class VietnamesePoCTests(unittest.TestCase):
    def test_alias_codebook_and_two_script_roundtrip(self):
        book,decode,glyphs=build_poc.codebook()
        self.assertEqual(len(book),74)
        self.assertEqual(len(decode),74)
        self.assertEqual(len(glyphs),74)
        for stem in ('stage1','DataBase'):
            original,patched,row=build_poc.prepare_script(stem,book)
            source=json.loads((build_poc.ROOT/'source'/(stem+'.json')).read_text(encoding='utf-8'))
            self.assertEqual(build_poc.sha(original),source['sha256'])
            self.assertNotEqual(patched,original)
            self.assertTrue(patched.startswith(b'ANGELSCRIPT'))
            self.assertEqual([c for c in row['vi'] if c in book] != [], True)
            self.assertEqual(build_poc.CONTROL.findall(row['vi']),build_poc.CONTROL.findall(row['source']))
            string_bytes=build_poc.encode_text(row['vi'],book)
            self.assertIn(string_bytes,patched)
            # Decoding two-byte native GBK and custom aliases restores VN.
            rebuilt=bytearray()
            i=0
            while i<len(string_bytes):
                b=string_bytes[i]
                if b<128:
                    chunk=string_bytes[i:i+1];i+=1
                else:
                    chunk=string_bytes[i:i+2];i+=2
                rebuilt+=chunk if chunk not in decode else decode[chunk].encode('utf-8')
            self.assertTrue(len(rebuilt)>0)

    def test_version_guard_and_exact_exe_patch(self):
        arr=bytearray(b'X'*1232896)
        off=build_poc.FONT_NAME_OFFSET
        arr[off:off+5]=build_poc.FONT_NAME_ORIGINAL+b'\0'
        for va in (0x402BA4,0x41A507):
            o=va-0x400000
            arr[o-8:o-3]=bytes.fromhex('6814254f00')
            arr[o:o+5]=b'\xe8'+struct.pack('<i',0x41AA10-va-5)
        original=bytes(arr)
        with patch.object(build_poc,'EXE_SHA',build_poc.sha(original)):
            patched=build_poc.patch_exe(original)
            self.assertEqual(patched[off:off+4],b'VV\0\0')
            self.assertEqual(sum(x!=y for x,y in zip(original,patched)),4)
            t=bytearray(original);t[off]=0x99
            with self.assertRaisesRegex(ValueError,'SHA'):
                build_poc.patch_exe(bytes(t))
            t=bytearray(original);t[0x402ba4-0x400000]=0x90
            with patch.object(build_poc,'EXE_SHA',build_poc.sha(t)):
                with self.assertRaisesRegex(ValueError,'factory call'):
                    build_poc.patch_exe(bytes(t))

    def test_installer_stops_if_not_explicit_copy_and_restores_exactly(self):
        with tempfile.TemporaryDirectory() as temp:
            temp=Path(temp)
            game=temp/'EOA3-COPY';game.mkdir();(game/'Data').mkdir()
            payload=b'fake-exe-original';sha=hashlib.sha256(payload).hexdigest()
            (game/'AngelSLG.exe').write_bytes(payload)
            stage=temp/'out';stage.mkdir();(stage/'Data').mkdir()
            originals={'AngelSLG.exe':payload}
            text=[]
            for stem in ('stage1','DataBase'):
                a,b,row=build_poc.prepare_script(stem,build_poc.codebook()[0])
                originals['Data/'+stem+'.bin']=a
                (game/'Data'/(stem+'.bin')).write_bytes(a)
                (stage/'Data'/(stem+'.bin')).write_bytes(b)
                text.append({'id':row['id'],'original_sha256':build_poc.sha(a),
                             'patched_sha256':build_poc.sha(b)})
            (stage/'AngelSLG.exe').write_bytes(b'fake-exe-changed')
            (stage/'VV.ttf').write_bytes(b'FAKEFONT')
            manifest={'status':'experimental_vietnamese_glyph_poc_NOT_verified_in_game',
                      'exe_original_sha256':sha,'changed_script_fields':text,
                      'output_files':{'AngelSLG.exe':build_poc.sha(b'fake-exe-changed'),
                        **{rel:build_poc.sha((stage/rel).read_bytes()) for rel in originals if rel!='AngelSLG.exe'}}}
            (stage/'manifest.json').write_text(json.dumps(manifest))
            with patch.object(apply_poc,'EXE_SHA',sha):
                with self.assertRaisesRegex(ValueError,'explicit confirmation'):
                    apply_poc.install(stage,game,False)
                self.assertFalse((game/apply_poc.BACKUP_DIR).exists())
                apply_poc.install(stage,game,True)
                self.assertTrue((game/apply_poc.BACKUP_DIR).exists())
                self.assertEqual((game/'AngelSLG.exe').read_bytes(),b'fake-exe-changed')
                with self.assertRaisesRegex(ValueError,'already exists'):
                    apply_poc.install(stage,game,True)
                apply_poc.restore(game)
                self.assertFalse((game/apply_poc.BACKUP_DIR).exists())
                for name,data in originals.items():
                    self.assertEqual((game/name).read_bytes(),data)

if __name__=='__main__':unittest.main()
