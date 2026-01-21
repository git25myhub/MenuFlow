# BlueSpace Restaurants Mobile App - Deployment Guide

This guide will help you build and deploy a production-ready app that can be installed on real devices.

## Prerequisites

1. **Expo Account** (free)
   - Sign up at [expo.dev](https://expo.dev)
   - Free tier includes unlimited builds

2. **Node.js 20+** (you already have this ✅)

3. **EAS CLI** (we'll install this)

## Step 1: Install EAS CLI

```powershell
npm install -g eas-cli
```

Verify installation:
```powershell
eas --version
```

## Step 2: Login to Expo

```powershell
eas login
```

This will open a browser window. Sign in with your Expo account (or create one if you don't have it).

## Step 3: Link Project to Expo

```powershell
cd "C:\ReactProjects\BlueSpace Restaurants\mobile-app"
eas build:configure
```

This will:
- Create an Expo project if needed
- Generate a project ID in `app.json`
- Set up the build configuration

## Step 4: Update Production API URL (If Needed)

If your backend is deployed at a different URL, update `app.json`:

```json
"extra": {
  "apiUrl": "https://your-production-api.com/api/v1"
}
```

**Note**: The app is already configured to use `https://bluespace-restaurants.onrender.com/api/v1` in production.

## Step 5: Build for Android (APK - Easy Distribution)

### Option A: Build APK for Direct Installation

```powershell
npm run build:android:preview
```

Or:
```powershell
eas build --platform android --profile preview
```

This creates an **APK file** that can be:
- Downloaded directly to Android devices
- Shared via email, cloud storage, or web link
- Installed without Google Play Store

**Build Time**: ~15-20 minutes (first time)

### Option B: Build Production AAB for Google Play Store

```powershell
npm run build:android
```

Or:
```powershell
eas build --platform android --profile production
```

This creates an **AAB (Android App Bundle)** file required for Google Play Store submission.

## Step 6: Build for iOS

### For Testing (Ad Hoc Distribution)

```powershell
npm run build:ios:preview
```

**Requirements**:
- Apple Developer Account ($99/year)
- Need to configure certificates (EAS will guide you)

### For App Store Submission

```powershell
npm run build:ios
```

**Requirements**:
- Apple Developer Account ($99/year)
- App Store Connect app configured

## Step 7: Download and Install Your Build

### After Build Completes

1. **Check Build Status**:
   ```powershell
   eas build:list
   ```

2. **Download the Build**:
   - Visit [expo.dev](https://expo.dev/accounts/[your-username]/projects/bluespace-restaurants/builds)
   - Click on your build
   - Download the APK (Android) or IPA (iOS)

### Installing on Android

**Method 1: Direct Download**
1. Download the APK to your Android device
2. Open the file
3. Allow "Install from Unknown Sources" if prompted
4. Tap Install

**Method 2: QR Code**
- EAS provides a QR code after build completes
- Scan with your Android device to download directly

### Installing on iOS

**For Testing:**
1. Download the IPA file
2. Install via TestFlight (recommended)
3. Or use Apple Configurator for direct installation

## Step 8: Share Your App

### Android APK Distribution

**Easy Methods:**

1. **Expo Updates Dashboard**:
   - After build, EAS provides a shareable link
   - Users can download directly from the link

2. **Google Drive / Dropbox**:
   - Upload APK to cloud storage
   - Share the link
   - Users download and install

3. **Your Own Website**:
   - Host the APK on your server
   - Create a download page

4. **Email**:
   - Attach APK and send
   - Note: Some email providers block APK files

### QR Code Distribution

After build completes, you'll get a QR code. Users can:
1. Scan QR code with phone
2. Download APK directly
3. Install the app

## Step 9: Submit to App Stores (Optional)

### Google Play Store

1. **Create Google Play Console Account** ($25 one-time fee)
2. **Create App Listing**:
   ```powershell
   eas submit --platform android
   ```
3. Fill out store listing information
4. Submit for review

### Apple App Store

1. **Create App Store Connect App**
2. **Submit Build**:
   ```powershell
   eas submit --platform ios
   ```
3. Fill out store listing
4. Submit for review

## Quick Reference Commands

```powershell
# Build Android APK (for direct installation)
npm run build:android:preview

# Build Android AAB (for Play Store)
npm run build:android

# Build iOS (requires Apple Developer account)
npm run build:ios

# Check build status
eas build:list

# View build logs
eas build:view [BUILD_ID]

# Cancel a build
eas build:cancel [BUILD_ID]
```

## Build Profiles Explained

### Development Profile
- For testing with Expo Go
- Fast builds
- Includes development tools

### Preview Profile
- For testing on real devices
- APK/IPA format
- No app store required
- Perfect for beta testing

### Production Profile
- For app store submission
- Optimized and minified
- AAB format for Android
- IPA format for iOS

## Troubleshooting

### Build Fails

1. **Check Logs**:
   ```powershell
   eas build:view [BUILD_ID]
   ```

2. **Common Issues**:
   - Missing environment variables
   - Invalid app.json configuration
   - Dependency conflicts

3. **Clear Cache and Retry**:
   ```powershell
   eas build --platform android --profile preview --clear-cache
   ```

### Android Installation Issues

- **"App not installed"**: Check device architecture (arm64-v8a)
- **"Unknown sources"**: Enable in Android settings
- **Corrupt download**: Re-download the APK

### iOS Installation Issues

- **"Untrusted Developer"**: Go to Settings > General > Device Management > Trust
- **Certificate Issues**: Re-run `eas build:configure`

## Updating Your App

### After Making Changes

1. **Update Version** in `app.json`:
   ```json
   "version": "1.0.1"
   ```

2. **Rebuild**:
   ```powershell
   npm run build:android:preview
   ```

3. **Distribute New Version**:
   - Share new APK/IPA
   - Or use Over-The-Air (OTA) updates (see below)

### Over-The-Air (OTA) Updates

For small updates (JavaScript/asset changes only):

```powershell
eas update --branch production --message "Bug fixes"
```

Users will get the update automatically on next app launch (no rebuild needed).

## Cost Information

- **Expo Free Tier**: Unlimited builds ✅
- **Google Play**: $25 one-time fee (if submitting to store)
- **Apple Developer**: $99/year (required for iOS builds)

## Next Steps

1. ✅ Install EAS CLI
2. ✅ Login to Expo
3. ✅ Configure project
4. ✅ Build APK for testing
5. ✅ Share with beta testers
6. ✅ Submit to app stores (optional)

## Support

- **Expo Docs**: https://docs.expo.dev/build/introduction/
- **EAS Build Docs**: https://docs.expo.dev/build/introduction/
- **Expo Discord**: https://chat.expo.dev/

## Important Notes

⚠️ **Production API**: Make sure your backend is deployed and accessible at the URL in `app.json`

⚠️ **App Icons**: Add proper app icons and splash screens before production builds:
- `assets/icon.png` (1024x1024)
- `assets/splash.png` (1242x2436)
- `assets/adaptive-icon.png` (Android)

⚠️ **Testing**: Always test the production build before distributing to users!

