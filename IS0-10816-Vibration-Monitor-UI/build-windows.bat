@echo off
REM AutomataNexus Vibration Monitor - Windows Build Script

echo ========================================================
echo  Building AutomataNexus Vibration Monitor
echo  Target: Windows x64
echo ========================================================
echo.

REM Check prerequisites
where cargo >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Rust not installed!
    pause
    exit /b 1
)

where npm >nul 2>nul  
if %errorlevel% neq 0 (
    echo ERROR: Node.js not installed!
    pause
    exit /b 1
)

REM Install dependencies
if not exist "node_modules" (
    echo Installing dependencies...
    npm install
)

echo.
echo Building production app...
echo This may take several minutes...
echo.

npm run build

echo.
echo ========================================================
echo  BUILD COMPLETE!
echo ========================================================
echo.
echo Installer location:
echo   src-tauri\target\release\bundle\msi\
echo.
echo Executable location:  
echo   src-tauri\target\release\AutomataNexus Vibration Monitor.exe
echo.
pause