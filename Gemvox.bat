@echo off
setlocal
title Gemvox

:: Switch to the directory where this script is located
cd /d "%~dp0"
set "PYTHONDONTWRITEBYTECODE=1"

set "PY_EXE="
set "PYW_EXE="

if exist "venv\Scripts\python.exe" (
    set "PY_EXE=venv\Scripts\python.exe"
    set "PYW_EXE=venv\Scripts\pythonw.exe"
) else if exist ".venv\Scripts\python.exe" (
    set "PY_EXE=.venv\Scripts\python.exe"
    set "PYW_EXE=.venv\Scripts\pythonw.exe"
) else if exist "..\venv\Scripts\python.exe" (
    set "PY_EXE=..\venv\Scripts\python.exe"
    set "PYW_EXE=..\venv\Scripts\pythonw.exe"
) else if exist "..\.venv\Scripts\python.exe" (
    set "PY_EXE=..\.venv\Scripts\python.exe"
    set "PYW_EXE=..\.venv\Scripts\pythonw.exe"
)

if "%PY_EXE%"=="" (
    python -c "import wx, google.genai" >nul 2>&1
    if not errorlevel 1 (
        set "PY_EXE=python"
        set "PYW_EXE=pythonw"
    )
)

if "%PY_EXE%"=="" (
    echo [Gemvox Setup] Virtual environment not found in "%~dp0venv".
    echo Creating virtual environment and installing dependencies automatically...
    python -m venv venv
    if errorlevel 1 (
        py -3 -m venv venv
    )
    if not exist "venv\Scripts\python.exe" (
        echo [ERROR] Could not create Python virtual environment.
        echo Please ensure Python 3.9+ is installed and added to PATH.
        pause
        exit /b 1
    )
    "venv\Scripts\python.exe" -m pip install --upgrade pip
    "venv\Scripts\python.exe" -m pip install -r requirements.txt
    set "PY_EXE=venv\Scripts\python.exe"
    set "PYW_EXE=venv\Scripts\pythonw.exe"
)

:: Verify core dependencies exist in the selected environment
"%PY_EXE%" -c "import wx, google.genai" >nul 2>&1
if errorlevel 1 (
    echo [Gemvox Setup] Installing/updating required packages from requirements.txt...
    "%PY_EXE%" -m pip install -r requirements.txt
)

:: If any arguments were passed, run with console output
if not "%~1"=="" (
    "%PY_EXE%" -B gemvox.py %*
    exit /b %errorlevel%
)

:: Launch the accessible GUI without a lingering console window
if exist "%PYW_EXE%" (
    start "" "%PYW_EXE%" -B gemvox.py
) else (
    start "" "%PY_EXE%" -B gemvox.py
)
exit /b 0

