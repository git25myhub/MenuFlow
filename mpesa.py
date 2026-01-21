import requests
import base64
from datetime import datetime
import json
import os
from dotenv import load_dotenv

load_dotenv()

class MpesaAPI:
    def __init__(self):
        self.consumer_key = os.getenv('MPESA_CONSUMER_KEY')
        self.consumer_secret = os.getenv('MPESA_CONSUMER_SECRET')
        self.passkey = os.getenv('MPESA_PASSKEY')
        self.shortcode = os.getenv('MPESA_SHORTCODE')
        self.env = os.getenv('MPESA_ENV', 'sandbox')
        
        if self.env == 'sandbox':
            self.base_url = 'https://sandbox.safaricom.co.ke'
        else:
            self.base_url = 'https://api.safaricom.co.ke'
            
        print(f"[MPESA DEBUG] MpesaAPI initialized with env: {self.env}, base_url: {self.base_url}")

    def get_access_token(self):
        """Get M-Pesa access token"""
        auth = base64.b64encode(f"{self.consumer_key}:{self.consumer_secret}".encode()).decode()
        headers = {
            'Authorization': f'Basic {auth}'
        }
        response = requests.get(f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials", headers=headers)
        return response.json().get('access_token')

    def initiate_stk_push(self, phone_number, amount, account_reference, transaction_desc, receiving_account=None):
        """Initiate STK Push to customer's phone"""
        access_token = self.get_access_token()
        
        if not access_token:
            print("[MPESA DEBUG] Failed to get access token")
            return {'ResponseCode': '1', 'ResponseDescription': 'Failed to get access token'}

        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password = base64.b64encode(
            f"{self.shortcode}{self.passkey}{timestamp}".encode()
        ).decode()

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        target_shortcode = receiving_account if receiving_account else self.shortcode

        payload = {
            "BusinessShortCode": self.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone_number,
            "PartyB": target_shortcode,
            "PhoneNumber": phone_number,
            "CallBackURL": f"{os.getenv('BASE_URL')}/mpesa/callback",
            "AccountReference": account_reference,
            "TransactionDesc": transaction_desc
        }

        print(f"[MPESA DEBUG] STK Push Payload: {json.dumps(payload, indent=2)}")

        try:
            response = requests.post(
                f"{self.base_url}/mpesa/stkpush/v1/processrequest",
                headers=headers,
                json=payload
            )
            response_json = response.json()
            print(f"[MPESA DEBUG] STK Push Response: {json.dumps(response_json, indent=2)}")
            return response_json
        except requests.exceptions.RequestException as e:
            print(f"[MPESA DEBUG] STK Push Request Error: {e}")
            return {'ResponseCode': '1', 'ResponseDescription': f'Request Error: {e}'}

    def check_transaction_status(self, checkout_request_id):
        """Check the status of an STK Push transaction"""
        access_token = self.get_access_token()
        
        if not access_token:
            print("[MPESA DEBUG] Failed to get access token for status check")
            return {'ResponseCode': '1', 'ResponseDescription': 'Failed to get access token'}

        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password = base64.b64encode(
            f"{self.shortcode}{self.passkey}{timestamp}".encode()
        ).decode()

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        payload = {
            "BusinessShortCode": self.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "CheckoutRequestID": checkout_request_id
        }

        print(f"[MPESA DEBUG] Transaction Status Check Payload: {json.dumps(payload, indent=2)}")

        try:
            response = requests.post(
                f"{self.base_url}/mpesa/stkpushquery/v1/query",
                headers=headers,
                json=payload
            )
            response_json = response.json()
            print(f"[MPESA DEBUG] Transaction Status Check Response: {json.dumps(response_json, indent=2)}")
            return response_json
        except requests.exceptions.RequestException as e:
            print(f"[MPESA DEBUG] Transaction Status Check Request Error: {e}")
            return {'ResponseCode': '1', 'ResponseDescription': f'Request Error: {e}'} 