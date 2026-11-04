@echo off
setlocal
cd /d "%~dp0"
if not exist ".qt-preview-venv\Scripts\python.exe" (
  py -3 -m venv ".qt-preview-venv"
  if errorlevel 1 goto failed
)
call ".qt-preview-venv\Scripts\activate.bat"
python -m pip install -r requirements-dev.txt
if errorlevel 1 goto failed
python -m pytest -q
if errorlevel 1 goto failed
python qt_window.py --self-test --self-test-report checks\windows-source-selftest.json
if errorlevel 1 goto failed
echo Checks passed.
pause
exit /b 0
:failed
echo Check failed. Please send this log.
pause
exit /b 1
