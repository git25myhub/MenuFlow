#!/bin/bash
# BlueSpace Restaurants - Mobile App Setup Script (Mac/Linux)

echo "========================================"
echo "BlueSpace Restaurants - Mobile App Setup"
echo "========================================"
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "[ERROR] Node.js is not installed!"
    echo "Please install Node.js from https://nodejs.org/"
    exit 1
fi

echo "[1/3] Checking Node.js version..."
node --version
echo ""

echo "[2/3] Navigating to mobile-app directory..."
cd mobile-app || exit 1

echo "[3/3] Installing dependencies..."
echo "This may take 5-10 minutes..."
echo ""
npm install

if [ $? -ne 0 ]; then
    echo "[ERROR] npm install failed!"
    exit 1
fi

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Update mobile-app/app.json with your API URL"
echo "2. Run: npm start"
echo "3. Scan QR code with Expo Go app or press 'i' for iOS / 'a' for Android"
echo ""

