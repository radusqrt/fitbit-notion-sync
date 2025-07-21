#!/usr/bin/env python3
"""
Fix Notion database schema by updating Sleep Start/End columns to Text type
"""

import os
from notion_client import Client
from dotenv import load_dotenv

def fix_database_schema():
    """Update Sleep Start/End columns to Text type"""
    load_dotenv()
    
    notion = Client(auth=os.getenv('NOTION_TOKEN'))
    database_id = os.getenv('NOTION_DATABASE_ID')
    
    try:
        # Get current database schema
        database = notion.databases.retrieve(database_id=database_id)
        print("📋 Current database properties:")
        for prop_name, prop_info in database['properties'].items():
            print(f"  {prop_name}: {prop_info['type']}")
        
        # Update Sleep Start and Sleep End to Text type
        print("\n🔧 Updating Sleep Start and Sleep End to Text type...")
        
        notion.databases.update(
            database_id=database_id,
            properties={
                "Sleep Start": {
                    "type": "rich_text",
                    "rich_text": {}
                },
                "Sleep End": {
                    "type": "rich_text", 
                    "rich_text": {}
                }
            }
        )
        
        print("✅ Database schema updated successfully!")
        
        # Verify the update
        updated_database = notion.databases.retrieve(database_id=database_id)
        print("\n📋 Updated database properties:")
        for prop_name, prop_info in updated_database['properties'].items():
            if 'Sleep' in prop_name:
                print(f"  {prop_name}: {prop_info['type']}")
        
    except Exception as e:
        print(f"❌ Error updating database schema: {e}")

if __name__ == "__main__":
    fix_database_schema()