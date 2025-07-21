#!/usr/bin/env python3
import os
import base64
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

client_id = os.getenv('FITBIT_CLIENT_ID')
client_secret = os.getenv('FITBIT_CLIENT_SECRET')
redirect_uri = "http://localhost:8080/callback"

# Authorization code from your callback URL
code = "c4392beb00a72427b84a2c73fba5c9ac71f4fa89"

print("🔄 Exchanging authorization code for access tokens...")

# Prepare Basic Auth header
auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

token_data = {
    'client_id': client_id,
    'grant_type': 'authorization_code',
    'redirect_uri': redirect_uri,
    'code': code
}

headers = {
    'Authorization': f'Basic {auth_header}',
    'Content-Type': 'application/x-www-form-urlencoded'
}

response = requests.post('https://api.fitbit.com/oauth2/token', 
                       data=token_data, headers=headers)

if response.status_code == 200:
    tokens = response.json()
    access_token = tokens['access_token']
    refresh_token = tokens['refresh_token']
    
    print("✅ Success! Got your tokens:")
    print(f"Access Token: {access_token[:20]}...")
    print(f"Refresh Token: {refresh_token[:20]}...")
    
    # Update .env file
    with open('.env', 'r') as f:
        content = f.read()
    
    content = content.replace('FITBIT_ACCESS_TOKEN=', f'FITBIT_ACCESS_TOKEN={access_token}')
    content = content.replace('FITBIT_REFRESH_TOKEN=', f'FITBIT_REFRESH_TOKEN={refresh_token}')
    
    with open('.env', 'w') as f:
        f.write(content)
        
    print("\n📝 Updated .env file with your tokens!")
    
else:
    print(f"❌ Error getting tokens: {response.status_code}")
    print(response.text)