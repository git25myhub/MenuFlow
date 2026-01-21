# 📱 Step-by-Step Setup Guide

Follow these steps in order to get everything running.

## Step 1: Set Up Mobile App ⚡

### Option A: Automated Setup (Recommended)

**Windows:**
```bash
setup_mobile_app.bat
```

**Mac/Linux:**
```bash
chmod +x setup_mobile_app.sh
./setup_mobile_app.sh
```

### Option B: Manual Setup

1. **Navigate to mobile-app directory**
   ```bash
   cd mobile-app
   ```

2. **Install dependencies** (takes 5-10 minutes first time)
   ```bash
   npm install
   ```
   
   You should see:
   ```
   ✓ Dependencies installed
   ✓ Node modules ready
   ```

3. **Verify installation**
   ```bash
   npm --version
   node --version
   ```

## Step 2: Configure Environment Variables 🔧

### Backend Configuration

1. **Create `.env` file in root directory**
   ```bash
   # Windows
   copy .env.example .env
   
   # Mac/Linux
   cp .env.example .env
   ```

2. **Edit `.env` file** with your settings:
   ```env
   # Essential settings
   FLASK_ENV=development
   SECRET_KEY=your-secret-key-change-this
   JWT_SECRET=your-jwt-secret-change-this
   DATABASE_URL=postgresql://user:pass@localhost/bluespace
   
   # CORS - Add your local IP for mobile app
   # Find your IP: ipconfig (Windows) or ifconfig (Mac/Linux)
   CORS_ORIGINS=http://localhost:3000,http://localhost:19006,exp://192.168.1.100:8081
   ```

3. **Get your local IP address** (needed for mobile app)
   - **Windows**: Run `ipconfig` and look for "IPv4 Address"
   - **Mac/Linux**: Run `ifconfig` or `ip addr`
   - Add it to CORS_ORIGINS: `exp://YOUR_IP:8081`

### Mobile App Configuration

The mobile app is already configured to use:
- **Development**: `http://localhost:5000/api/v1` (when running locally)
- **Production**: `https://bluespace-restaurants.onrender.com/api/v1` (when built)

**To change API URL**, edit `mobile-app/app.json`:
```json
"extra": {
  "apiUrl": "http://YOUR_IP:5000/api/v1"  // Use your computer's IP for physical device
}
```

## Step 3: Start Everything 🚀

### Terminal 1: Backend Server

```bash
# Make sure you're in root directory
# Activate virtual environment
venv\Scripts\activate  # Windows
# OR
source venv/bin/activate  # Mac/Linux

# Start Flask server
python app.py
```

You should see:
```
 * Running on http://127.0.0.1:5000
 * Running on http://192.168.1.100:5000
```

✅ **Backend is running!**

### Terminal 2: Mobile App

```bash
# Navigate to mobile-app directory
cd mobile-app

# Start Expo
npm start
```

You should see:
```
Metro waiting on exp://192.168.1.100:8081
Scan the QR code above with Expo Go (Android) or the Camera app (iOS)
```

## Step 4: Run Mobile App on Device 📱

### Option A: Physical Device (Recommended for Testing)

1. **Install Expo Go** on your phone:
   - iOS: [App Store](https://apps.apple.com/app/expo-go/id982107779)
   - Android: [Google Play](https://play.google.com/store/apps/details?id=host.exp.exponent)

2. **Connect to same WiFi** as your computer

3. **Scan QR code** from terminal:
   - iOS: Use Camera app
   - Android: Use Expo Go app

4. **App should load** on your device!

### Option B: iOS Simulator (Mac only)

1. **Press `i`** in Expo terminal
2. Simulator will open automatically

### Option C: Android Emulator

1. **Start Android Studio** and launch an emulator
2. **Press `a`** in Expo terminal
3. App will install on emulator

## Step 5: Test the Connection ✅

### Test Backend API

Open browser or use curl:
```bash
# Test menu endpoint
curl http://localhost:5000/api/v1/menu/categories?restaurant_id=1

# Should return JSON response
```

### Test Mobile App

1. **Open app** on device/simulator
2. **Try to login** with existing credentials
3. **Check if data loads** (dashboard, orders, etc.)

### Troubleshooting Connection

**If mobile app can't connect:**

1. **Check backend is running**
   ```bash
   curl http://localhost:5000/api/v1/menu/categories?restaurant_id=1
   ```

2. **Verify IP address**
   - Make sure CORS_ORIGINS includes your IP
   - Update app.json with your IP if using physical device

3. **Check firewall**
   - Allow port 5000 in Windows Firewall
   - Or use `expo start --tunnel` for remote connection

4. **Try tunnel mode**
   ```bash
   cd mobile-app
   expo start --tunnel
   ```

## Step 6: Start Developing! 💻

### Development Workflow

1. **Make changes to backend** → Auto-reloads (if debug mode)
2. **Make changes to mobile app** → Press `r` in Expo terminal to reload
3. **Test on device** → Changes appear instantly

### Your First Feature

1. **Create feature branch**
   ```bash
   git checkout -b feature/my-first-feature
   ```

2. **Make changes**
   - Backend: Add API endpoint in `api/` directory
   - Mobile: Add screen in `mobile-app/src/screens/`

3. **Test locally**
   - Test API with curl or Postman
   - Test mobile app on device

4. **Commit and push**
   ```bash
   git add .
   git commit -m "Add my first feature"
   git push origin feature/my-first-feature
   ```

## Quick Reference Commands

### Backend
```bash
# Start server
python app.py

# Run migrations
flask db upgrade

# Create migration
flask db migrate -m "Description"
```

### Mobile App
```bash
# Start Expo
npm start

# Clear cache and restart
npm start -- --clear

# Run on specific platform
npm run ios      # iOS only
npm run android  # Android only
```

## Next Steps

1. ✅ Mobile app setup complete
2. ✅ Environments configured
3. 📖 Read `APP_DEVELOPMENT_GUIDE.md` for detailed workflow
4. 🎯 Start building features!

## Need Help?

- **Setup issues**: Check `SETUP_GUIDE.md`
- **Development workflow**: See `APP_DEVELOPMENT_GUIDE.md`
- **Quick reference**: See `QUICK_START.md`
- **API documentation**: See `DEPLOYMENT.md`

Happy coding! 🎉

