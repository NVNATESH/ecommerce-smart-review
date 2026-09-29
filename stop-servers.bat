@echo off
REM Frees ports 3000 and 8000 by killing whatever listens on them.
REM Use this before starting the servers if you see WinError 10013.

for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do taskkill /F /PID %%p >nul 2>&1
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":3000" ^| findstr "LISTENING"') do taskkill /F /PID %%p >nul 2>&1

echo Ports 3000 and 8000 are free.
