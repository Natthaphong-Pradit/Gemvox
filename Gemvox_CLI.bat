@echo off
setlocal
title Gemvox - Accessible Terminal Menu

:: Switch to the directory where this script is located
cd /d "%~dp0"

:: Verify that the virtual environment exists
if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment was not found in:
    echo "%~dp0venv"
    echo.
    echo Press any key to close this window...
    pause >nul
    exit /b 1
)

:: Launch the accessible interactive terminal CLI
"venv\Scripts\python.exe" gemvox.py --cli

if %errorlevel% neq 0 (
    echo.
    echo [Process finished with exit code %errorlevel%]
    pause
)
