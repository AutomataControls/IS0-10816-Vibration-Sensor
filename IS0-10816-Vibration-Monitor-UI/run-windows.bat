@echo off
REM AutomataNexus Vibration Monitor - Windows Launcher

echo ========================================================
echo  AutomataNexus Vibration Monitor Desktop App
echo  Professional Industrial Monitoring Suite
echo ========================================================
echo.

REM Check if npm is installed
where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Node.js/npm not found!
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

REM Check if cargo is installed
where cargo >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Rust not found!
    echo.
    echo Please install Rust:
    echo 1. Visit https://rustup.rs/
    echo 2. Download and run rustup-init.exe
    echo 3. Follow the installation instructions
    echo 4. Restart this script
    echo.
    pause
    exit /b 1
)

echo [OK] Prerequisites found
echo.

REM Install dependencies if needed
if not exist "node_modules" (
    echo Installing dependencies...
    npm install
)

REM Check backend
echo Checking backend API...
curl -s http://localhost:5000/api/status >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Backend API is running
) else (
    echo [WARNING] Backend API not responding at http://localhost:5000
    echo.
    echo To start the backend:
    echo 1. Open a new terminal
    echo 2. Navigate to your sensor project directory
    echo 3. Run: python universal_vibration_monitor.py
    echo.
    choice /C YN /M "Continue anyway"
    if errorlevel 2 exit /b 1
)

echo.
echo Starting desktop application...
echo ===============================
echo.

npm run dev

pause