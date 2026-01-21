# BlueSpace Restaurants - App Development Guide

## Overview

This guide explains how to maintain and develop the BlueSpace Restaurants app while keeping it in production.

## Architecture

### Backend (Flask API)
- **Location**: Root directory
- **API Routes**: `/api/v1/*`
- **Web Routes**: Existing templates (maintained for backward compatibility)
- **Database**: PostgreSQL with Alembic migrations

### Mobile App (React Native)
- **Location**: `mobile-app/` directory
- **Framework**: React Native with Expo
- **Navigation**: React Navigation
- **State Management**: React Context API

## Development Workflow

### 1. Local Development

#### Backend
```bash
# Activate virtual environment
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export FLASK_ENV=development
export DATABASE_URL=postgresql://localhost/bluespace_dev

# Run migrations
flask db upgrade

# Start server
flask run
```

#### Mobile App
```bash
cd mobile-app

# Install dependencies
npm install

# Start Expo
npm start

# Run on device/simulator
npm run ios  # or npm run android
```

### 2. Feature Development

#### Adding New API Endpoints

1. **Create endpoint in appropriate API module**
   ```python
   # api/new_feature.py
   from api import api_bp
   from api.auth import require_auth
   
   @api_bp.route('/new-feature', methods=['GET'])
   @require_auth
   def get_new_feature():
       # Implementation
       return jsonify({'success': True})
   ```

2. **Import in `api/__init__.py`**
   ```python
   from api import new_feature
   ```

3. **Test endpoint**
   ```bash
   curl -H "Authorization: Bearer <token>" http://localhost:5000/api/v1/new-feature
   ```

#### Adding New Mobile Screens

1. **Create screen component**
   ```javascript
   // mobile-app/src/screens/restaurant/NewScreen.js
   import React from 'react';
   import { View, Text } from 'react-native';
   
   export default function NewScreen() {
     return (
       <View>
         <Text>New Screen</Text>
       </View>
     );
   }
   ```

2. **Add to navigation**
   ```javascript
   // App.js
   import NewScreen from './src/screens/restaurant/NewScreen';
   
   // Add to Stack.Navigator
   <Stack.Screen name="NewScreen" component={NewScreen} />
   ```

### 3. Database Changes

1. **Create migration**
   ```bash
   flask db migrate -m "Add new table"
   ```

2. **Review migration file** in `migrations/versions/`

3. **Test migration**
   ```bash
   flask db upgrade
   ```

4. **Rollback if needed**
   ```bash
   flask db downgrade
   ```

### 4. Testing

#### Backend Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test
pytest tests/test_orders.py
```

#### Mobile App Tests
```bash
cd mobile-app
npm test
```

### 5. Staging Deployment

1. **Merge to develop branch**
   ```bash
   git checkout develop
   git merge feature/new-feature
   git push origin develop
   ```

2. **Staging auto-deploys** (if CI/CD is configured)

3. **Test on staging environment**

### 6. Production Deployment

1. **Merge to main branch**
   ```bash
   git checkout main
   git merge develop
   git push origin main
   ```

2. **Production auto-deploys** (if CI/CD is configured)

3. **Monitor deployment**

## Maintaining Production While Developing

### Best Practices

1. **Use Feature Flags**
   - Deploy code without enabling features
   - Enable features gradually
   - Rollback easily if issues occur

2. **Database Migrations**
   - Always test migrations on staging first
   - Use backward-compatible migrations when possible
   - Have rollback plan ready

3. **API Versioning**
   - Keep `/api/v1/` stable
   - Add new features in `/api/v2/` if breaking changes
   - Deprecate old versions gradually

4. **Mobile App Updates**
   - Test on staging API first
   - Use over-the-air updates (Expo) for non-native changes
   - Submit app store updates for native changes

5. **Monitoring**
   - Monitor error rates
   - Track API response times
   - Watch database performance
   - Monitor mobile app crashes

### Version Control Strategy

```
main (production)
  └── develop (staging)
      └── feature/new-feature
      └── feature/another-feature
```

**Workflow:**
1. Create feature branch from `develop`
2. Develop and test locally
3. Merge to `develop` for staging
4. Test on staging
5. Merge to `main` for production

### Environment Variables

#### Development
```env
FLASK_ENV=development
DATABASE_URL=postgresql://localhost/bluespace_dev
SECRET_KEY=dev-secret-key
JWT_SECRET=dev-jwt-secret
CORS_ORIGINS=http://localhost:3000,http://localhost:19006
```

#### Staging
```env
FLASK_ENV=staging
DATABASE_URL=postgresql://staging-db-url
SECRET_KEY=staging-secret-key
JWT_SECRET=staging-jwt-secret
CORS_ORIGINS=https://staging.bluespace-restaurants.com
```

#### Production
```env
FLASK_ENV=production
DATABASE_URL=postgresql://production-db-url
SECRET_KEY=production-secret-key
JWT_SECRET=production-jwt-secret
CORS_ORIGINS=https://bluespace-restaurants.onrender.com
```

## Adding New Features

### Example: Adding Push Notifications

1. **Backend: Add notification endpoint**
   ```python
   # api/notifications.py
   @api_bp.route('/notifications/register', methods=['POST'])
   @require_auth
   def register_device():
       # Save device token
       return jsonify({'success': True})
   ```

2. **Mobile: Add notification service**
   ```javascript
   // mobile-app/src/services/notifications.js
   import * as Notifications from 'expo-notifications';
   
   export const registerForNotifications = async () => {
     // Register device
   };
   ```

3. **Test locally**
4. **Deploy to staging**
5. **Deploy to production**

## Troubleshooting

### API Issues
- Check CORS configuration
- Verify JWT token handling
- Review database connections
- Check error logs

### Mobile App Issues
- Clear Expo cache: `expo start -c`
- Reinstall dependencies
- Check API URL configuration
- Review network requests

### Database Issues
- Check connection pool settings
- Review slow queries
- Monitor database size
- Check migration status

## Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [React Native Documentation](https://reactnative.dev/)
- [Expo Documentation](https://docs.expo.dev/)
- [API Documentation](./DEPLOYMENT.md#api-endpoints)

## Support

For questions or issues:
1. Check logs
2. Review documentation
3. Create an issue in the repository
4. Contact the development team

