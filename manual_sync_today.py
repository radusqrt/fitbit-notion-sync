#!/usr/bin/env python3
"""
Manual sync for today's date (including your latte photo!)
"""

import os
import sys
from datetime import datetime
from google_drive_food import process_drive_food_photos, format_meal_text
from sync_fitbit_notion import get_fitbit_data, update_notion_database

def manual_sync_today():
    """Manual sync for today's date"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    print(f"🔄 Starting MANUAL sync for TODAY: {today}")
    print(f"🎯 This will include your breakfast latte photo!")
    print()
    
    # Get Fitbit data for today
    print("📊 Fetching Fitbit data for today...")
    try:
        fitbit_data = get_fitbit_data(today)
        if fitbit_data:
            print("✅ Fitbit data fetched:")
            for key, value in fitbit_data.items():
                if value is not None and value != 0:
                    print(f"  {key}: {value}")
        else:
            print("⚠️ No Fitbit data available for today")
            fitbit_data = {}
    except Exception as e:
        print(f"⚠️ Error fetching Fitbit data: {e}")
        print("  (This is normal if today's data isn't complete yet)")
        fitbit_data = {}
    
    print()
    
    # Get food data from Drive
    print("🍽️ Processing food photos from Drive...")
    try:
        food_data = process_drive_food_photos(today)
        
        food_found = any(food_data.values())
        if food_found:
            print("✅ Food data processed:")
            for meal, foods in food_data.items():
                if foods:
                    print(f"  {meal.title()}: {format_meal_text(foods)}")
        else:
            print("  No food photos found for today")
            
    except Exception as e:
        print(f"❌ Error processing food photos: {e}")
        food_data = None
    
    print()
    
    # Update Notion
    print("📝 Updating Notion database...")
    try:
        update_notion_database(today, fitbit_data, food_data)
        print("✅ Notion database updated successfully!")
        print()
        print("🎉 Manual sync completed!")
        print("📱 Check your Notion database to see the results!")
        
    except Exception as e:
        print(f"❌ Error updating Notion: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = manual_sync_today()
    if success:
        print("\n🚀 Your latte should now appear in your Notion health database!")
    else:
        print("\n❌ Sync failed - check the errors above")