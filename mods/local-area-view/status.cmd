@echo off
chcp 65001 >nul
setlocal
python -X utf8 "%~dp0patch.py" status
set "result=%errorlevel%"
if not "%result%"=="0" echo 状态检查失败，请查看上方原因。
echo.
pause
exit /b %result%
