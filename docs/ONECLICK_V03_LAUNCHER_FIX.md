# One-click Vietnamese PoC v0.3: repair of v0.2 launcher quoting

**2026-10-12 — Windows incident report:** A user of the v0.2 one-click artifact saw:

```text
usage: run_poc.py [-h] --game-copy GAME_COPY
run_poc.py: error: PoC has not been installed into this game COPY
```

## Root cause in v0.2 installer

The generated launcher used:

```bat
cd /d "%~dp0"
py -3 "_EOA3_VIET_POC_LOCAL_FONT\run_poc.py" --game-copy "%~dp0"
```

`%~dp0` ends in a backslash. When passed as a *quoted argument* to a Python Windows process, the trailing backslash can escape the quote in the command line parser. Consequently `--game-copy` may point to an incorrect path and `run_poc.py` incorrectly says the PoC is missing. This affects the launcher argument only; it is **not proof the installation failed**.

**Fixed launcher for v0.3:**

```bat
@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
py -3 "_EOA3_VIET_POC_LOCAL_FONT\run_poc.py" --game-copy .
set "EXITCODE=%ERRORLEVEL%"
if not "%EXITCODE%"=="0" echo Chay ban thu that bai, hay chup anh cua so nay.
pause
exit /b %EXITCODE%
```

`cd /d "%~dp0"` remains correct as a CMD built-in, but the Python `--game-copy` parameter is now **`.`** (the current directory, after the preceding `cd`). This also works for paths with spaces or parentheses.

## Recovery workflow packaged in artifact

ChatGPT generated `EOA3-VietHoa-1CLICK-v0.3-FIX.zip` (1,123,884 bytes; **15 entries**, 14 payloads and `THONG-TIN-GOI.json`). This is an experiment, not a playable verified localization. **ZIP bytes and full v0.3 code were delivered in the chat artifact, not committed into this repo.**

1. Extract ZIP and double-click `BAT-DAU-O-DAY.cmd`.
2. **If an existing v0.2 TEST copy was created:** select `AngelSLG.exe` inside `Downloads\EOA3-VietHoa-TEST-...` (not the original EXE).
3. Code detects `_EOA3_VIET_POC_BACKUP/manifest.json`; verifies the hashes of all 3 patched files and all 3 backed-up originals plus local `VV.ttf` and `run_poc.py`; only then replaces `EOA3-RUN-VIET-POC.cmd` with the fixed launcher and opens it. **Does not recopy the game or touch the original.**
4. If no TEST copy exists, select original game EXE; previous automatic-copy workflow continues, but new installations generate the corrected launcher and verify install completion before offering to open.
5. Missing/tampered files cause a clear failure without repairing launcher or launching game.

## Local QA on Python synthetic files

- Previous 8 builder/easy-workflow offline tests passed on modified source.
- Four additional regression tests passed: fresh install + old v0.2 launcher repair + exact restore; incomplete VV font safety stop; tampered EXE safety stop; auto-copy staging keeps original unchanged.
- A clean extraction of the final ZIP passed Python compilation and SHA-256 of all **14 included payload files**.
- **NOT performed:** real Windows GDI runtime validation; in-game font, diacritic placement, dialogue and skill-tooltip visual verification. Do not claim runtime success.

## User-facing next step

If v0.2 created a TEST directory in Downloads, the user only needs to run v0.3 and select that TEST directory's `AngelSLG.exe`. Request a screenshot of the next error or the Vietnamese text in game; **do not ask for a new V8/V9 diagnostic report**. Preserve 1,881 translated strings, 574 review and 573 drafted names. No translation sources or original game files were changed by this repair.
