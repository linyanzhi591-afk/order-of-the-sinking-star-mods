@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0manage.ps1" -Action Install
set "result=%errorlevel%"
pause
exit /b %result%
