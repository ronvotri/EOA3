"""Explicit install/restore of experiment on a SEPARATELY COPIED EOA3 folder."""
import argparse
import hashlib
import json
import os
import shutil
from pathlib import Path
from build_poc import sha, EXE_SHA

BACKUP_DIR="_EOA3_VIET_POC_BACKUP"
FILES=("AngelSLG.exe","Data/stage1.bin","Data/DataBase.bin")

def read_manifest(stage):
    manifest=json.loads((stage/"manifest.json").read_text(encoding="utf-8"))
    if manifest.get("status")!="experimental_vietnamese_glyph_poc_NOT_verified_in_game" or manifest.get("exe_original_sha256")!=EXE_SHA:
        raise ValueError("Unexpected PoC manifest")
    if set(manifest.get("output_files",{}))!=set(FILES):
        raise ValueError("Missing experiment files")
    for rel,digest in manifest["output_files"].items():
        if sha((stage/rel).read_bytes())!=digest:
            raise ValueError("Staged PoC file has changed: "+rel)
    if not (stage/"VV.ttf").is_file():
        raise ValueError("Locally generated VV.ttf missing")
    return manifest



def launcher_content():
    """Use relative dot: a quoted path ending in backslash breaks Windows argv.

    `cd /d "%~dp0"` is a CMD built-in and is safe; the Python argument MUST NOT
    be `%~dp0` quoted with a trailing backslash.
    """
    return ('@echo off\r\n'
            'setlocal\r\n'
            'chcp 65001 >nul\r\n'
            'cd /d "%~dp0"\r\n'
            'py -3 "_EOA3_VIET_POC_LOCAL_FONT\\run_poc.py" --game-copy .\r\n'
            'set "EXITCODE=%ERRORLEVEL%"\r\n'
            'if not "%EXITCODE%"=="0" echo Chay ban thu that bai, hay chup anh cua so nay.\r\n'
            'pause\r\n'
            'exit /b %EXITCODE%\r\n')


def inspect_installed_copy(folder):
    """Return an error message, or None for a validated installed test copy.

    The code checks hashes of *all three* patched assets and original backups;
    it does not rely on a manifest existing alone.
    """
    folder=Path(folder).resolve()
    backup=folder/BACKUP_DIR
    manifest_path=backup/'manifest.json'
    font=folder/'_EOA3_VIET_POC_LOCAL_FONT'/'VV.ttf'
    local_runner=folder/'_EOA3_VIET_POC_LOCAL_FONT'/'run_poc.py'
    if not manifest_path.is_file():
        return 'Khong thay file backup/manifest.json trong ban sao. Ban thu chua duoc cai day du.'
    if not font.is_file() or not local_runner.is_file():
        return 'Ban thu thieu font VV.ttf hoac file mo game; can tao lai tren ban sao.'
    try:
        manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
        if (manifest.get('status')!='experimental_vietnamese_glyph_poc_NOT_verified_in_game'
                or manifest.get('exe_original_sha256')!=EXE_SHA
                or set(manifest.get('output_files',{}))!=set(FILES)):
            return 'Manifest ban thu khong dung phien ban.'
        for rel in FILES:
            installed=folder/rel
            original=backup/rel
            if not installed.is_file() or not original.is_file():
                return 'Thieu file game hoac backup: '+rel
            if sha(installed.read_bytes())!=manifest['output_files'][rel]:
                return 'File ban thu da thay doi: '+rel
            if rel=='AngelSLG.exe':
                original_expected=EXE_SHA
            else:
                change=next((x for x in manifest.get('changed_script_fields',[])
                             if x.get('id','').startswith(Path(rel).stem+':')),None)
                if not change:
                    return 'Thieu kiem tra file goc: '+rel
                original_expected=change['original_sha256']
            if sha(original.read_bytes())!=original_expected:
                return 'Ban sao luu khong dung SHA: '+rel
    except (OSError,ValueError,TypeError,KeyError,UnicodeDecodeError) as exc:
        return 'Khong doc duoc thong tin ban thu: '+type(exc).__name__
    return None


def repair_launcher_if_installed(folder):
    """Only rewrite launcher after every original/patched asset verifies."""
    problem=inspect_installed_copy(folder)
    if problem:
        raise ValueError(problem)
    target=Path(folder)/'EOA3-RUN-VIET-POC.cmd'
    atomic_write(target,launcher_content().encode('ascii'))
    return target

def atomic_write(path,data):
    temp=path.with_suffix(path.suffix+".poc-tmp")
    temp.write_bytes(data)
    os.replace(str(temp),str(path))


