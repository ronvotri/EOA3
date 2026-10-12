@echo off
setlocal
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"
where py >nul 2>&1
if not errorlevel 1 (
    py -3 tools\easy_poc.py
) else (
    where python >nul 2>&1
    if errorlevel 1 (
        echo Khong tim thay Python 3. May da chay V8/V9 thi thuong da co Python.
        echo Gui anh cua so nay cho ChatGPT.
        pause
        exit /b 1
    )
    python tools\easy_poc.py
)
if errorlevel 1 (
    echo.
    echo DA CO LOI: Gui anh cua so nay cho ChatGPT.
)
echo.
echo Ban co the dong cua so nay.
pause
