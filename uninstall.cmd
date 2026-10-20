@echo off
setlocal
chcp 65001 >nul
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) and sys.maxsize > 2**32 else 1)" >nul 2>nul
if errorlevel 1 goto try_python
py -3 -B -X utf8 "%~dp0bundle.py" uninstall %*
goto done
:try_python
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) and sys.maxsize > 2**32 else 1)" >nul 2>nul
if errorlevel 1 goto no_python
python -B -X utf8 "%~dp0bundle.py" uninstall %*
goto done
:no_python
echo Python 3.10+ x64 is required. Install Python and enable its launcher or PATH.
set "BUNDLE_EXIT=1"
goto finish
:done
set "BUNDLE_EXIT=%ERRORLEVEL%"
:finish
echo.
echo Exit code: %BUNDLE_EXIT%
pause
exit /b %BUNDLE_EXIT%
