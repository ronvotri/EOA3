"""EOA3 simplified one-click, copy-only Vietnamese glyph prototype.

The user picks original AngelSLG.exe ONCE. The launcher scans a local font,
creates an independent game copy, stages two tiny translation changes, launches
that copy with a temporary font registration, and leaves the original intact.
"""
from __future__ import annotations
import hashlib
import os
import shutil
import sys
import tempfile
import traceback
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDORED = ROOT / 'vendor' / 'fonttools-source.zip'
if VENDORED.is_file():
    sys.path.insert(0, str(VENDORED))

import build_poc
import apply_poc

FONT_CANDIDATES = (
    'arial.ttf', 'segoeui.ttf', 'tahoma.ttf', 'calibri.ttf',
    'verdana.ttf', 'times.ttf', 'trebuc.ttf',
)
MAX_COPY_BYTES = 20 * (1024 ** 3)


def find_local_font(fonts_dir: Path, required_codepoints):
    try:
        from fontTools.ttLib import TTFont
    except ImportError as exc:
        raise RuntimeError('Thư viện fontTools chưa có trong gói; hãy dùng ZIP v0.2 nguyên vẹn.') from exc
    checked = []
    for name in FONT_CANDIDATES:
        candidate = fonts_dir / name
        if not candidate.is_file():
            continue
        try:
            font = TTFont(str(candidate), fontNumber=0, lazy=True)
            try:
                if 'glyf' not in font or 'cmap' not in font:
                    continue
                cmap = font.getBestCmap() or {}
                if all(cp in cmap for cp in required_codepoints):
                    return candidate
                checked.append(name)
            finally:
                font.close()
        except (OSError, ValueError):
            checked.append(name)
    raise RuntimeError('Không tìm thấy font Windows có đủ dấu Việt. Đã kiểm tra: ' + ', '.join(checked or FONT_CANDIDATES))


def verify_baseline(folder: Path):
    """Refuse before copying if input isn't the EXACT documented original."""
    folder = folder.resolve(strict=True)
    exe = folder / 'AngelSLG.exe'
    if not exe.is_file():
        raise ValueError('Thư mục đã chọn không chứa AngelSLG.exe')
    # Read only this EXE and two scripts, no patching yet.
    exe_bytes = exe.read_bytes()
    if build_poc.sha(exe_bytes) != build_poc.EXE_SHA:
        raise ValueError('Sai phiên bản AngelSLG.exe (SHA không khớp). Không sửa game.')
    build_poc.patch_exe(exe_bytes)  # Validate two verified font callers.
    aliases = build_poc.codebook()[0]
    for stem in ('stage1', 'DataBase'):
        original, _, _ = build_poc.prepare_script(stem, aliases)
        path = folder / 'Data' / (stem + '.bin')
        if not path.is_file() or build_poc.sha(path.read_bytes()) != build_poc.sha(original):
            raise ValueError('File gốc không khớp: Data/' + stem + '.bin (chưa sao chép hay sửa).')
    return folder


def safe_scan(source):
    """Reject symlink/reparse paths and estimate copy size without reading data."""
    total = 0
    entries = 0
    def fail_walk(exc):
        raise exc
    for root, dirs, files in os.walk(source, followlinks=False, onerror=fail_walk):
        here = Path(root)
        for name in dirs + files:
            p = here / name
            if p.is_symlink() or (getattr(p.lstat(), 'st_file_attributes', 0) & 0x400):
                raise ValueError('Game có đường dẫn liên kết/junction: ' + str(p) + '; dừng để bảo vệ dữ liệu.')
        for name in files:
            total += (here / name).stat().st_size
            entries += 1
            if total > MAX_COPY_BYTES:
                raise ValueError('Thư mục game quá 20GB; không tự sao chép.')
    return total, entries


