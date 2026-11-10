@echo off
cd /d "%~dp0"
echo ========================================================
echo Starting Truffle Develop Ethereum Blockchain (Port 9545)
echo ========================================================
echo.
echo Once the truffle(develop)^> prompt appears, type:
echo   compile
echo   migrate --reset
echo.
npx truffle develop
pause

