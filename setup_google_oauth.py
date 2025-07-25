#!/usr/bin/env python3
"""
Set up Google Drive OAuth and get refresh token
"""

import os
import webbrowser
from urllib.parse import urlparse, parse_qs
import requests
from dotenv import load_dotenv

def setup_google_oauth():
    """Set up Google Drive OAuth to get refresh token"""
    load_dotenv()
    
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
    
    if not all([client_id, client_secret]):
        print("❌ Missing Google Client ID/Secret in .env file")
        return False
    
    # OAuth flow with offline access to get refresh token
    auth_url = f"https://accounts.google.com/o/oauth2/auth?client_id={client_id}&redirect_uri=http://localhost:8080&scope=https://www.googleapis.com/auth/drive.readonly&response_type=code&access_type=offline&prompt=consent"
    
    print("🔄 Setting up Google Drive OAuth to get refresh token...")
    print("1. Opening browser for Google authorization...")
    print("2. Make sure to approve access to Google Drive")
    print("3. You'll be redirected to localhost:8080 - that's expected")
    print("4. Copy the FULL redirect URL and paste it here")
    print()
    
    webbrowser.open(auth_url)
    
    print("📋 Authorization URL (if browser didn't open):")
    print(auth_url)
    print()
    
    redirect_url = input("🔗 Paste the full redirect URL here: ").strip()
    
    # Extract code from redirect URL
    parsed_url = urlparse(redirect_url)
    query_params = parse_qs(parsed_url.query)
    
    if 'code' not in query_params:
        print("❌ No authorization code found in URL")
        return False
    
    auth_code = query_params['code'][0]
    print(f"✅ Got authorization code: {auth_code[:20]}...")
    
    # Exchange code for tokens
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'code': auth_code,
        'grant_type': 'authorization_code',
        'redirect_uri': 'http://localhost:8080'
    }
    
    print("🔄 Exchanging code for tokens...")
    response = requests.post(token_url, data=token_data)
    
    if response.status_code == 200:
        tokens = response.json()
        access_token = tokens['access_token']
        refresh_token = tokens.get('refresh_token', '')
        
        print("✅ Google OAuth successful!")
        print(f"📋 Access token: {access_token[:20]}...")
        if refresh_token:
            print(f"📋 Refresh token: {refresh_token[:20]}...")
            
            # Update .env file
            with open('.env', 'r') as f:
                content = f.read()
            
            # Update or add tokens
            if 'GOOGLE_ACCESS_TOKEN=' in content:
                # Replace existing
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if line.startswith('GOOGLE_ACCESS_TOKEN='):
                        lines[i] = f'GOOGLE_ACCESS_TOKEN={access_token}'
                    elif line.startswith('GOOGLE_REFRESH_TOKEN='):
                        lines[i] = f'GOOGLE_REFRESH_TOKEN={refresh_token}'
                content = '\n'.join(lines)
            else:
                # Add new
                content += f'\nGOOGLE_ACCESS_TOKEN={access_token}\n'
                content += f'GOOGLE_REFRESH_TOKEN={refresh_token}\n'
            
            # Add refresh token if not present
            if 'GOOGLE_REFRESH_TOKEN=' not in content:
                content += f'GOOGLE_REFRESH_TOKEN={refresh_token}\n'
            
            with open('.env', 'w') as f:
                f.write(content)
            
            print()
            print("🔑 TOKENS UPDATED IN .env FILE")
            print("Now update your GitHub Secrets with these values:")
            print(f"GOOGLE_ACCESS_TOKEN={access_token}")
            print(f"GOOGLE_REFRESH_TOKEN={refresh_token}")
            
        else:
            print("⚠️ No refresh token received - you may need to revoke access and try again")
            
        return True
    else:
        print(f"❌ Failed to get tokens: {response.text}")
        return False

if __name__ == "__main__":
    setup_google_oauth()