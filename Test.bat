@echo off
setlocal
title Gemvox - Diagnostic Test
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

echo Running Gemvox Environment Diagnostic Test...
echo Using Python interpreter: %PY_EXE%
echo.

"%PY_EXE%" -B test_gemvox.py

echo.
echo Press any key to close this test window...
pause >nul
