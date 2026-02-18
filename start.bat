@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

set "VENV_DIR=venv"
set "MARKER=%VENV_DIR%\.installed"

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: Python not found. Please install Python 3.9+
    exit /b 1
)

if not exist "%VENV_DIR%" (
    echo ▶ Creating virtual environment...
    python -m venv "%VENV_DIR%"
)

call "%VENV_DIR%\Scripts\activate.bat"

if not exist "%MARKER%" (
    echo ▶ Installing dependencies...
    where uv >nul 2>nul
    if !errorlevel! equ 0 (
        uv pip install -r requirements.txt -q 2>nul || pip install -r requirements.txt -q
    ) else (
        pip install -r requirements.txt -q
    )
    type nul > "%MARKER%"
)

echo ▶ Starting server...
python main.py
