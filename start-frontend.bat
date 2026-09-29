@echo off
REM Starts the Next.js frontend in this window (http://localhost:3000).
cd /d "%~dp0frontend"
call npm run dev
