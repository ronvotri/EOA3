@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if errorlevel 1 (
    echo Could not open the diagnostic tool folder.
    goto end
)
echo =======================================================
echo EOA3 Windows Diagnostic - READ ONLY
echo This tool will NOT modify or launch your game.
echo =======================================================
echo.
if not exist "build" mkdir "build"
if not exist "build" (
    echo ERROR: Cannot create report folder next to this CMD.
    echo Extract the ZIP to your Desktop or Downloads first.
    goto end
)
set "REPORT=%CD%\build\EOA3-Windows-Diagnostics.zip"
set "LOG=%CD%\build\EOA3-Diagnostic-Log.txt"
if exist "%REPORT%" del /q "%REPORT%"

set "PYTHON_CMD="
where py >nul 2>nul
if not errorlevel 1 (
    py -3 -c "import sys; assert sys.version_info >= (3, 9)" >nul 2>nul
    if not errorlevel 1 set "PYTHON_CMD=py -3"
)
if not defined PYTHON_CMD (
    where python >nul 2>nul
    if not errorlevel 1 (
        python -c "import sys; assert sys.version_info >= (3, 9)" >nul 2>nul
        if not errorlevel 1 set "PYTHON_CMD=python"
    )
)
if not defined PYTHON_CMD (
    echo ERROR: Python 3.9 or newer was not found.
    >"%LOG%" echo Python 3.9 or newer is required. Install Python and retry.
    goto fail
)

if not exist "tools\windows_diagnostic_bundle.py" (
    echo ERROR: Missing tools folder.
    >"%LOG%" echo Extract ALL the files from EOA3-Windows-Diagnostic-Tool.zip before running.
    goto fail
)
if not exist "source\DataBase.json" (
    echo ERROR: Missing source files.
    >"%LOG%" echo Extract ALL the files from EOA3-Windows-Diagnostic-Tool.zip before running.
    goto fail
)

if "%~1"=="" goto choose_exe
echo Checking the AngelSLG.exe that you dragged onto this CMD.
%PYTHON_CMD% "tools\windows_diagnostic_bundle.py" --exe "%~1" --out "%REPORT%" >"%LOG%" 2>&1
goto result

:choose_exe
echo Choose AngelSLG.exe in the file selection window.
echo.
%PYTHON_CMD% "tools\windows_diagnostic_bundle.py" --out "%REPORT%" >"%LOG%" 2>&1

:result
set "RESULT_CODE=%ERRORLEVEL%"
type "%LOG%"
if not "%RESULT_CODE%"=="0" goto fail
if not exist "%REPORT%" (
    echo ERROR: The command finished but the report ZIP is missing.
    goto fail
)
echo.
echo =======================================================
echo SUCCESS! Report created at:
echo "%REPORT%"
echo =======================================================
echo.
echo Opening the build folder now...
start "" "%CD%\build"
echo Send EOA3-Windows-Diagnostics.zip back to the chat.
goto end

:fail
echo.
echo =======================================================
echo REPORT NOT CREATED. See:
echo "%LOG%"
echo =======================================================
echo.
echo Opening the build folder to help you find the error log...
start "" "%CD%\build"
echo Send EOA3-Diagnostic-Log.txt or a photo of this window.
echo Your game files were not modified.

:end
echo.
pause
endlocal
