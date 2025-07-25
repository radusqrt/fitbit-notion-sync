#!/usr/bin/env python3
"""
Helper script to display current token values for updating GitHub Secrets
"""

import os
from dotenv import load_dotenv

def main():
    load_dotenv()
    
    print("🔑 CURRENT TOKEN VALUES FOR GITHUB SECRETS")
    print("=" * 50)
    print("Copy these values to your GitHub repository secrets:")
    print("Settings → Secrets and variables → Actions → Update secrets")
    print()
    
    secrets = [
        ('FITBIT_CLIENT_ID', os.getenv('FITBIT_CLIENT_ID')),
        ('FITBIT_CLIENT_SECRET', os.getenv('FITBIT_CLIENT_SECRET')),
        ('FITBIT_ACCESS_TOKEN', os.getenv('FITBIT_ACCESS_TOKEN')),
        ('FITBIT_REFRESH_TOKEN', os.getenv('FITBIT_REFRESH_TOKEN')),
        ('NOTION_TOKEN', os.getenv('NOTION_TOKEN')),
        ('NOTION_DATABASE_ID', os.getenv('NOTION_DATABASE_ID')),
        ('GOOGLE_CLIENT_ID', os.getenv('GOOGLE_CLIENT_ID')),
        ('GOOGLE_CLIENT_SECRET', os.getenv('GOOGLE_CLIENT_SECRET')),
        ('GOOGLE_ACCESS_TOKEN', os.getenv('GOOGLE_ACCESS_TOKEN')),
        ('GOOGLE_REFRESH_TOKEN', os.getenv('GOOGLE_REFRESH_TOKEN')),
        ('GOOGLE_API_KEY', os.getenv('GOOGLE_API_KEY')),
    ]
    
    for name, value in secrets:
        if value:
            # Show first 10 and last 10 characters for security
            if len(value) > 20:
                display_value = f"{value[:10]}...{value[-10:]}"
                print(f"{name}: {display_value}")
                print(f"  Full value: {value}")
            else:
                print(f"{name}: {value}")
        else:
            print(f"{name}: ❌ NOT SET")
        print()

if __name__ == "__main__":
    main()