@echo off
setlocal
chcp 65001 >nul

:: Set title
title CDU System Launcher (New UI)

:: Change to project root directory
cd /d "%~dp0"

echo ==========================================
echo       CDU System Launcher
echo       (New UI Version)
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
node --version >nul 2>&1
if %errorlevel% equ 0 goto :NodeFound

:: Check User's Common Path (C:\Users\sky.lo\node)
if exist "C:\Users\sky.lo\node\node.exe" (
    set "PATH=C:\Users\sky.lo\node;%PATH%"
    echo [CHECK] Found Node.js at C:\Users\sky.lo\node
    goto :NodeFound
)

:: Check if we already have a portable version in project bin
if exist "%~dp0bin\node\node.exe" (
    set "PATH=%~dp0bin\node;%PATH%"
    echo [CHECK] Portable Node.js found and added to PATH.
    goto :NodeFound
)

echo [INFO] Node.js is NOT installed or not in PATH.
echo.
echo ========================================================
echo  Node.js is required to run the Frontend.
echo  I can download a portable version (v20.11.0) for you.
echo  This will be saved to "%~dp0bin\node" and used locally.
echo ========================================================
echo.
set /p "AskInstall=Do you want to auto-download Node.js now? (Y/N): "
if /i "%AskInstall%" neq "Y" (
    echo.
    echo [ERROR] Cannot proceed without Node.js.
    echo Please install it manually from https://nodejs.org/
    pause
    exit /b
)

echo.
echo [STEP 0/4] Downloading Node.js Portable (This may take a minute)...
if not exist "bin" mkdir "bin"

:: Download using PowerShell
powershell -Command "Invoke-WebRequest -Uri 'https://nodejs.org/dist/v20.11.0/node-v20.11.0-win-x64.zip' -OutFile 'bin\node.zip'"

if not exist "bin\node.zip" (
    echo [ERROR] Download failed. Please check internet connection.
    pause
    exit /b
)

echo [STEP 0/4] Extracting Node.js...
powershell -Command "Expand-Archive -Path 'bin\node.zip' -DestinationPath 'bin' -Force"

:: Rename folder (It extracts as node-v20.11.0-win-x64, we want it as 'bin\node')
cd bin
rem Rename the extracted folder to 'node'
for /d %%D in (node-v*) do (
    move "%%D" "node"
)
cd ..

:: Clean up zip
del "bin\node.zip"

:: Add to PATH
set "PATH=%~dp0bin\node;%PATH%"
echo [CHECK] Node.js installed successfully!
node --version

:NodeFound
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
if exist "webUI\requirements.txt" (
    echo    Installing WebUI requirements...
    pip install -r webUI\requirements.txt
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
echo [STEP 3/4] Starting Backend (Port 5501)...
:: Start Backend in a new minimized window
:: Using webUI as working directory for app.py
start "CDU Backend (Port 5501)" /min cmd /k "call windows_venv\Scripts\activate && cd webUI && python web\app.py"

echo    Backend launching... waiting 5 seconds...
timeout /t 5 >nul

echo.
echo [STEP 4/4] Starting Vue Frontend (Port 5173)...
echo    The system should open automatically in your browser.
echo.

:: Start Frontend
cd webUI\frontend
start "CDU Frontend" cmd /k "npm run dev"

:: Wait for Vite to start (approx 5-8 seconds)
echo    Waiting for Frontend to initialize...
timeout /t 8 >nul

:: Explicitly open the New UI in default browser
echo    Opening New UI (http://localhost:5173)...
start http://localhost:5173

echo ==========================================
echo       System Launch Initiated!
echo ==========================================
echo.
echo [IMPORTANT]
echo The system is now running.
echo - Backend (API): http://localhost:5501
echo - Frontend (UI): http://localhost:5173  <-- PLEASE USE THIS ONE
echo.
echo NOTE: Do not close the terminal windows.
echo To stop the system, close the terminal windows.
echo.
pause
