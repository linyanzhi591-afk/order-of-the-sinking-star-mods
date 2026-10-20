@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0manage.ps1" -Action Restore
set "result=%errorlevel%"
pause
exit /b %result%
