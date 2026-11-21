@echo off
rem Cross-platform hook launcher for Windows cmd.exe / PowerShell (Codex commandWindows, manual use).
rem Picks the first working Python 3.10+ (py -3, python, python3) and runs scripts\sdlc_hook.py.
rem Fail-closed: exit 2 when no suitable Python exists.
setlocal
set "ENTRY=%~dp0..\sdlc_hook.py"
set "CHECK=import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"

py -3 -c "%CHECK%" >nul 2>nul
if errorlevel 1 goto try_python
py -3 "%ENTRY%" %*
exit /b %errorlevel%

:try_python
python -c "%CHECK%" >nul 2>nul
if errorlevel 1 goto try_python3
python "%ENTRY%" %*
exit /b %errorlevel%

:try_python3
python3 -c "%CHECK%" >nul 2>nul
if errorlevel 1 goto fail
python3 "%ENTRY%" %*
exit /b %errorlevel%

:fail
>&2 echo BLOCKED: sdlc-hook could not find Python 3.10+ (tried py -3, python, python3). Install Python 3.10+ then run: py -3 scripts\setup.py
exit /b 2
