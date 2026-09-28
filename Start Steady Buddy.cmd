@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -Command "try { $r = Invoke-RestMethod -Uri 'http://localhost:8765/health' -TimeoutSec 2; if ($r.app -eq 'Steady Buddy') { Start-Process 'http://localhost:8765/'; exit 0 } } catch {}; exit 1"
if not errorlevel 1 exit /b 0
if not exist ".venv\Scripts\python.exe" (
  echo Setting up your buddy...
  where uv >nul 2>nul
  if not errorlevel 1 (
    uv venv --python 3.12 .venv
    if errorlevel 1 goto failed
    uv pip install --python .venv\Scripts\python.exe -r requirements.txt
  ) else (
    py -3.12 -m venv .venv
    if errorlevel 1 goto failed
    .venv\Scripts\python.exe -m pip install -r requirements.txt
  )
  if errorlevel 1 goto failed
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\open_when_ready.ps1"
.venv\Scripts\python.exe run.py
if errorlevel 1 goto failed
exit /b 0
:failed
echo Couldn't start. Check that Python 3.12 and the app dependencies are installed.
pause
exit /b 1
