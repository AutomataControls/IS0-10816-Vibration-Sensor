@echo off
echo Force Update AutomataNexus Vibration Package
echo ============================================
echo.

cd /d %USERPROFILE%\.node-red

echo Clearing NPM cache...
call npm cache clean --force

echo.
echo Removing old version...
call npm remove node-red-contrib-automatanexus-hvac-vibration

echo.
echo Installing version 2.0.0...
call npm install node-red-contrib-automatanexus-hvac-vibration@2.0.0

echo.
echo Restarting Node-RED...
call node-red-stop
timeout /t 3
call node-red-start

echo.
echo Force update complete!
echo Check Node-RED for the new Industrial Vibration Parser node.
echo.
pause