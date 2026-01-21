# BlueSpace Restaurants Mobile App

React Native mobile application for BlueSpace Restaurants management system.

## Features

- **Restaurant Management**: Dashboard, orders, menu management, analytics
- **Order Tracking**: Real-time order status updates
- **Menu Management**: Add, edit, delete menu items and categories
- **Payment Processing**: Handle payments and confirmations
- **Analytics**: View revenue and order statistics
- **Customer Interface**: Browse menus, place orders, track delivery

## Prerequisites

- Node.js 18+ and npm
- Expo CLI: `npm install -g expo-cli`
- iOS: Xcode (for iOS development)
- Android: Android Studio (for Android development)

## Installation

```bash
# Install dependencies
npm install

# Start Expo development server
npm start
```

## Running the App

### iOS
```bash
npm run ios
```

### Android
```bash
npm run android
```

### Web (for testing)
```bash
npm run web
```

## Configuration

Update `app.json` to configure:
- API endpoint URL
- App name and branding
- Bundle identifiers

## Project Structure

```
mobile-app/
├── src/
│   ├── screens/          # Screen components
│   │   ├── auth/        # Authentication screens
│   │   ├── restaurant/  # Restaurant management screens
│   │   └── customer/    # Customer-facing screens
│   ├── services/        # API services
│   ├── context/         # React Context providers
│   └── components/      # Reusable components
├── App.js               # Main app component
├── app.json            # Expo configuration
└── package.json        # Dependencies
```

## API Integration

The app connects to the Flask backend API at `/api/v1/`. 

### Authentication
- JWT tokens stored securely using `expo-secure-store`
- Automatic token refresh
- Logout clears tokens

### API Endpoints Used
- `/api/v1/auth/*` - Authentication
- `/api/v1/orders/*` - Order management
- `/api/v1/menu/*` - Menu management
- `/api/v1/payments/*` - Payment processing
- `/api/v1/analytics/*` - Analytics data

## Building for Production

### iOS
```bash
eas build --platform ios --profile production
```

### Android
```bash
eas build --platform android --profile production
```

## Development Workflow

1. **Feature Development**
   - Create feature branch
   - Develop and test locally
   - Submit pull request

2. **Testing**
   - Test on iOS and Android
   - Verify API integration
   - Check error handling

3. **Deployment**
   - Merge to main branch
   - Build production app
   - Submit to app stores

## Troubleshooting

### Common Issues

1. **API Connection Errors**
   - Check API URL in `app.json`
   - Verify backend is running
   - Check network connectivity

2. **Build Errors**
   - Clear cache: `expo start -c`
   - Reinstall dependencies: `rm -rf node_modules && npm install`
   - Check Node.js version

3. **Token Issues**
   - Clear secure store
   - Re-login
   - Check token expiration

## Support

For issues or questions, refer to the main project documentation or create an issue in the repository.

