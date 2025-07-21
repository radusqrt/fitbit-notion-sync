#!/usr/bin/env python3
"""
Sync Fitbit data to Notion database
Fetches yesterday's health metrics and updates Notion
"""

import os
import requests
from datetime import datetime, timedelta
from notion_client import Client
from dotenv import load_dotenv

def get_yesterday_date():
    """Get yesterday's date in YYYY-MM-DD format (Zurich timezone)"""
    # For simplicity, using UTC. In production, consider timezone conversion
    yesterday = datetime.now() - timedelta(days=1)
    return yesterday.strftime('%Y-%m-%d')

def refresh_fitbit_token():
    """Refresh the Fitbit access token if needed"""
    load_dotenv()
    
    client_id = os.getenv('FITBIT_CLIENT_ID')
    client_secret = os.getenv('FITBIT_CLIENT_SECRET')
    refresh_token = os.getenv('FITBIT_REFRESH_TOKEN')
    
    headers = {
        'Authorization': f'Basic {requests.auth._basic_auth_str(client_id, client_secret)}',
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
        new_refresh_token = tokens['refresh_token']
        
        # Update .env file
        with open('.env', 'r') as f:
            content = f.read()
        
        content = content.replace(
            f'FITBIT_ACCESS_TOKEN={os.getenv("FITBIT_ACCESS_TOKEN")}',
            f'FITBIT_ACCESS_TOKEN={new_access_token}'
        )
        content = content.replace(
            f'FITBIT_REFRESH_TOKEN={refresh_token}',
            f'FITBIT_REFRESH_TOKEN={new_refresh_token}'
        )
        
        with open('.env', 'w') as f:
            f.write(content)
            
        return new_access_token
    else:
        raise Exception(f"Failed to refresh token: {response.text}")

def get_fitbit_data(date):
    """Fetch comprehensive Fitbit data for a specific date"""
    load_dotenv()
    access_token = os.getenv('FITBIT_ACCESS_TOKEN')
    
    headers = {'Authorization': f'Bearer {access_token}'}
    base_url = 'https://api.fitbit.com/1/user/-'
    
    data = {}
    
    try:
        # Activity summary
        response = requests.get(f'{base_url}/activities/date/{date}.json', headers=headers)
        if response.status_code == 200:
            activities = response.json()
            summary = activities['summary']
            data['steps'] = summary.get('steps', 0)
            data['distance'] = summary.get('distances', [{}])[0].get('distance', 0) if summary.get('distances') else 0
            data['calories'] = summary.get('caloriesOut', 0)
            data['active_minutes'] = summary.get('fairlyActiveMinutes', 0) + summary.get('veryActiveMinutes', 0)
        
        # Sleep data with detailed stages
        response = requests.get(f'{base_url}/sleep/date/{date}.json', headers=headers)
        if response.status_code == 200:
            sleep_data = response.json()
            if sleep_data.get('sleep'):
                main_sleep = sleep_data['sleep'][0]
                data['sleep_hours'] = round(main_sleep.get('minutesAsleep', 0) / 60, 1)
                data['sleep_efficiency'] = main_sleep.get('efficiency', 0)
                data['sleep_start'] = main_sleep.get('startTime', '')
                data['sleep_end'] = main_sleep.get('endTime', '')
                
                # Sleep stages
                levels = main_sleep.get('levels', {}).get('summary', {})
                data['deep_sleep'] = levels.get('deep', {}).get('minutes', 0)
                data['light_sleep'] = levels.get('light', {}).get('minutes', 0)
                data['rem_sleep'] = levels.get('rem', {}).get('minutes', 0)
        
        # Heart rate data (resting + zones)
        response = requests.get(f'{base_url}/activities/heart/date/{date}/1d.json', headers=headers)
        if response.status_code == 200:
            hr_data = response.json()
            if hr_data.get('activities-heart'):
                heart_info = hr_data['activities-heart'][0].get('value', {})
                data['resting_heart_rate'] = heart_info.get('restingHeartRate')
                
                # Heart rate zones
                zones = heart_info.get('heartRateZones', [])
                for zone in zones:
                    zone_name = zone.get('name', '').lower().replace(' ', '_')
                    if 'fat_burn' in zone_name or 'fat burn' in zone_name:
                        data['fat_burn_minutes'] = zone.get('minutes', 0)
                    elif 'cardio' in zone_name:
                        data['cardio_minutes'] = zone.get('minutes', 0)  
                    elif 'peak' in zone_name:
                        data['peak_minutes'] = zone.get('minutes', 0)
        
        # Weight data (if available)
        response = requests.get(f'{base_url}/body/log/weight/date/{date}.json', headers=headers)
        if response.status_code == 200:
            weight_data = response.json()
            if weight_data.get('weight'):
                latest_weight = weight_data['weight'][0]
                data['weight'] = latest_weight.get('weight')
                data['bmi'] = latest_weight.get('bmi')
        
        # Body fat data (if available)
        response = requests.get(f'{base_url}/body/log/fat/date/{date}.json', headers=headers)
        if response.status_code == 200:
            fat_data = response.json()
            if fat_data.get('fat'):
                data['body_fat'] = fat_data['fat'][0].get('fat')
        
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching Fitbit data: {e}")
        return None

def update_notion_database(date, fitbit_data):
    """Update or create entry in Notion database"""
    load_dotenv()
    
    notion = Client(auth=os.getenv('NOTION_TOKEN'))
    database_id = os.getenv('NOTION_DATABASE_ID')
    
    # Check if entry already exists for this date
    existing_pages = notion.databases.query(
        database_id=database_id,
        filter={
            "property": "Date",
            "date": {
                "equals": date
            }
        }
    )
    
    # Prepare properties with all Fitbit metrics
    properties = {
        "Date": {"date": {"start": date}},
        "Steps": {"number": fitbit_data.get('steps', 0)},
        "Distance (km)": {"number": round(fitbit_data.get('distance', 0), 2)},
        "Calories": {"number": fitbit_data.get('calories', 0)},
        "Active Minutes": {"number": fitbit_data.get('active_minutes', 0)},
        "Sleep Hours": {"number": fitbit_data.get('sleep_hours', 0)},
        "Sleep Efficiency": {"number": fitbit_data.get('sleep_efficiency', 0)},
        "Deep Sleep (min)": {"number": fitbit_data.get('deep_sleep', 0)},
        "Light Sleep (min)": {"number": fitbit_data.get('light_sleep', 0)},
        "REM Sleep (min)": {"number": fitbit_data.get('rem_sleep', 0)},
        "Fat Burn Zone (min)": {"number": fitbit_data.get('fat_burn_minutes', 0)},
        "Cardio Zone (min)": {"number": fitbit_data.get('cardio_minutes', 0)},
        "Peak Zone (min)": {"number": fitbit_data.get('peak_minutes', 0)},
    }
    
    # Add optional properties if available
    if fitbit_data.get('resting_heart_rate'):
        properties["Wake Resting HR"] = {"number": fitbit_data['resting_heart_rate']}
    
    if fitbit_data.get('sleep_start'):
        # Extract time from datetime string (e.g. "2025-07-20T14:45:00.000" -> "14:45")
        time_part = fitbit_data['sleep_start'].split('T')[1].split(':')
        properties["Sleep Start"] = {"rich_text": [{"text": {"content": f"{time_part[0]}:{time_part[1]}"}}]}
    
    if fitbit_data.get('sleep_end'):
        time_part = fitbit_data['sleep_end'].split('T')[1].split(':')
        properties["Sleep End"] = {"rich_text": [{"text": {"content": f"{time_part[0]}:{time_part[1]}"}}]}
    
    if fitbit_data.get('weight'):
        properties["Weight (kg)"] = {"number": fitbit_data['weight']}
    
    if fitbit_data.get('bmi'):
        properties["BMI"] = {"number": fitbit_data['bmi']}
    
    if fitbit_data.get('body_fat'):
        properties["Body Fat %"] = {"number": fitbit_data['body_fat']}
    
    try:
        if existing_pages['results']:
            # Update existing page
            page_id = existing_pages['results'][0]['id']
            notion.pages.update(page_id=page_id, properties=properties)
            print(f"✅ Updated existing entry for {date}")
        else:
            # Create new page
            notion.pages.create(
                parent={"database_id": database_id},
                properties=properties
            )
            print(f"✅ Created new entry for {date}")
            
    except Exception as e:
        print(f"❌ Error updating Notion: {e}")

def main():
    """Main sync function"""
    print("🔄 Starting Fitbit → Notion sync...")
    
    date = get_yesterday_date()
    print(f"📅 Syncing data for: {date}")
    
    # Get Fitbit data
    fitbit_data = get_fitbit_data(date)
    if not fitbit_data:
        print("❌ Failed to fetch Fitbit data")
        return
    
    print("📊 Fitbit data fetched:")
    for key, value in fitbit_data.items():
        print(f"  {key}: {value}")
    
    # Update Notion
    update_notion_database(date, fitbit_data)
    
    print("🎉 Sync completed!")

if __name__ == "__main__":
    main()