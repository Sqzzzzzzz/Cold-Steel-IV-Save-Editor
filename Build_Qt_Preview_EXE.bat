@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 goto no_python
py -3 -c "import sys; sys.exit(sys.version_info < (3,10) or sys.version_info >= (3,15))"
if errorlevel 1 goto no_python
if not exist ".qt-preview-venv\Scripts\python.exe" (
  py -3 -m venv ".qt-preview-venv"
  if errorlevel 1 goto failed
)
call ".qt-preview-venv\Scripts\activate.bat"
rem Keep unrelated Qt/ICU DLLs on the caller's PATH out of the executable.
set "PATH=%CD%\.qt-preview-venv\Scripts;%SystemRoot%\System32;%SystemRoot%"
python -m pip install -r requirements-release.txt
if errorlevel 1 goto failed
python tools\build_release.py
if errorlevel 1 goto failed
echo SUCCESS: dist\CS4_Inventory_Editor.exe
pause
exit /b 0
:no_python
echo Python 3.10 through 3.14 is required. Release builds use 64-bit Python 3.14.
pause
exit /b 1
:failed
echo BUILD FAILED. Please send the full error log.
pause
exit /b 1
