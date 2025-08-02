@echo off
echo AutomataNexus Industrial Vibration Package Installer
echo ====================================================
echo.

REM Navigate to Node-RED directory
cd /d %USERPROFILE%\.node-red

echo Current directory: %CD%
echo.

REM Remove old version if exists
echo Removing old version...
call npm remove node-red-contrib-automatanexus-hvac-vibration

REM Install new version
echo.
echo Installing new version 2.0.0...
call npm install D:\opt\automatanexus-node-red-dev\node-red-contrib-automatanexus-hvac-vibration

echo.
echo Installation complete!
echo.
echo Please restart Node-RED to use the new nodes:
echo - HVAC Vibration Parser (original)
echo - Industrial Vibration Parser (new - supports 32 sensors)
echo.
pause