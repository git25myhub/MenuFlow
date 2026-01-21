# BlueSpace Restaurants - Complete Setup Guide

## Step 1: Set Up Mobile App

### Prerequisites
- Node.js 18+ installed ([Download](https://nodejs.org/))
- npm (comes with Node.js)
- Expo CLI (will be installed automatically)

### Installation Steps

1. **Navigate to mobile-app directory**
   ```bash
   cd mobile-app
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```
   This will install all React Native and Expo dependencies (~5-10 minutes)

3. **Start Expo development server**
   ```bash
   npm start
   ```
   This will:
   - Start the Metro bundler
   - Show a QR code in terminal
   - Open Expo DevTools in browser

4. **Run on device/simulator**
   
   **Option A: Physical Device**
   - Install "Expo Go" app on your phone (iOS/Android)
   - Scan the QR code from terminal
   
   **Option B: iOS Simulator** (Mac only)
   ```bash
   npm run ios
   ```
   
   **Option C: Android Emulator**
   ```bash
   npm run android
   ```
   (Requires Android Studio and emulator setup)

## Step 2: Configure Environments

### Backend Environment Variables

Create a `.env` file in the root directory:

```bash
# Copy the example file
cp .env.example .env
```

Or create manually with these variables:

```env
# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-secret-key-here-change-in-production
JWT_SECRET=your-jwt-secret-key-here

# Database
DATABASE_URL=postgresql://username:password@localhost/bluespace_dev

# CORS (for mobile app)
CORS_ORIGINS=http://localhost:3000,http://localhost:19006,exp://192.168.1.x:8081

# Mail Configuration (optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com

# Hardware (optional, for Raspberry Pi)
SIMULATION_MODE=true

# Cloudinary (optional, for image uploads)
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
```

### Mobile App Configuration

Update `mobile-app/app.json` to set your API URL:

```json
{
  "expo": {
    "extra": {
      "apiUrl": "http://localhost:5000/api/v1"  // For local development
      // "apiUrl": "https://bluespace-restaurants.onrender.com/api/v1"  // For production
    }
  }
}
```

Or use environment variables in `mobile-app/.env`:
```env
API_URL=http://localhost:5000/api/v1
```

## Step 3: Test the Setup

### Test Backend API

1. **Start backend server**
   ```bash
   # In root directory
   python app.py
   ```

2. **Test API endpoint**
   ```bash
   curl http://localhost:5000/api/v1/menu/categories?restaurant_id=1
   ```

### Test Mobile App

1. **Start mobile app** (from mobile-app directory)
   ```bash
   npm start
   ```

2. **Test login**
   - Open app on device/simulator
   - Try logging in with existing credentials
   - Should connect to backend API

## Step 4: Development Workflow

### Daily Development

1. **Start Backend**
   ```bash
   # Terminal 1 - Backend
   python app.py
   ```

2. **Start Mobile App**
   ```bash
   # Terminal 2 - Mobile App
   cd mobile-app
   npm start
   ```

3. **Make Changes**
   - Backend: Changes auto-reload (if debug mode)
   - Mobile: Press `r` in Expo terminal to reload

### Adding New Features

See `APP_DEVELOPMENT_GUIDE.md` for detailed workflow:
- Feature branches
- Testing
- Staging deployment
- Production deployment

## Troubleshooting

### Mobile App Issues

**"Cannot connect to API"**
- Check backend is running on correct port
- Verify API_URL in app.json
- Check CORS_ORIGINS in .env includes your IP

**"Module not found"**
- Delete `node_modules` and `package-lock.json`
- Run `npm install` again

**"Expo Go not connecting"**
- Ensure phone and computer on same WiFi
- Check firewall settings
- Try `expo start --tunnel` for remote connection

### Backend Issues

**"Database connection error"**
- Check DATABASE_URL in .env
- Verify database is running
- Check database credentials

**"Port already in use"**
- Change port: `flask run --port 5001`
- Or kill process using port 5000

## Next Steps

1. ✅ Complete mobile app setup
2. ✅ Configure environments
3. 📖 Read `APP_DEVELOPMENT_GUIDE.md` for development workflow
4. 🚀 Start building features!

