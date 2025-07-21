#!/usr/bin/env python3
"""
One-time OAuth helper to get your Fitbit access tokens.
Run this script once to authorize your app and get tokens.
"""

import os
import base64
import webbrowser
import requests
from urllib.parse import parse_qs, urlparse
from dotenv import load_dotenv

def get_fitbit_tokens():
    # Load environment variables
    load_dotenv()
    
    client_id = os.getenv('FITBIT_CLIENT_ID')
    client_secret = os.getenv('FITBIT_CLIENT_SECRET')
    redirect_uri = "http://localhost:8080/callback"
    
    if not client_id or not client_secret:
        print("❌ Please add your FITBIT_CLIENT_ID and FITBIT_CLIENT_SECRET to .env file")
        return
    
    # Step 1: Build authorization URL
    auth_url = (
        f"https://www.fitbit.com/oauth2/authorize?"
        f"response_type=code&"
        f"client_id={client_id}&"
        f"redirect_uri={redirect_uri}&"
        f"scope=activity%20heartrate%20location%20nutrition%20profile%20settings%20sleep%20social%20weight"
    )
    
    print("🔗 Opening browser for Fitbit authorization...")
    print(f"If browser doesn't open, visit: {auth_url}")
    webbrowser.open(auth_url)
    
    # Step 2: Get authorization code from user
    print("\n📋 After authorizing, you'll be redirected to a page that won't load.")
    print("Copy the ENTIRE URL from your browser and paste it here:")
    callback_url = input("Full callback URL: ").strip()
    
    # Extract code from callback URL
    parsed_url = urlparse(callback_url)
    code = parse_qs(parsed_url.query).get('code', [None])[0]
    
    if not code:
        print("❌ No authorization code found in URL")
        return
    
    # Step 3: Exchange code for tokens
    print("🔄 Exchanging code for tokens...")
    
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
        update_env_file(access_token, refresh_token)
        print("\n📝 Updated .env file with your tokens!")
        
    else:
        print(f"❌ Error getting tokens: {response.status_code}")
        print(response.text)

def update_env_file(access_token, refresh_token):
    """Update .env file with tokens"""
    with open('.env', 'r') as f:
        content = f.read()
    
    content = content.replace('FITBIT_ACCESS_TOKEN=', f'FITBIT_ACCESS_TOKEN={access_token}')
    content = content.replace('FITBIT_REFRESH_TOKEN=', f'FITBIT_REFRESH_TOKEN={refresh_token}')
    
    with open('.env', 'w') as f:
        f.write(content)

if __name__ == "__main__":
    get_fitbit_tokens()