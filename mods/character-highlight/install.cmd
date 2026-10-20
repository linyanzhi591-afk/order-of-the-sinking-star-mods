@echo off
setlocal
cd /d "%~dp0"
python -X utf8 "%~dp0patch.py" install %*
set "RESULT=%ERRORLEVEL%"
echo.
echo Exit code: %RESULT%
pause
exit /b %RESULT%
