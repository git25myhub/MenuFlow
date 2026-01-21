@echo off
REM BlueSpace Restaurants - Mobile App Setup Script (Windows)
echo ========================================
echo BlueSpace Restaurants - Mobile App Setup
echo ========================================
echo.

REM Check if Node.js is installed
where node >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Node.js is not installed!
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

echo [1/3] Checking Node.js version...
node --version
echo.

echo [2/3] Navigating to mobile-app directory...
cd mobile-app
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] mobile-app directory not found!
    pause
    exit /b 1
)

echo [3/3] Installing dependencies...
echo This may take 5-10 minutes...
echo.
npm install

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] npm install failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Update mobile-app/app.json with your API URL
echo 2. Run: npm start
echo 3. Scan QR code with Expo Go app or press 'i' for iOS / 'a' for Android
echo.
pause

