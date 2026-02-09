@echo off
setlocal
chcp 65001 >nul

:: Set title
title CDU System Launcher (OLD UI)

:: Change to project root directory
cd /d "%~dp0"

echo ==========================================
echo       CDU System Launcher
echo       (OLD UI Version)
echo ==========================================
echo.

:: ------------------------------------------------
:: 1. Check Prerequisites
:: ------------------------------------------------

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.10+ and check 'Add to PATH'.
    pause
    exit /b
)
echo [CHECK] Python is available.

:: ------------------------------------------------
:: 2. Setup Python Environment
:: ------------------------------------------------

echo.
echo [STEP 1/2] Setting up Python Environment...

if not exist "windows_venv" (
    echo    Creating virtual environment 'windows_venv'...
    python -m venv windows_venv
)

echo    Activating virtual environment...
call windows_venv\Scripts\activate

echo    Checking Application dependencies...
pip install --upgrade pip >nul 2>&1
if exist "webUI\requirements.txt" (
    echo    Installing WebUI requirements...
    pip install -r webUI\requirements.txt
)

:: ------------------------------------------------
:: 3. Start Services
:: ------------------------------------------------

echo.
echo [STEP 2/2] Starting Backend (Port 5501)...
:: Start Backend in a new minimized window
start "CDU Backend (Port 5501)" /min cmd /k "call windows_venv\Scripts\activate && cd webUI && python web\app.py"

echo    Backend launching... waiting 5 seconds...
timeout /t 5 >nul

:: Explicitly open the Old UI in default browser
echo    Opening Old UI (http://localhost:5501/login)...
start http://localhost:5501/login

echo ==========================================
echo       System Launch Initiated!
echo ==========================================
echo.
echo [IMPORTANT]
echo The OLD system is now running.
echo - URL: http://localhost:5501
echo.
echo NOTE: Do not close the terminal windows.
echo To stop the system, close the terminal windows.
echo.
pause
