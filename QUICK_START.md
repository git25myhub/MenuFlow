# 🚀 Quick Start Guide

Get your BlueSpace Restaurants app running in 5 minutes!

## Prerequisites Check

- [ ] Node.js 18+ installed (`node --version`)
- [ ] Python 3.9+ installed (`python --version`)
- [ ] PostgreSQL database running
- [ ] Git installed

## Step-by-Step Setup

### 1️⃣ Backend Setup (2 minutes)

```bash
# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies (if not already done)
pip install -r requirements.txt

# Create .env file
copy .env.example .env
# Or manually create .env with your database URL

# Update .env with your database connection
# DATABASE_URL=postgresql://user:pass@localhost/bluespace

# Run migrations
flask db upgrade

# Start server
python app.py
```

✅ Backend should be running on http://localhost:5000

### 2️⃣ Mobile App Setup (3 minutes)

```bash
# Navigate to mobile app directory
cd mobile-app

# Install dependencies (first time only, takes ~5 minutes)
npm install

# Start Expo
npm start
```

**Choose how to run:**
- **Physical Device**: Install "Expo Go" app, scan QR code
- **iOS Simulator**: Press `i` in terminal (Mac only)
- **Android Emulator**: Press `a` in terminal (requires Android Studio)

### 3️⃣ Test Connection

1. **Backend Test**
   ```bash
   curl http://localhost:5000/api/v1/menu/categories?restaurant_id=1
   ```

2. **Mobile App Test**
   - Open app
   - Try login with existing credentials
   - Should connect to backend

## 🎉 You're Ready!

- ✅ Backend running on port 5000
- ✅ Mobile app running via Expo
- ✅ API endpoints accessible
- ✅ Ready to develop!

## Next Steps

1. **Read Development Guide**: `APP_DEVELOPMENT_GUIDE.md`
2. **Configure Environments**: See `SETUP_GUIDE.md` Step 2
3. **Start Building**: Create your first feature!

## Common Issues

**"Port 5000 already in use"**
```bash
# Kill process or use different port
flask run --port 5001
```

**"Cannot connect to API from mobile"**
- Check backend is running
- Verify CORS_ORIGINS in .env includes your IP
- Update API_URL in mobile-app/app.json

**"npm install fails"**
```bash
# Clear cache and retry
rm -rf node_modules package-lock.json
npm install
```

## Need Help?

- Check `SETUP_GUIDE.md` for detailed instructions
- Review `APP_DEVELOPMENT_GUIDE.md` for workflow
- Check logs for error messages

Happy coding! 🎊

