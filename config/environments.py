"""
Environment configuration for different deployment stages
"""
import os
from datetime import timedelta


class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    JWT_SECRET = os.environ.get('JWT_SECRET', SECRET_KEY)
    JWT_ALGORITHM = 'HS256'
    JWT_EXPIRATION = 86400  # 24 hours
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://localhost/bluespace')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 300,
        'pool_pre_ping': True
    }
    
    # Flask
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)
    
    # CORS for API
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    
    # File uploads
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # Mail
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.example.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', '')
    
    # Cloudinary
    CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME')
    CLOUDINARY_API_KEY = os.environ.get('CLOUDINARY_API_KEY')
    CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET')
    
    # Hardware
    SIMULATION_MODE = os.environ.get('SIMULATION_MODE', 'false').lower() == 'true'


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    SQLALCHEMY_ECHO = False
    CORS_ORIGINS = ['http://localhost:3000', 'http://localhost:19006', '*']  # React Native Metro
    SESSION_COOKIE_SECURE = False  # Allow HTTP in development


class StagingConfig(Config):
    """Staging configuration"""
    DEBUG = False
    TESTING = False
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'https://staging.bluespace-restaurants.com').split(',')


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'https://bluespace-restaurants.onrender.com').split(',')
    SESSION_COOKIE_SECURE = True
    WTF_CSRF_ENABLED = True


# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'staging': StagingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

