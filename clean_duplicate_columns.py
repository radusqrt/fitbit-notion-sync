#!/usr/bin/env python3
"""
Remove duplicate sleep columns from Notion database
"""

import os
from notion_client import Client
from dotenv import load_dotenv

def remove_duplicate_sleep_columns():
    """Remove duplicate 'Sleep start' and 'Sleep end' columns"""
    load_dotenv()
    
    notion = Client(auth=os.getenv('NOTION_TOKEN'))
    database_id = os.getenv('NOTION_DATABASE_ID')
    
    try:
        print("🗑️ Removing duplicate sleep columns...")
        
        # Remove the lowercase duplicates by setting them to null
        notion.databases.update(
            database_id=database_id,
            properties={
                "Sleep start": None,  # This removes the property
                "Sleep end": None     # This removes the property
            }
        )
        
        print("✅ Duplicate sleep columns removed!")
        
        # Verify cleanup
        database = notion.databases.retrieve(database_id=database_id)
        print("\n📋 Remaining sleep columns:")
        for prop_name, prop_info in database['properties'].items():
            if 'sleep' in prop_name.lower() and ('start' in prop_name.lower() or 'end' in prop_name.lower()):
                print(f"  {prop_name}: {prop_info['type']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    remove_duplicate_sleep_columns()