def install(stage,game_copy,confirm=False):
    if not confirm:
        raise ValueError("Refusing to modify files without explicit confirmation that this is a GAME COPY")
    stage=Path(stage).resolve();game_copy=Path(game_copy).resolve()
    if stage.is_relative_to(game_copy) or game_copy.is_relative_to(stage):
        raise ValueError("Stage and game copy must be separate paths")
    manifest=read_manifest(stage)
    backup=game_copy/BACKUP_DIR
    if backup.exists():
        raise ValueError("Backup already exists; restore previous PoC first")
    originals={}
    for rel in FILES:
        f=game_copy/rel
        if not f.is_file():raise ValueError("Missing game-copy file: "+rel)
        originals[rel]=f.read_bytes()
        if rel=="AngelSLG.exe":
            wanted=EXE_SHA
        else:
            text=next((x for x in manifest["changed_script_fields"] if x["id"].startswith(Path(rel).stem+":")),None)
            if text is None:raise ValueError("Missing baseline script record")
            wanted=text["original_sha256"]
        if sha(originals[rel])!=wanted:
            raise ValueError("Game-copy asset differs from known baseline; no files changed: "+rel)
    backup.mkdir()
    try:
        for rel,data in originals.items():
            f=backup/rel;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(data)
        (backup/"manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
        for rel in FILES:
            atomic_write(game_copy/rel,(stage/rel).read_bytes())
        stage_font_dir=game_copy/"_EOA3_VIET_POC_LOCAL_FONT"
        stage_font_dir.mkdir()
        (stage_font_dir/"VV.ttf").write_bytes((stage/"VV.ttf").read_bytes())
        shutil.copy2(Path(__file__).parent/"run_poc.py",stage_font_dir/"run_poc.py")
        (game_copy/"EOA3-RUN-VIET-POC.cmd").write_text(
            launcher_content(),encoding="ascii")
        (game_copy/"EOA3-RESTORE-POC.txt").write_text(
            "To restore: from the extracted builder directory run:\n"
            "py -3 tools\\apply_poc.py restore --game-copy \"PATH_TO_THIS_GAME_COPY\"\n",
            encoding="utf-8")
        problem=inspect_installed_copy(game_copy)
        if problem:
            raise ValueError('Post-install verification failed: '+problem)
    except Exception:
        for rel,data in originals.items():
            atomic_write(game_copy/rel,data)
        shutil.rmtree(backup,ignore_errors=True)
        shutil.rmtree(game_copy/'_EOA3_VIET_POC_LOCAL_FONT',ignore_errors=True)
        for name in ('EOA3-RUN-VIET-POC.cmd','EOA3-RESTORE-POC.txt'):
            (game_copy/name).unlink(missing_ok=True)
        raise
    print("INSTALLED ON GAME COPY ONLY:",game_copy)
    print("Run EOA3-RUN-VIET-POC.cmd in that copy. Restore via apply_poc.py restore.")


def restore(game_copy):
    game_copy=Path(game_copy).resolve()
    backup=game_copy/BACKUP_DIR
    if not (backup/"manifest.json").is_file():
        raise ValueError("No PoC backup found")
    manifest=json.loads((backup/"manifest.json").read_text(encoding="utf-8"))
    for rel in FILES:
        target=game_copy/rel
        if not target.is_file() or sha(target.read_bytes())!=manifest["output_files"][rel]:
            raise ValueError("PoC asset modified since installation; refusing unsafe restore: "+rel)
        b=(backup/rel).read_bytes()
        if rel=="AngelSLG.exe":wanted=EXE_SHA
        else:
            x=next(x for x in manifest["changed_script_fields"] if x["id"].startswith(Path(rel).stem+":"))
            wanted=x["original_sha256"]
        if sha(b)!=wanted:raise ValueError("Backup checksum mismatch: "+rel)
    for rel in FILES:
        atomic_write(game_copy/rel,(backup/rel).read_bytes())
    shutil.rmtree(backup)
    shutil.rmtree(game_copy/"_EOA3_VIET_POC_LOCAL_FONT",ignore_errors=True)
    for name in ("EOA3-RUN-VIET-POC.cmd","EOA3-RESTORE-POC.txt"):
        (game_copy/name).unlink(missing_ok=True)
    print("RESTORED original EXE and both scripts in game COPY:",game_copy)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest="command",required=True)
    install_p=sub.add_parser("install")
    install_p.add_argument("--stage",type=Path,required=True)
    install_p.add_argument("--game-copy",type=Path,required=True)
    install_p.add_argument("--confirm-this-is-a-copy",action="store_true")
    restore_p=sub.add_parser("restore")
    restore_p.add_argument("--game-copy",type=Path,required=True)
    a=p.parse_args()
    try:
        if a.command=="install":install(a.stage,a.game_copy,a.confirm_this_is_a_copy)
        else:restore(a.game_copy)
    except (ValueError,OSError) as exc:
        p.error(str(exc))

if __name__=="__main__":main()
