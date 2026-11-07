@echo off
setlocal
title Gemvox

:: Switch to the directory where this script is located
cd /d "%~dp0"

:: Verify that the virtual environment exists
if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment was not found in:
    echo "%~dp0venv"
    echo.
    echo Please ensure the virtual environment is installed.
    echo Press any key to close this window...
    pause >nul
    exit /b 1
)

:: If any arguments were passed, run with console output
if not "%~1"=="" (
    "venv\Scripts\python.exe" gemvox.py %*
    exit /b %errorlevel%
)

:: Launch the accessible GUI without a lingering console window
start "" "venv\Scripts\pythonw.exe" gemvox.py
exit /b 0
