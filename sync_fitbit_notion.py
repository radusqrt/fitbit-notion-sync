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
# Import Google Drive functionality with fallback
try:
    from google_drive_food import process_drive_food_photos, format_meal_text
    GOOGLE_DRIVE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Google Drive integration not available: {e}")
    GOOGLE_DRIVE_AVAILABLE = False
    def process_drive_food_photos(date):
        return None
    def format_meal_text(foods):
        return ""

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

def make_api_request_with_refresh(url, headers):
    """Make API request with automatic token refresh if needed"""
    response = requests.get(url, headers=headers)
    
    if response.status_code == 401:  # Token expired
        print("🔄 Access token expired, refreshing...")
        try:
            new_token = refresh_fitbit_token()
            headers['Authorization'] = f'Bearer {new_token}'
            # Retry with new token
            response = requests.get(url, headers=headers)
        except Exception as e:
            print(f"❌ Token refresh failed: {e}")
    
    return response

def get_fitbit_data(date):
    """Fetch comprehensive Fitbit data for a specific date"""
    load_dotenv()
    access_token = os.getenv('FITBIT_ACCESS_TOKEN')
    
    headers = {'Authorization': f'Bearer {access_token}'}
    base_url = 'https://api.fitbit.com/1/user/-'
    
    data = {}
    
    try:
        # Activity summary
        response = make_api_request_with_refresh(f'{base_url}/activities/date/{date}.json', headers)
        if response.status_code == 200:
            activities = response.json()
            summary = activities['summary']
            data['steps'] = summary.get('steps', 0)
            data['distance'] = summary.get('distances', [{}])[0].get('distance', 0) if summary.get('distances') else 0
            data['calories'] = summary.get('caloriesOut', 0)
            data['active_minutes'] = summary.get('fairlyActiveMinutes', 0) + summary.get('veryActiveMinutes', 0)
        
        # Sleep data with detailed stages - use sleep log list endpoint for stages data
        headers_v12 = headers.copy()
        headers_v12['Accept-Language'] = 'en_US'
        headers_v12['Accept-Version'] = '1.2'
        
        # Use sleep log list endpoint to get stages data
        from datetime import datetime, timedelta
        next_day = (datetime.strptime(date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
        response = make_api_request_with_refresh(f'https://api.fitbit.com/1.2/user/-/sleep/list.json?beforeDate={next_day}&sort=desc&limit=5', headers_v12)
        if response.status_code == 200:
            sleep_data = response.json()
            if sleep_data.get('sleep'):
                # Find the sleep session for the specific date
                main_sleep = None
                for sleep_session in sleep_data['sleep']:
                    if sleep_session.get('dateOfSleep') == date and sleep_session.get('isMainSleep', False):
                        main_sleep = sleep_session
                        break
                
                # Fallback to any session for the date
                if not main_sleep:
                    for sleep_session in sleep_data['sleep']:
                        if sleep_session.get('dateOfSleep') == date:
                            main_sleep = sleep_session
                            break
                data['sleep_hours'] = round(main_sleep.get('minutesAsleep', 0) / 60, 1)
                data['sleep_efficiency'] = main_sleep.get('efficiency', 0)
                data['sleep_start'] = main_sleep.get('startTime', '')
                data['sleep_end'] = main_sleep.get('endTime', '')
                
                # Sleep stages - handle both new and old Fitbit formats
                levels = main_sleep.get('levels', {})
                
                # First try new format with levels.summary
                if 'summary' in levels and levels['summary']:
                    summary = levels['summary']
                    data['deep_sleep'] = summary.get('deep', {}).get('minutes', 0)
                    data['light_sleep'] = summary.get('light', {}).get('minutes', 0)
                    data['rem_sleep'] = summary.get('rem', {}).get('minutes', 0)
                
                # If no summary, try parsing levels.data for sleep stages
                elif 'data' in levels and levels['data']:
                    stage_minutes = {'deep': 0, 'light': 0, 'rem': 0}
                    
                    # Parse data groupings (stages > 3 minutes)
                    for period in levels['data']:
                        stage = period.get('level', '')
                        if stage in stage_minutes:
                            # Convert seconds to minutes
                            duration_seconds = period.get('seconds', 0)
                            stage_minutes[stage] += duration_seconds // 60
                    
                    # Parse shortData if available (short wake periods ≤ 3 minutes)
                    if 'shortData' in levels:
                        for period in levels.get('shortData', []):
                            stage = period.get('level', '')
                            if stage in stage_minutes:
                                duration_seconds = period.get('seconds', 0)
                                stage_minutes[stage] += duration_seconds // 60
                    
                    data['deep_sleep'] = stage_minutes['deep']
                    data['light_sleep'] = stage_minutes['light']
                    data['rem_sleep'] = stage_minutes['rem']
                
                else:
                    # Fallback to old format - parse minuteData
                    minute_data = main_sleep.get('minuteData', [])
                    if minute_data:
                        asleep_minutes = sum(1 for m in minute_data if m.get('value') == '1')
                        # For old format, treat all sleep as "light sleep"
                        data['light_sleep'] = asleep_minutes
                        data['deep_sleep'] = 0  # Not available in old format
                        data['rem_sleep'] = 0   # Not available in old format
                    else:
                        data['deep_sleep'] = 0
                        data['light_sleep'] = 0
                        data['rem_sleep'] = 0
        
        # Heart rate data (resting + zones)
        response = make_api_request_with_refresh(f'{base_url}/activities/heart/date/{date}/1d.json', headers)
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
        response = make_api_request_with_refresh(f'{base_url}/body/log/weight/date/{date}.json', headers)
        if response.status_code == 200:
            weight_data = response.json()
            if weight_data.get('weight'):
                latest_weight = weight_data['weight'][0]
                data['weight'] = latest_weight.get('weight')
                data['bmi'] = latest_weight.get('bmi')
        
        # Body fat data (if available)
        response = make_api_request_with_refresh(f'{base_url}/body/log/fat/date/{date}.json', headers)
        if response.status_code == 200:
            fat_data = response.json()
            if fat_data.get('fat'):
                data['body_fat'] = fat_data['fat'][0].get('fat')
        
        # HRV data (Heart Rate Variability)
        response = make_api_request_with_refresh(f'{base_url}/hrv/date/{date}.json', headers)
        if response.status_code == 200:
            hrv_data = response.json()
            if hrv_data.get('hrv'):
                hrv_entries = hrv_data['hrv']
                if hrv_entries:
                    # Get the most recent HRV reading for the day
                    latest_hrv = hrv_entries[-1]
                    hrv_value = latest_hrv.get('value', {})
                    data['hrv_daily_rmssd'] = hrv_value.get('dailyRmssd')
                    data['hrv_deep_rmssd'] = hrv_value.get('deepRmssd')
        
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching Fitbit data: {e}")
        return None

def update_notion_database(date, fitbit_data, food_data=None):
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
    
    if fitbit_data.get('hrv_daily_rmssd'):
        properties["HRV Daily RMSSD"] = {"number": fitbit_data['hrv_daily_rmssd']}
    
    if fitbit_data.get('hrv_deep_rmssd'):
        properties["HRV Deep RMSSD"] = {"number": fitbit_data['hrv_deep_rmssd']}
    
    # Add food data if available
    if food_data:
        if food_data.get('breakfast'):
            properties["Breakfast"] = {"rich_text": [{"text": {"content": format_meal_text(food_data['breakfast'])}}]}
        
        if food_data.get('lunch'):
            properties["Lunch"] = {"rich_text": [{"text": {"content": format_meal_text(food_data['lunch'])}}]}
        
        if food_data.get('dinner'):
            properties["Dinner"] = {"rich_text": [{"text": {"content": format_meal_text(food_data['dinner'])}}]}
        
        # Mark that food photos were processed
        properties["Food Photos Processed"] = {"checkbox": True}
    
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
    
    # Get Google Drive food data
    if GOOGLE_DRIVE_AVAILABLE:
        print("🍽️ Processing food photos from Drive...")
        try:
            food_data = process_drive_food_photos(date)
            
            # Log food data
            if food_data and any(food_data.values()):
                print("📊 Food data processed:")
                for meal, foods in food_data.items():
                    if foods:
                        print(f"  {meal}: {format_meal_text(foods)}")
            else:
                print("  No food photos found for this date")
                
        except Exception as e:
            print(f"⚠️ Error processing food photos: {e}")
            food_data = None
    else:
        print("⚠️ Google Drive integration disabled - skipping food photos")
        food_data = None
    
    # Update Notion
    update_notion_database(date, fitbit_data, food_data)
    
    print("🎉 Sync completed!")

if __name__ == "__main__":
    main()