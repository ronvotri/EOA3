@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
 py -3 tools\probe_glyph_v9.py %*
) else (
 python tools\probe_glyph_v9.py %*
)
set CODE=%ERRORLEVEL%
echo.
if not "%CODE%"=="0" (
 echo CO LOI - V9 KHONG SUA FILE GAME, XEM DONG BAO LOI O TREN.
) else (
 echo DA TAO build\EOA3-Glyph-V9.zip - KHONG PHAI PATCH.
)
pause
exit /b %CODE%
