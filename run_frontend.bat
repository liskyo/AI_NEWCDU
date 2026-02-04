@echo off
setlocal

:: Add Node.js to PATH specifically for this session
set "PATH=C:\Users\sky.lo\node;%PATH%"

echo [INFO] Starting CDU Frontend (Vue.js)...
cd webUI\frontend

:: Check if node_modules exists, install if not
if not exist "node_modules" (
    echo [INFO] Installing dependencies...
    call npm install
)

:: Start the dev server
echo [INFO] Launching Vite Dev Server...
call npm run dev

endlocal
pause
