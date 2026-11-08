@echo off
setlocal
title Gemvox - Accessible Terminal Menu

:: Switch to the directory where this script is located
cd /d "%~dp0"
set "PYTHONDONTWRITEBYTECODE=1"

set "PY_EXE="
if exist "venv\Scripts\python.exe" (
    set "PY_EXE=venv\Scripts\python.exe"
) else if exist ".venv\Scripts\python.exe" (
    set "PY_EXE=.venv\Scripts\python.exe"
) else if exist "..\venv\Scripts\python.exe" (
    set "PY_EXE=..\venv\Scripts\python.exe"
) else if exist "..\.venv\Scripts\python.exe" (
    set "PY_EXE=..\.venv\Scripts\python.exe"
) else (
    set "PY_EXE=python"
)

:: Launch the accessible interactive terminal CLI
"%PY_EXE%" -B gemvox.py --cli

if %errorlevel% neq 0 (
    echo.
    echo [Process finished with exit code %errorlevel%]
    pause
)

