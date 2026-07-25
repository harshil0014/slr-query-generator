@echo off
setlocal
cd /d "%~dp0"
set AUTONOMOUS_LOCAL_MODE=
set AUTONOMOUS_REAL_DATA_MODE=true
set AUTONOMOUS_IN_MEMORY_STORAGE=true
echo Starting Autonomous Research with REAL OpenAlex data at http://127.0.0.1:8000/autonomous
echo No demo records will be generated.
start "Autonomous Research" cmd /c "timeout /t 2 /nobreak ^>nul ^& start http://127.0.0.1:8000/autonomous"
python server.py
