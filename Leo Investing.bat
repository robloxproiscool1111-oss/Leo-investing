@echo off

title Leo Investing - Debug Launcher

cd /d "%~dp0"

echo.
echo ==========================================
echo        LEO INVESTING STARTUP
echo ==========================================
echo.
echo Project folder:
echo %CD%
echo.

REM Delete Python cache folders
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"

REM Prevent Python from creating/loading bytecode cache
set PYTHONDONTWRITEBYTECODE=1

echo Python being used:
where python

echo.
echo Starting Leo Investing...
echo.

python -B -u "%~dp0main.py"

echo.
echo ==========================================
echo Program closed.
echo ==========================================
pause