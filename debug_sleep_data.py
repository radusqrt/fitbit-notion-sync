#!/usr/bin/env python3
"""
Debug Fitbit sleep data to see what's actually returned
"""

import os
import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

def debug_fitbit_sleep():
    """Fetch and display raw Fitbit sleep data"""
    load_dotenv()
    access_token = os.getenv('FITBIT_ACCESS_TOKEN')
    
    headers = {'Authorization': f'Bearer {access_token}'}
    base_url = 'https://api.fitbit.com/1/user/-'
    
    # Get yesterday's date
    yesterday = datetime.now() - timedelta(days=1)
    date = yesterday.strftime('%Y-%m-%d')
    
    print(f"🔍 Debugging sleep data for: {date}")
    
    # Try different sleep endpoints
    endpoints = [
        f'{base_url}/sleep/date/{date}.json',
        f'{base_url}/sleep/date/{date}/1d.json',
        f'{base_url}/sleep/list.json?beforeDate={date}&sort=desc&offset=0&limit=1'
    ]
    
    for i, endpoint in enumerate(endpoints, 1):
        print(f"\n📡 Endpoint {i}: {endpoint}")
        try:
            response = requests.get(endpoint, headers=headers)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Status: {response.status_code}")
                print(f"📄 Raw response:")
                print(json.dumps(data, indent=2))
            else:
                print(f"❌ Status: {response.status_code}")
                print(f"Error: {response.text}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("="*50)

if __name__ == "__main__":
    debug_fitbit_sleep()