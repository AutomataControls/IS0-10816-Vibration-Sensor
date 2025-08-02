@echo off
echo Updating to bug fix version 2.0.1
echo ==================================
echo.

cd /d %USERPROFILE%\.node-red

echo Updating to version 2.0.1...
call npm update node-red-contrib-automatanexus-hvac-vibration

echo.
echo Restarting Node-RED...
call node-red-restart

echo.
echo Update complete! The Industrial Vibration Parser should now work with your data.
echo.
pause