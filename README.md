# Fitbit to Notion Sync

Automated daily sync of Fitbit health data to a Notion database using GitHub Actions.

## Features

- **Automated Daily Sync**: Runs every day at 9 AM Zurich time
- **Manual Backfill**: Fill in missing historical data for any date range
- **Comprehensive Health Metrics**:
  - Activity: Steps, distance, calories, active minutes
  - Sleep: Total hours, efficiency, start/end times, sleep stages (deep/light/REM)
  - Heart Rate: Resting HR, fat burn/cardio/peak zones
  - HRV: Daily and deep sleep heart rate variability
  - Body: Weight, BMI, body fat percentage (if available)

## Setup

### 1. Fitbit API Setup
1. Go to https://dev.fitbit.com/apps/new
2. Create a "Server" application type
3. Note your Client ID and Client Secret

### 2. Notion Integration Setup
1. Go to https://www.notion.so/my-integrations
2. Create a new integration
3. Copy the integration token
4. Share your health tracking database with the integration

### 3. Get OAuth Tokens
Run the OAuth helper to get your personal access tokens:
```bash
python oauth_helper.py
```
This will guide you through the Fitbit authorization process and save tokens to your `.env` file.

### 4. GitHub Secrets Setup
**Required for automation:** Copy values from your `.env` file to GitHub Secrets.

Go to your repository → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Add these 6 secrets:
- `FITBIT_CLIENT_ID` - Your Fitbit app Client ID
- `FITBIT_CLIENT_SECRET` - Your Fitbit app Client Secret  
- `FITBIT_ACCESS_TOKEN` - Generated from OAuth flow
- `FITBIT_REFRESH_TOKEN` - Generated from OAuth flow
- `NOTION_TOKEN` - Your Notion integration token
- `NOTION_DATABASE_ID` - Your Notion database ID (from database URL)

**Note:** GitHub Actions requires these secrets to access your APIs. The local `.env` file only works for manual runs.

### 5. Notion Database Schema
Your Notion database should have these columns:

**Required:**
- Date (Date)
- Steps (Number)
- Wake Resting HR (Number)

**Optional Activity:**
- Distance (km) (Number)
- Calories (Number)
- Active Minutes (Number)

**Sleep Metrics:**
- Sleep Hours (Number)
- Sleep Efficiency (Number)
- Sleep Start (Text)
- Sleep End (Text)
- Deep Sleep (min) (Number)
- Light Sleep (min) (Number)
- REM Sleep (min) (Number)

**Heart Rate Zones:**
- Fat Burn Zone (min) (Number)
- Cardio Zone (min) (Number)
- Peak Zone (min) (Number)

**HRV Metrics:**
- HRV Daily RMSSD (Number)
- HRV Deep RMSSD (Number)

**Body Metrics (optional):**
- Weight (kg) (Number)
- BMI (Number)
- Body Fat % (Number)

## Usage

### Automatic Sync
The workflow runs automatically every day at 9 AM Zurich time via GitHub Actions.

### Manual Sync
```bash
# Run locally for today
python sync_fitbit_notion.py

# Or trigger GitHub Action manually from the Actions tab
```

### Backfill Historical Data
```bash
# Backfill last week (local)
python backfill_fitbit_data.py

# Backfill specific date range (local)
python backfill_fitbit_data.py --start-date 2025-07-01 --end-date 2025-07-10

# Backfill single day (local)
python backfill_fitbit_data.py --start-date 2025-07-15

# Or use GitHub Actions:
# 1. Go to Actions tab → "Manual Backfill Fitbit Data"
# 2. Click "Run workflow"
# 3. Choose date range or select "last week"
```

### Initial OAuth Setup
If you need to get new tokens:
```bash
python oauth_helper.py
```

## Files

- `sync_fitbit_notion.py` - Main daily sync script
- `backfill_fitbit_data.py` - Historical data backfill script
- `oauth_helper.py` - One-time OAuth setup helper
- `.github/workflows/sync-health-data.yml` - Daily sync GitHub Actions workflow
- `.github/workflows/manual-backfill.yml` - Manual backfill GitHub Actions workflow
- `requirements.txt` - Python dependencies

## Data Handling

- **Sleep Stages**: Supports both new Fitbit API format (detailed stages) and older format (calculated from minute data)
- **Main Sleep**: Prioritizes main sleep session over naps
- **Token Refresh**: Automatically refreshes expired Fitbit tokens
- **Error Handling**: Graceful handling of missing or incomplete data

## Privacy

- All sensitive data is stored in GitHub Secrets
- Personal health data is never committed to the repository
- Fitbit tokens are automatically refreshed when needed

## Troubleshooting

1. **Missing Data**: Check if your Fitbit device is syncing properly
2. **Token Errors**: Re-run the OAuth flow with `oauth_helper.py` and update GitHub Secrets
3. **Notion Errors**: Verify database ID and integration permissions
4. **Scheduling Issues**: GitHub Actions may have delays during peak times

## License

MIT License - See LICENSE file for details