# Fix Instructions for Node.js Compatibility Issue

## Problem
You're encountering an error because Node.js v24.11.1 is not compatible with Expo ~50.0.0. The error occurs when Metro tries to create directories with invalid names.

## Solution Steps

### Step 1: Switch to Node.js 18 (Recommended)

Since you have both Node v18.18.2 and v24.11.1 installed, you need to switch to Node 18:

**If using nvm (Node Version Manager):**
```bash
nvm use 18.18.2
```

**If using nvm-windows:**
```bash
nvm use 18.18.2
```

**Verify the switch:**
```bash
node -v
# Should show: v18.18.2
```

### Step 2: Clean Install

After switching to Node 18, clean and reinstall:

```bash
# Remove node_modules and package-lock.json
rmdir /s /q node_modules
del package-lock.json

# Clear npm cache
npm cache clean --force

# Reinstall dependencies
npm install
```

### Step 3: Clear Expo Cache

```bash
# Clear Expo cache
npx expo start -c
```

Or manually delete the `.expo` folder:
```bash
rmdir /s /q .expo
```

### Step 4: Start the App

```bash
npm start
```

## Alternative: If You Don't Have nvm

If you don't have nvm installed, you can:

1. **Download Node.js 18 LTS** from [nodejs.org](https://nodejs.org/)
2. Install it (this will replace your current Node version)
3. Follow steps 2-4 above

## Notes

- The `.nvmrc` file has been created to help nvm automatically use the correct version
- The deprecated `@types/react-native` package has been removed from package.json
- Metro and Babel config files have been created to ensure proper configuration

## Why This Happens

Node.js v24 is very new (released in 2024) and Expo 50 was released before it. The "node:sea" error occurs because Metro's external shim handling doesn't properly escape Node.js built-in module references in the newer Node version, creating invalid Windows directory names.