def choose_destination(source: Path, downloads: Path, date_tag: str):
    """Downloads is deliberately outside the original game; never overwrite."""
    downloads = downloads.resolve()
    source = source.resolve()
    if downloads == source or downloads.is_relative_to(source):
        raise ValueError('Thư mục Downloads nằm trong game gốc; không thể đặt bản sao an toàn.')
    downloads.mkdir(parents=True, exist_ok=True)
    for i in range(100):
        suffix = ('-' + str(i+1)) if i else ''
        target = downloads / ('EOA3-VietHoa-TEST-' + date_tag + suffix)
        if not target.exists() and not target.with_name(target.name+'-DANG-SAO-CHEP').exists():
            return target
    raise ValueError('Có quá nhiều thư mục bản thử, không tạo trùng.')


def create_copy(source: Path, target: Path, progress=None):
    if target.exists():
        raise FileExistsError('Bản sao thử đã tồn tại; không ghi đè.')
    temp = target.with_name(target.name + '-DANG-SAO-CHEP')
    if temp.exists():
        raise FileExistsError('Thư mục sao chép dở đã tồn tại; không ghi đè.')
    total, entries = safe_scan(source)
    if shutil.disk_usage(target.parent).free < total + 100 * 1024 * 1024:
        raise OSError('Không đủ chỗ trống để tự sao chép game; không sửa gì.')
    copied = 0
    def copy_item(a,b):
        nonlocal copied
        shutil.copy2(a,b)
        copied += 1
        if progress and (copied == entries or copied % 12 == 0):
            progress('Đang tự sao chép game: %d/%d file' % (copied, entries))
        return b
    try:
        shutil.copytree(source, temp, symlinks=False, copy_function=copy_item)
        temp.rename(target)
    except BaseException:
        shutil.rmtree(temp, ignore_errors=True)
        raise
    return target


def perform(source: Path, target: Path, font: Path, progress=None):
    """Automatic COPY -> build -> install. Never patches the input directory."""
    source = verify_baseline(source)
    if progress: progress('Kiểm tra xong game gốc, đang tạo bản sao an toàn...')
    create_copy(source, target, progress)
    try:
        if progress: progress('Đang tạo font VV có dấu và 2 câu thử...')
        with tempfile.TemporaryDirectory(prefix='EOA3-Viet-POC-') as t:
            stage = Path(t) / 'stage'
            build_poc.make_poc(target, font, stage)
            if progress: progress('Đang cài bản thử vào game SAO CHÉP...')
            apply_poc.install(stage, target, True)
        return target
    except BaseException:
        # Keep original intact. Clean only the just-created copy on failure.
        shutil.rmtree(target, ignore_errors=True)
        raise


