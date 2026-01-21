# Expo SDK 54 Upgrade Instructions

## Current Situation

You've upgraded to Expo SDK 54, which requires:
- **Node.js >= 20.19.4** (you're currently on 18.18.2)
- Updated dependencies including React 19 and React Native 0.81.5

## Step-by-Step Fix

### Step 1: Upgrade Node.js to Version 20 LTS

**If using nvm (Node Version Manager):**

```powershell
# Install Node.js 20 LTS (if not already installed)
nvm install 20.18.0

# Switch to Node.js 20
nvm use 20.18.0

# Verify
node -v
# Should show: v20.18.0 or higher
```

**If you don't have nvm:**

1. Download Node.js 20 LTS from [nodejs.org](https://nodejs.org/)
2. Install it (this will replace your current Node version)
3. Verify: `node -v` should show v20.x.x

### Step 2: Clean Install Dependencies

```powershell
# Navigate to mobile-app directory
cd "C:\ReactProjects\BlueSpace Restaurants\mobile-app"

# Remove existing dependencies
rmdir /s /q node_modules
del package-lock.json

# Clear npm cache
npm cache clean --force

# Install with legacy peer deps to resolve conflicts
npm install --legacy-peer-deps
```

### Step 3: Fix Remaining Package Versions

```powershell
# This will update all packages to SDK 54 compatible versions
npx expo install --fix --legacy-peer-deps
```

### Step 4: Start the App

```powershell
# Clear Expo cache and start
rmdir /s /q .expo
npm start
```

## What Was Fixed

1. ✅ Updated `.nvmrc` to Node.js 20.18.0
2. ✅ Updated `@types/react` to ~19.1.10 to match React 19
3. ✅ Removed asset references from `app.json` (icon, splash image, etc.) - you can add these later

## Notes

- The `--legacy-peer-deps` flag is needed because React 19 and React Native 0.81.5 have peer dependency conflicts that npm's strict resolver flags, but they actually work together fine.
- You may see warnings about deprecated packages - these are generally safe to ignore for now.
- The missing assets (icon.png, splash.png) won't prevent the app from running, but you should add them later for production.

## If You Prefer to Stay on Expo SDK 50

If you'd rather not upgrade to SDK 54, you can:

1. Switch back to Node.js 18
2. Revert package.json to SDK 50 dependencies
3. Install the older Expo Go app for SDK 50

Let me know if you'd like help with this alternative approach.

