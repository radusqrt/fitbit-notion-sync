#!/usr/bin/env python3
"""
Backfill Fitbit data to Notion database for a date range
Can be run manually with custom date ranges or defaults to last week
"""

import os
import sys
import argparse
import requests
import time
from datetime import datetime, timedelta
from notion_client import Client
from dotenv import load_dotenv

def get_date_range(start_date=None, end_date=None, last_week=False):
    """Get date range for backfill"""
    if last_week or (not start_date and not end_date):
        # Default to last 7 days
        end_date = datetime.now() - timedelta(days=1)  # Yesterday
        start_date = end_date - timedelta(days=6)  # 7 days total
        return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')
    
    if start_date and not end_date:
        end_date = start_date
    elif end_date and not start_date:
        start_date = end_date
    
    return start_date, end_date

def make_api_request(url, headers, description="API call"):
    """Make API request with rate limiting and retry logic"""
    max_retries = 3
    base_delay = 2  # Start with 2 second delay
    
    for attempt in range(max_retries):
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return response
        elif response.status_code == 429:  # Rate limited
            retry_delay = base_delay * (2 ** attempt)  # Exponential backoff
            print(f"   Rate limited on {description}, waiting {retry_delay}s...")
            time.sleep(retry_delay)
        else:
            print(f"   {description} error {response.status_code}: {response.text}")
            break
    
    return response

def get_fitbit_data(date):
    """Fetch comprehensive Fitbit data for a specific date with rate limiting"""
    load_dotenv()
    access_token = os.getenv('FITBIT_ACCESS_TOKEN')
    
    headers = {'Authorization': f'Bearer {access_token}'}
    base_url = 'https://api.fitbit.com/1/user/-'
    
    data = {}
    
    # Add longer delays between API calls to avoid rate limiting
    api_delay = 2  # Increased to 2 seconds
    
    try:
        # Activity summary
        response = make_api_request(f'{base_url}/activities/date/{date}.json', headers, "Activity")
        if response.status_code == 200:
            activities = response.json()
            summary = activities['summary']
            data['steps'] = summary.get('steps', 0)
            data['distance'] = summary.get('distances', [{}])[0].get('distance', 0) if summary.get('distances') else 0
            data['calories'] = summary.get('caloriesOut', 0)
            data['active_minutes'] = summary.get('fairlyActiveMinutes', 0) + summary.get('veryActiveMinutes', 0)
        
        time.sleep(api_delay)  # Delay between API calls
        
        # Sleep data with detailed stages - use sleep log list endpoint for stages data
        headers_v12 = headers.copy()
        headers_v12['Accept-Language'] = 'en_US'
        headers_v12['Accept-Version'] = '1.2'
        
        # Use sleep log list endpoint to get stages data
        from datetime import datetime, timedelta
        next_day = (datetime.strptime(date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
        response = make_api_request(f'https://api.fitbit.com/1.2/user/-/sleep/list.json?beforeDate={next_day}&sort=desc&limit=5', headers_v12, "Sleep")
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
                
                if main_sleep:
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
        
        time.sleep(api_delay)  # Delay between API calls
        
        # Heart rate data (resting + zones)
        response = make_api_request(f'{base_url}/activities/heart/date/{date}/1d.json', headers, "Heart Rate")
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
        
        time.sleep(api_delay)  # Delay between API calls
        
        # Weight data (if available)
        response = make_api_request(f'{base_url}/body/log/weight/date/{date}.json', headers, "Weight")
        if response.status_code == 200:
            weight_data = response.json()
            if weight_data.get('weight'):
                latest_weight = weight_data['weight'][0]
                data['weight'] = latest_weight.get('weight')
                data['bmi'] = latest_weight.get('bmi')
        
        time.sleep(api_delay)  # Delay between API calls
        
        # Body fat data (if available)
        response = make_api_request(f'{base_url}/body/log/fat/date/{date}.json', headers, "Body Fat")
        if response.status_code == 200:
            fat_data = response.json()
            if fat_data.get('fat'):
                data['body_fat'] = fat_data['fat'][0].get('fat')
        
        time.sleep(api_delay)  # Delay between API calls
        
        # HRV data (Heart Rate Variability)
        response = make_api_request(f'{base_url}/hrv/date/{date}.json', headers, "HRV")
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
        print(f"❌ Error fetching Fitbit data for {date}: {e}")
        return None

def update_notion_database(date, fitbit_data):
    """Update or create entry in Notion database (reused from sync script)"""
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
    
    # Optional body metrics (only add if data exists and columns exist in database)
    # These columns might not exist in all databases, so we'll skip them gracefully
    
    if fitbit_data.get('hrv_daily_rmssd'):
        properties["HRV Daily RMSSD"] = {"number": fitbit_data['hrv_daily_rmssd']}
    
    if fitbit_data.get('hrv_deep_rmssd'):
        properties["HRV Deep RMSSD"] = {"number": fitbit_data['hrv_deep_rmssd']}
    
    try:
        if existing_pages['results']:
            # Update existing page
            page_id = existing_pages['results'][0]['id']
            notion.pages.update(page_id=page_id, properties=properties)
            return "updated"
        else:
            # Create new page
            notion.pages.create(
                parent={"database_id": database_id},
                properties=properties
            )
            return "created"
            
    except Exception as e:
        print(f"❌ Error updating Notion for {date}: {e}")
        return "error"

def generate_date_list(start_date, end_date):
    """Generate list of dates between start and end date (inclusive)"""
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    date_list = []
    current = start
    while current <= end:
        date_list.append(current.strftime('%Y-%m-%d'))
        current += timedelta(days=1)
    
    return date_list

def main():
    """Main backfill function"""
    parser = argparse.ArgumentParser(description='Backfill Fitbit data to Notion database')
    parser.add_argument('--start-date', '-s', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', '-e', type=str, help='End date (YYYY-MM-DD)')
    parser.add_argument('--last-week', '-w', action='store_true', help='Backfill last 7 days (default if no dates provided)')
    
    args = parser.parse_args()
    
    # Get date range
    start_date, end_date = get_date_range(args.start_date, args.end_date, args.last_week)
    
    print("🔄 Starting Fitbit → Notion backfill...")
    print(f"📅 Date range: {start_date} to {end_date}")
    
    # Generate list of dates to process
    dates = generate_date_list(start_date, end_date)
    
    print(f"📊 Processing {len(dates)} days...")
    
    # Track results
    created = 0
    updated = 0
    errors = 0
    
    for date in dates:
        print(f"\n📅 Processing {date}...")
        
        # Get Fitbit data
        fitbit_data = get_fitbit_data(date)
        if not fitbit_data:
            print(f"❌ Failed to fetch Fitbit data for {date}")
            errors += 1
            continue
        
        # Show key metrics
        print(f"   Steps: {fitbit_data.get('steps', 0)}, Sleep: {fitbit_data.get('sleep_hours', 0)}h, HRV: {fitbit_data.get('hrv_daily_rmssd', 'N/A')}")
        
        # Update Notion
        result = update_notion_database(date, fitbit_data)
        if result == "created":
            print(f"✅ Created entry for {date}")
            created += 1
        elif result == "updated":
            print(f"✅ Updated entry for {date}")
            updated += 1
        else:
            errors += 1
        
        # Longer delay between days to avoid overwhelming API
        if date != dates[-1]:  # Don't delay after the last date
            time.sleep(5)  # 5 second delay between days
    
    # Summary
    print(f"\n🎉 Backfill completed!")
    print(f"📊 Results: {created} created, {updated} updated, {errors} errors")

if __name__ == "__main__":
    main()