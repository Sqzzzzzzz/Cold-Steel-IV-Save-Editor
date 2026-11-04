@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 goto no_python
py -3 -c "import sys; sys.exit(sys.version_info < (3,10))"
if errorlevel 1 goto no_python
if not exist ".qt-preview-venv\Scripts\python.exe" (
  py -3 -m venv ".qt-preview-venv"
  if errorlevel 1 goto failed
)
call ".qt-preview-venv\Scripts\activate.bat"
rem Keep unrelated Qt/ICU DLLs on the caller's PATH out of the executable.
set "PATH=%CD%\.qt-preview-venv\Scripts;%SystemRoot%\System32;%SystemRoot%"
python -m pip install -r requirements-dev.txt "pyinstaller>=6,<7" pefile
if errorlevel 1 goto failed
python -m pytest -q
if errorlevel 1 goto failed
python tools\extract_tk_icon.py icons\app_icon.ico
if errorlevel 1 goto failed
python -m PyInstaller --noconfirm --clean --onefile --windowed --name CS4_Inventory_Editor --add-data "icons/original;icons/original" --add-data "icons/app_icon.ico;icons" --add-data "assets;assets" --icon "icons/app_icon.ico" qt_window.py
if errorlevel 1 goto failed
python tools\extract_tk_icon.py --verify-exe dist\CS4_Inventory_Editor.exe icons\app_icon.ico
if errorlevel 1 goto failed
echo.
start /wait "CS4 self-test" dist\CS4_Inventory_Editor.exe --self-test --self-test-report checks\windows-selftest.json
if errorlevel 1 goto failed
python tools\package_release.py
if errorlevel 1 goto failed
echo SUCCESS: dist\CS4_Inventory_Editor.exe
pause
exit /b 0
:no_python
echo Python 3.10 or later is required.
pause
exit /b 1
:failed
echo BUILD FAILED. Please send the full error log.
pause
exit /b 1
