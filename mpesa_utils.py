import requests
import base64
from datetime import datetime
import os
from models import DarajaCredentials, PlatformSettings

def get_mpesa_access_token(credentials):
    """Get M-Pesa access token using restaurant-specific credentials"""
    base_url = "https://api.safaricom.co.ke" if credentials.environment == 'production' else "https://sandbox.safaricom.co.ke"
    auth_url = f"{base_url}/oauth/v1/generate?grant_type=client_credentials"
    response = requests.get(auth_url, auth=(credentials.consumer_key, credentials.consumer_secret))
    return response.json().get('access_token')

def get_password(credentials):
    """Generate password using restaurant-specific credentials"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    data_to_encode = credentials.shortcode + credentials.passkey + timestamp
    return base64.b64encode(data_to_encode.encode()).decode('utf-8'), timestamp

def get_callback_url(environment):
    settings = PlatformSettings.query.first()
    if environment == 'production':
        return settings.callback_url_production
    else:
        return settings.callback_url_sandbox

def stk_push(phone, amount, account_reference, transaction_desc, credentials):
    """Initiate STK push using restaurant-specific credentials"""
    access_token = get_mpesa_access_token(credentials)
    password, timestamp = get_password(credentials)
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Determine the API URL based on environment
    base_url = "https://api.safaricom.co.ke" if credentials.environment == 'production' else "https://sandbox.safaricom.co.ke"
    
    callback_url = get_callback_url(credentials.environment)
    
    payload = {
        "BusinessShortCode": credentials.shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone,
        "PartyB": credentials.shortcode,
        "PhoneNumber": phone,
        "CallBackURL": callback_url,
        "AccountReference": account_reference,
        "TransactionDesc": transaction_desc
    }
    
    url = f"{base_url}/mpesa/stkpush/v1/processrequest"
    response = requests.post(url, json=payload, headers=headers)
    return response.json()

def test_credentials(credentials):
    """Test if the provided Daraja credentials are valid"""
    try:
        access_token = get_mpesa_access_token(credentials)
        if access_token:
            return True, "Credentials are valid"
        return False, "Failed to get access token"
    except Exception as e:
        return False, str(e) 