@echo off
REM Starts the frontend (http://localhost:3000) in fast production mode.
REM Auto-frees port 3000 first. For frontend development use:  npm run dev

for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":3000" ^| findstr "LISTENING"') do taskkill /F /PID %%p >nul 2>&1

cd /d "%~dp0frontend"
if not exist ".next\BUILD_ID" (
    echo Building production bundle - first run only, please wait...
    call npm run build
)
call npx next start -p 3000
