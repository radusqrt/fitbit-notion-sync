#!/usr/bin/env python3
"""
Refresh Fitbit token manually
"""

import os
import requests
import base64
from dotenv import load_dotenv

def refresh_fitbit_token():
    """Refresh Fitbit access token"""
    load_dotenv()
    
    client_id = os.getenv('FITBIT_CLIENT_ID')
    client_secret = os.getenv('FITBIT_CLIENT_SECRET')
    refresh_token = os.getenv('FITBIT_REFRESH_TOKEN')
    
    if not all([client_id, client_secret, refresh_token]):
        print("❌ Missing Fitbit credentials")
        return False
    
    print("🔄 Refreshing Fitbit token...")
    
    # Create Basic Auth header
    credentials = f"{client_id}:{client_secret}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    headers = {
        'Authorization': f'Basic {encoded_credentials}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }
    
    response = requests.post('https://api.fitbit.com/oauth2/token', data=data, headers=headers)
    
    if response.status_code == 200:
        tokens = response.json()
        new_access_token = tokens['access_token']
        new_refresh_token = tokens.get('refresh_token', refresh_token)
        
        print("✅ Token refreshed successfully!")
        
        # Update .env file
        with open('.env', 'r') as f:
            content = f.read()
        
        # Replace tokens
        content = content.replace(
            f'FITBIT_ACCESS_TOKEN={os.getenv("FITBIT_ACCESS_TOKEN")}',
            f'FITBIT_ACCESS_TOKEN={new_access_token}'
        )
        content = content.replace(
            f'FITBIT_REFRESH_TOKEN={os.getenv("FITBIT_REFRESH_TOKEN")}',
            f'FITBIT_REFRESH_TOKEN={new_refresh_token}'
        )
        
        with open('.env', 'w') as f:
            f.write(content)
        
        print("🔑 TOKENS UPDATED IN .env FILE")
        print()
        print("📋 UPDATE THESE GITHUB SECRETS:")
        print(f"FITBIT_ACCESS_TOKEN={new_access_token}")
        print(f"FITBIT_REFRESH_TOKEN={new_refresh_token}")
        
        return True
    else:
        print(f"❌ Failed to refresh token: {response.text}")
        return False

if __name__ == "__main__":
    refresh_fitbit_token()