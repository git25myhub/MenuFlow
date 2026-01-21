"""
BlueSpace Restaurants API
Modern API-first architecture for mobile app support
"""
from flask import Blueprint

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

# Import all API routes
from api import auth, orders, menu, payments, restaurants, analytics

