#!/usr/bin/env python3
"""
Fix all Sleep Start/End columns in Notion database
"""

import os
from notion_client import Client
from dotenv import load_dotenv

def fix_all_sleep_columns():
    """Update all Sleep Start/End variants to Text type and remove duplicates"""
    load_dotenv()
    
    notion = Client(auth=os.getenv('NOTION_TOKEN'))
    database_id = os.getenv('NOTION_DATABASE_ID')
    
    try:
        # Get current database schema
        database = notion.databases.retrieve(database_id=database_id)
        print("📋 All current database properties:")
        sleep_columns = []
        for prop_name, prop_info in database['properties'].items():
            print(f"  {prop_name}: {prop_info['type']}")
            if 'sleep' in prop_name.lower() and ('start' in prop_name.lower() or 'end' in prop_name.lower()):
                sleep_columns.append(prop_name)
        
        print(f"\n🔍 Found sleep time columns: {sleep_columns}")
        
        # Update all sleep time columns to rich_text
        properties_to_update = {}
        for col_name in sleep_columns:
            if 'start' in col_name.lower():
                properties_to_update["Sleep Start"] = {
                    "type": "rich_text",
                    "rich_text": {}
                }
            elif 'end' in col_name.lower():
                properties_to_update["Sleep End"] = {
                    "type": "rich_text", 
                    "rich_text": {}
                }
        
        print(f"\n🔧 Updating columns: {list(properties_to_update.keys())}")
        
        notion.databases.update(
            database_id=database_id,
            properties=properties_to_update
        )
        
        print("✅ Sleep columns updated to Text type!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    fix_all_sleep_columns()