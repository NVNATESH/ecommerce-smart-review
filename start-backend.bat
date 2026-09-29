@echo off
REM Starts the FastAPI backend in this window (http://localhost:8000).
cd /d "%~dp0backend"
call .venv\Scripts\activate
uvicorn main:app --reload
