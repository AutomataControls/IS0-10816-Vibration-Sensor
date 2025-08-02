@echo off
echo Updating AutomataNexus Vibration Package in Node-RED
echo ====================================================
echo.

cd /d %USERPROFILE%\.node-red

echo Current directory: %CD%
echo.

echo Updating to version 2.0.0...
call npm update node-red-contrib-automatanexus-hvac-vibration

echo.
echo Update complete! 
echo.
echo Restarting Node-RED...
call node-red-restart

echo.
echo Node-RED restarted. You should now see both nodes:
echo - HVAC Vibration Parser
echo - Industrial Vibration Parser
echo.
pause