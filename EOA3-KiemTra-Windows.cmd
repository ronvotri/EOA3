@echo off
setlocal
cd /d "%~dp0"
echo =======================================================
echo EOA3 Windows Diagnostic - READ ONLY
echo Does not modify, patch, install, or launch the game.
echo =======================================================
echo.
where py >nul 2>nul
if not errorlevel 1 goto use_py
where python >nul 2>nul
if not errorlevel 1 goto use_python
echo Python 3.9 or newer is needed. Install Python and try again.
goto end

:use_py
set "PYTHON_CMD=py -3"
goto run

:use_python
set "PYTHON_CMD=python"
goto run

:run
if "%~1"=="" goto choose_exe
echo Checking the AngelSLG.exe file you dragged onto this script.
%PYTHON_CMD% "tools\windows_diagnostic_bundle.py" --exe "%~1" --out "build\EOA3-Windows-Diagnostics.zip"
goto result

:choose_exe
echo Choose the ORIGINAL AngelSLG.exe in the window that appears.
%PYTHON_CMD% "tools\windows_diagnostic_bundle.py" --out "build\EOA3-Windows-Diagnostics.zip"

:result
if errorlevel 1 (
    echo.
    echo The check did not finish. No game files were changed.
) else (
    echo.
    echo Report: build\EOA3-Windows-Diagnostics.zip
    echo Check this ZIP before sharing it.
    echo No EXE or font file is included.
)

:end
echo.
pause
endlocal
