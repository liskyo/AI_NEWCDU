@echo off
setlocal
chcp 65001 >nul

:: Set title
title CDU System Launcher V2

:: Change to project root directory
cd /d "%~dp0"

echo ==========================================
echo       CDU System Launcher V2
echo       (Python Backend + Vue Frontend)
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

:: Check Node.js
cmd /c "npm --version" >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed!
    echo Please install Node.js LTS version to run the Vue Frontend.
    echo Download: https://nodejs.org/
    pause
    exit /b
)
echo [CHECK] Node.js is available.

:: ------------------------------------------------
:: 2. Setup Python Environment
:: ------------------------------------------------

echo.
echo [STEP 1/4] Setting up Python Environment...

if not exist "windows_venv" (
    echo    Creating virtual environment 'windows_venv'...
    python -m venv windows_venv
)

echo    Activating virtual environment...
call windows_venv\Scripts\activate

echo    Checking Application dependencies...
pip install --upgrade pip >nul 2>&1
if exist "RestAPI\requirements.txt" (
    echo    Installing RestAPI requirements...
    pip install -r RestAPI\requirements.txt
)

:: ------------------------------------------------
:: 3. Setup Frontend Environment
:: ------------------------------------------------

echo.
echo [STEP 2/4] Setting up Vue Frontend...
cd webUI\frontend

if not exist "node_modules" (
    echo    Detected first run. Installing npm dependencies...
    echo    This may take a few minutes...
    cmd /c "npm install"
) else (
    echo    Dependencies already installed. Skipping npm install.
)

:: Go back to root
cd ..\..

:: ------------------------------------------------
:: 4. Start Services
:: ------------------------------------------------

echo.
echo [STEP 3/4] Starting RestAPI (Backend)...
:: Start Backend in a new minimized window
start "CDU Backend (Port 5001)" /min cmd /k "call windows_venv\Scripts\activate && cd RestAPI && python app.py"

echo    Backend launching... waiting 5 seconds...
timeout /t 5 >nul

echo.
echo [STEP 4/4] Starting Vue Frontend...
echo    The browser should open automatically.
echo.

:: Start Frontend (this will stay in the current window or open a new one depending on preference)
:: Using start to keep this batch file open for a moment then close, or keep it as controller
cd webUI\frontend
:: 'npm run dev' usually runs Vite on port 5173
start "CDU Frontend" cmd /k "npm run dev"

echo ==========================================
echo       System Launch Initiated!
echo ==========================================
echo.
echo Backend URL: http://localhost:5001 (API)
echo Frontend URL: http://localhost:5173 (UI)
echo.
echo NOTE: Do not close the backend/frontend terminal windows.
echo To stop the system, close the terminal windows.
echo.
pause