def main():
    if sys.platform != 'win32':
        raise RuntimeError('Bộ thử một nút chỉ chạy trên Windows.')
    from tkinter import Tk, filedialog, messagebox, Label, Toplevel
    from tkinter.ttk import Progressbar

    root=Tk(); root.withdraw()
    status=None
    try:
        messagebox.showinfo('EOA3 Việt hóa có dấu',
            'Bạn chỉ cần CHỌN FILE AngelSLG.exe của game.\n\n'
            'Tui sẽ tự chọn font, tự sao chép game sang Downloads, và chỉ sửa BẢN SAO.\n'
            'Không cần cài fontTools hay tự tạo bản sao.', parent=root)
        chosen=filedialog.askopenfilename(parent=root,
            title='Chọn file AngelSLG.exe của Empire of Angels III',
            filetypes=[('AngelSLG.exe','AngelSLG.exe'),('Executable','*.exe')])
        if not chosen: return
        exe=Path(chosen)
        if exe.name.lower() != 'angelslg.exe':
            raise ValueError('Hãy chọn đúng AngelSLG.exe.')
        # If user picked a game copy produced by broken v0.2, reuse it.
        # Old launcher passed quoted %~dp0 (trailing slash) as a Python argv,
        # which may resolve to the WRONG directory and display false errors.
        # Verify all patched files AND every original backup before changing
        # anything; never create another multi-GB game copy unnecessarily.
        pre_existing=(exe.parent/apply_poc.BACKUP_DIR/'manifest.json').is_file()
        if pre_existing:
            if not messagebox.askyesno('Sửa bản thử cũ (không sao chép lại)',
                'Đã tìm thấy bản thử trong:\n%s\n\n'
                'Tui sẽ kiểm tra và sửa file MỞ GAME bị lỗi đường dẫn, '
                'không chép hay cài lại game. Làm nhé?' % str(exe.parent),parent=root):return
            launcher=apply_poc.repair_launcher_if_installed(exe.parent)
            import subprocess
            subprocess.Popen(['cmd.exe','/c',str(launcher)],cwd=str(exe.parent),
                             creationflags=getattr(subprocess,'CREATE_NEW_CONSOLE',0))
            messagebox.showinfo('Đã sửa nút mở game',
                'Đã kiểm tra đủ file bản thử, backup và sửa lỗi đường dẫn.\n\n'
                'Game thử đang mở; game gốc không bị đụng tới.\n'
                'Từ giờ có thể nhấn EOA3-RUN-VIET-POC.cmd trong bản sao.',parent=root)
            return
        source=verify_baseline(exe.parent)
        alias_map=build_poc.codebook()[2]
        windir=Path(os.environ.get('WINDIR', r'C:\Windows'))
        font=find_local_font(windir/'Fonts', set(alias_map.values()))
        downloads=Path.home()/'Downloads'
        target=choose_destination(source,downloads,time.strftime('%Y%m%d-%H%M%S'))
        total,_=safe_scan(source)
        if not messagebox.askyesno('Xác nhận bản thử',
            'Tui sẽ tự tạo một BẢN SAO GAME khoảng %.1f MB ở:\n%s\n\n'
            'Font Windows tự chọn: %s\n\n'
            'Game gốc KHÔNG bị chỉnh sửa. Bắt đầu nhé?' %
            (total/1024**2,str(target),font.name),parent=root): return
        status=Toplevel(root);status.title('EOA3 - Tạo bản thử an toàn')
        status.geometry('470x145');status.resizable(False,False)
        lbl=Label(status,text='Đang chuẩn bị...',wraplength=445,justify='center')
        lbl.pack(pady=(22,8))
        bar=Progressbar(status,mode='indeterminate',length=400)
        bar.pack(pady=6);bar.start(15)
        status.update()
        def progress(message):
            lbl.config(text=message); status.update()
        perform(source,target,font,progress)
        bar.stop();status.destroy();status=None
        if messagebox.askyesno('Bản thử đã tạo!',
            'XONG! Đã tạo game riêng tại:\n%s\n\n'
            'Game gốc giữ nguyên. Bây giờ mở game thử luôn nhé?' % target,
            parent=root):
            # Simplest next step: keep the CMD launcher in the copy so errors
            # remain visible and the user can take a screenshot.
            import subprocess
            # Do not launch from an incomplete or partially installed copy.
            problem=apply_poc.inspect_installed_copy(target)
            if problem: raise ValueError('Ban thu chua cai xong: '+problem)
            launcher=target/'EOA3-RUN-VIET-POC.cmd'
            subprocess.Popen(['cmd.exe','/c',str(launcher)], cwd=str(target),
                             creationflags=getattr(subprocess,'CREATE_NEW_CONSOLE',0))
            messagebox.showinfo('Đã mở bản thử',
                'Kiểm tra thoại đầu màn 1 và tooltip kỹ năng.\n'
                'Nếu lỗi, chụp lại cửa sổ đen hoặc màn hình game và gửi tui.\n\n'
                'Bản game gốc vẫn nguyên vẹn.',parent=root)
        else:
            messagebox.showinfo('Bạn có thể chơi thử sau',
                'Mở thư mục Downloads và nhấn EOA3-RUN-VIET-POC.cmd trong bản thử.',parent=root)
    except BaseException as exc:
        if status is not None:
            try: status.destroy()
            except Exception: pass
        messagebox.showerror('EOA3 TEST - Chưa thành công',
             str(exc)+'\n\nGame gốc chưa bị chỉnh sửa.',parent=root)
        # The terminal keeps a full trace if launched via .cmd.
        traceback.print_exc()
    finally:
        root.destroy()

if __name__=='__main__': main()
