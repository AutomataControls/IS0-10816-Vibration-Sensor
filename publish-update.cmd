@echo off
echo AutomataNexus Industrial Vibration Package v2.0.0 Publisher
echo ===========================================================
echo.

cd /d D:\opt\automatanexus-node-red-dev\node-red-contrib-automatanexus-hvac-vibration

echo Current directory: %CD%
echo.

echo Publishing version 2.0.0 to NPM...
npm publish

echo.
echo Published! Users can now update via Node-RED palette manager.
echo.
echo To update in your local Node-RED:
echo 1. Open Node-RED palette manager
echo 2. Go to "Nodes" tab
echo 3. Search for "automatanexus"
echo 4. Click "update" on the package
echo.
echo Or use command line:
echo   cd %%USERPROFILE%%\.node-red
echo   npm update node-red-contrib-automatanexus-hvac-vibration
echo.
pause