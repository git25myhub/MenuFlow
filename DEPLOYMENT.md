# BlueSpace Restaurants - Deployment Guide

## Modern App Architecture

This project uses a **modern API-first architecture** with:
- **Backend**: Flask REST API (Python)
- **Mobile App**: React Native (iOS & Android)
- **Web App**: Existing Flask templates (maintained for backward compatibility)

## Environment Setup

### Development Environment

1. **Backend Setup**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export FLASK_ENV=development
export DATABASE_URL=postgresql://user:password@localhost/bluespace_dev
export SECRET_KEY=your-dev-secret-key
export JWT_SECRET=your-jwt-secret-key

# Run migrations
flask db upgrade

# Start development server
flask run
```

2. **Mobile App Setup**
```bash
cd mobile-app

# Install dependencies
npm install

# Start Expo development server
npm start

# Run on iOS simulator
npm run ios

# Run on Android emulator
npm run android
```

### Staging Environment

1. **Backend (Render.com)**
   - Create a new Web Service on Render
   - Set environment: `FLASK_ENV=staging`
   - Use staging database
   - Set CORS_ORIGINS to staging app URL

2. **Mobile App**
   - Update `app.json` with staging API URL
   - Build staging APK/IPA for testing

### Production Environment

1. **Backend (Render.com)**
   - Use existing production service
   - Ensure API routes are accessible
   - Set proper CORS origins
   - Enable SSL/TLS

2. **Mobile App**
   - Build production APK/IPA
   - Submit to App Store / Google Play
   - Update API URL to production

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/register` - Register
- `GET /api/v1/auth/me` - Get current user
- `POST /api/v1/auth/logout` - Logout

### Orders
- `GET /api/v1/orders` - List orders
- `GET /api/v1/orders/<id>` - Get order details
- `POST /api/v1/orders` - Create order
- `PUT /api/v1/orders/<id>/status` - Update order status
- `DELETE /api/v1/orders/<id>` - Cancel order

### Menu
- `GET /api/v1/menu/items` - List menu items
- `GET /api/v1/menu/items/<id>` - Get menu item
- `POST /api/v1/menu/items` - Create menu item
- `PUT /api/v1/menu/items/<id>` - Update menu item
- `DELETE /api/v1/menu/items/<id>` - Delete menu item
- `GET /api/v1/menu/categories` - List categories

### Payments
- `POST /api/v1/payments/process` - Process payment
- `POST /api/v1/payments/confirm/<order_id>` - Confirm payment
- `GET /api/v1/payments/status/<order_id>` - Get payment status

### Analytics
- `GET /api/v1/analytics/dashboard` - Dashboard stats
- `GET /api/v1/analytics/revenue` - Revenue stats

## Continuous Development Workflow

### 1. Feature Development

```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes
# Test locally

# Commit and push
git commit -m "Add new feature"
git push origin feature/new-feature

# Create pull request to develop branch
```

### 2. Testing

- **Backend**: Run `pytest` before committing
- **Mobile**: Test on iOS and Android simulators
- **Integration**: Test API endpoints with Postman/Insomnia

### 3. Staging Deployment

```bash
# Merge to develop branch
git checkout develop
git merge feature/new-feature

# Push to trigger staging deployment
git push origin develop
```

### 4. Production Deployment

```bash
# Merge to main branch
git checkout main
git merge develop

# Push to trigger production deployment
git push origin main
```

## Mobile App Build Process

### iOS Build

```bash
cd mobile-app

# Install iOS dependencies
cd ios
pod install
cd ..

# Build for App Store
eas build --platform ios --profile production
```

### Android Build

```bash
cd mobile-app

# Build APK
eas build --platform android --profile production

# Or build locally
cd android
./gradlew assembleRelease
```

## Database Migrations

```bash
# Create migration
flask db migrate -m "Description"

# Review migration
# Edit migration file if needed

# Apply migration
flask db upgrade

# Rollback if needed
flask db downgrade
```

## Monitoring & Maintenance

### Backend Monitoring
- Check Render.com logs
- Monitor API response times
- Track error rates
- Database connection pool status

### Mobile App Monitoring
- Use Expo Analytics
- Track crash reports
- Monitor API call failures
- User feedback

## Version Management

### API Versioning
- Current version: `/api/v1/`
- Future versions: `/api/v2/`, `/api/v3/`, etc.
- Maintain backward compatibility when possible

### Mobile App Versioning
- Update version in `app.json`
- Follow semantic versioning (MAJOR.MINOR.PATCH)
- Update App Store / Play Store listings

## Security Best Practices

1. **API Security**
   - Use HTTPS in production
   - Validate all inputs
   - Rate limiting
   - JWT token expiration
   - CORS configuration

2. **Mobile App Security**
   - Store tokens securely (expo-secure-store)
   - Validate API responses
   - Handle errors gracefully
   - No hardcoded secrets

3. **Database Security**
   - Use connection pooling
   - Parameterized queries (SQLAlchemy handles this)
   - Regular backups
   - Access control

## Troubleshooting

### API Issues
- Check CORS configuration
- Verify JWT token expiration
- Check database connectivity
- Review error logs

### Mobile App Issues
- Clear cache: `expo start -c`
- Reinstall dependencies: `rm -rf node_modules && npm install`
- Check API URL configuration
- Review network requests in debugger

### Deployment Issues
- Check environment variables
- Verify database migrations
- Review build logs
- Check service status on Render

## Support

For issues or questions:
1. Check logs
2. Review this documentation
3. Create an issue in the repository
4. Contact the development team

