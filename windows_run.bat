@echo off
setlocal

:: Set title
title CDU System Launcher

:: Change to project root directory
cd /d "%~dp0"

echo ==========================================
echo       CDU System Launcher for Windows
echo ==========================================

:: check python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    pause
    exit /b
)

:: Create venv if not exists
if not exist "windows_venv" (
    echo [INFO] Creating virtual environment 'windows_venv'...
    python -m venv windows_venv
    
    echo [INFO] Activating virtual environment...
    call windows_venv\Scripts\activate
    
    echo [INFO] Installing dependencies...
    pip install --upgrade pip
    if exist "RestAPI\requirements.txt" (
        echo [INFO] Installing RestAPI requirements...
        pip install -r RestAPI\requirements.txt
    )
    if exist "webUI\requirements.txt" (
        echo [INFO] Installing WebUI requirements...
        pip install -r webUI\requirements.txt
    )
    if exist "PLC\requirements.txt" (
        echo [INFO] Installing PLC requirements...
        pip install -r PLC\requirements.txt
    )
) else (
    echo [INFO] Virtual environment found. Activating...
    call windows_venv\Scripts\activate
)

echo.
echo [INFO] Starting Services...
echo.

:: Start RestAPI
if exist "RestAPI\app.py" (
    echo [INFO] Launching RestAPI...
    start "CDU RestAPI (Port 5001)" cmd /k "cd RestAPI && ..\windows_venv\Scripts\python app.py"
) else (
    echo [WARN] RestAPI\app.py not found!
)

:: Start WebUI
if exist "webUI\web\app.py" (
    echo [INFO] Launching WebUI...
    start "CDU WebUI (Port 5501)" cmd /k "cd webUI && ..\windows_venv\Scripts\python web\app.py"
) else (
    echo [WARN] webUI\web\app.py not found!
)

:: Wait a bit for services to start
timeout /t 5 >nul

echo.
echo ==========================================
echo System Running!
echo ==========================================
echo RestAPI URL: http://localhost:5001
echo WebUI URL:   http://localhost:5501
echo.
echo To open the WebUI, open your browser to the URL above.
echo.
pause
