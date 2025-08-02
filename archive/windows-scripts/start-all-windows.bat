@echo off
REM Start both Python backend and Tauri frontend on Windows

echo ========================================================
echo  Starting AutomataNexus Vibration Monitor System
echo ========================================================
echo.

REM Check if Python backend is running
curl -s http://localhost:5000/api/status >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Backend already running
) else (
    echo Starting Python backend...
    
    REM Check if Python script exists
    if exist "universal_vibration_monitor.py" (
        REM Start Python in new window
        start "Vibration Monitor Backend" /min cmd /c python universal_vibration_monitor.py
        
        echo Waiting for backend to start...
        timeout /t 5 /nobreak >nul
        
        REM Check if backend started
        curl -s http://localhost:5000/api/status >nul 2>&1
        if %errorlevel% neq 0 (
            echo [ERROR] Backend failed to start!
            echo Check the Python console window for errors
            pause
            exit /b 1
        )
        echo [OK] Backend started successfully
    ) else (
        echo [ERROR] universal_vibration_monitor.py not found!
        echo Make sure you're in the sensor project directory
        pause
        exit /b 1
    )
)

echo.
echo Starting Tauri UI...
echo.

cd IS0-10816-Vibration-Monitor-UI
call npm run dev

REM When UI closes, offer to stop backend
echo.
echo UI closed. 
choice /C YN /M "Stop the backend server too"
if errorlevel 1 (
    taskkill /FI "WindowTitle eq Vibration Monitor Backend*" /T /F >nul 2>&1
    echo Backend stopped.
)

pause