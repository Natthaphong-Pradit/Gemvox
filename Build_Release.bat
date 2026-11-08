@echo off
chcp 65001 >nul
title Gemvox Release Builder (Standalone EXE + Portable ZIP)
cd /d "%~dp0"

if exist "venv\Scripts\python.exe" (
    set "PY_EXE=venv\Scripts\python.exe"
) else (
    set "PY_EXE=python"
)

echo ====================================================================
echo Building Gemvox Release Packages (Gemvox_Standalone.exe + Portable ZIP)
echo ====================================================================
"%PY_EXE%" -m pip install --upgrade pyinstaller
"%PY_EXE%" build_release.py %*
echo.
pause
