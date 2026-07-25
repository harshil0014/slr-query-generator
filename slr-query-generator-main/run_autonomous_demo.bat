@echo off
setlocal
cd /d "%~dp0"
set AUTONOMOUS_LOCAL_MODE=true
set AUTONOMOUS_REAL_DATA_MODE=
set AUTONOMOUS_IN_MEMORY_STORAGE=true
echo Starting fixture-only demo mode at http://127.0.0.1:8000/autonomous
echo This mode creates Local Demo records and must not be used for a real review.
start "Autonomous Demo" cmd /c "timeout /t 2 /nobreak ^>nul ^& start http://127.0.0.1:8000/autonomous"
python server.py
