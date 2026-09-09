@echo off
setlocal
cd /d "%~dp0"
set "PYTHONPATH=%~dp0src"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 -m dikwp_ascent serve "%~dp0workspace" --port 8765
) else (
  python -m dikwp_ascent serve "%~dp0workspace" --port 8765
)
echo.
echo Console ended. Existing research has not been deleted.
pause
