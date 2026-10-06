@echo off
REM Starts the FastAPI backend (http://localhost:8000) in stable production mode.
REM Auto-frees port 8000 first if something is still holding it.
REM For backend development use:  uvicorn main:app --reload

for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do taskkill /F /PID %%p >nul 2>&1

cd /d "%~dp0backend"
call .venv\Scripts\activate
uvicorn main:app --host 127.0.0.1 --port 8000
