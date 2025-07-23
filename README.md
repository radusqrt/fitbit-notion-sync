# Fitbit to Notion Sync with AI Food Tracking

Automated daily sync of Fitbit health data and AI-powered food photo analysis to a Notion database using GitHub Actions.

## Features

### 🏃‍♂️ **Fitbit Health Data**
- **Automated Daily Sync**: Runs every day at 9 AM Zurich time
- **Manual Backfill**: Fill in missing historical data for any date range
- **Comprehensive Health Metrics**:
  - Activity: Steps, distance, calories, active minutes
  - Sleep: Total hours, efficiency, start/end times, sleep stages (deep/light/REM)
  - Heart Rate: Resting HR, fat burn/cardio/peak zones
  - HRV: Daily and deep sleep heart rate variability
  - Body: Weight, BMI, body fat percentage (if available)

### 🍽️ **AI Food Photo Tracking**
- **Google Drive Integration**: Upload food photos to your designated Drive folder
- **Original Timestamp Extraction**: Uses EXIF data to get when photos were actually taken
- **Smart Meal Classification**: Automatically categorizes by time (breakfast/lunch/dinner)
- **AI Food Recognition**: Gemini 2.0 Flash provides concise food descriptions
- **Manual Sync Option**: On-demand processing via GitHub Actions

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

### 3. Google Drive & AI Setup
1. **Google Cloud Console**: Enable Drive API at https://console.cloud.google.com/
2. **Create OAuth credentials** for your application
3. **Create Drive folder** for food photos
4. **Get Gemini API key** from https://aistudio.google.com/app/apikey

### 4. Get OAuth Tokens
Run the OAuth helper to get your personal access tokens:
```bash
python oauth_helper.py  # For Fitbit
python setup_drive_oauth.py  # For Google Drive (if needed)
```

### 5. GitHub Secrets Setup
**Required for automation:** Copy values from your `.env` file to GitHub Secrets.

Go to your repository → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

**Fitbit & Notion:**
- `FITBIT_CLIENT_ID` - Your Fitbit app Client ID
- `FITBIT_CLIENT_SECRET` - Your Fitbit app Client Secret  
- `FITBIT_ACCESS_TOKEN` - Generated from OAuth flow
- `FITBIT_REFRESH_TOKEN` - Generated from OAuth flow
- `NOTION_TOKEN` - Your Notion integration token
- `NOTION_DATABASE_ID` - Your Notion database ID (from database URL)

**Google Drive & AI:**
- `GOOGLE_CLIENT_ID` - Your Google Cloud OAuth Client ID
- `GOOGLE_CLIENT_SECRET` - Your Google Cloud OAuth Client Secret
- `GOOGLE_ACCESS_TOKEN` - Generated from Drive OAuth flow
- `GOOGLE_API_KEY` - Your Gemini API key

### 6. Notion Database Schema
Run the schema updater to add food tracking columns:
```bash
python update_notion_schema.py
```

**Health Metrics Columns:**
- Date (Date)
- Steps, Distance (km), Calories, Active Minutes (Numbers)
- Sleep Hours, Sleep Efficiency, Deep/Light/REM Sleep (Numbers)
- Sleep Start, Sleep End (Text)
- Wake Resting HR, Fat Burn/Cardio/Peak Zone minutes (Numbers)
- HRV Daily/Deep RMSSD, Weight, BMI, Body Fat % (Numbers)

**Food Tracking Columns:**
- Breakfast, Lunch, Dinner (Rich Text)
- Food Photos Processed (Checkbox)

## Usage

### 🔄 **Automatic Daily Sync**
The workflow runs automatically every day at 9 AM Zurich time via GitHub Actions, processing:
- Yesterday's Fitbit health data
- Food photos uploaded to your Drive folder

### 🍽️ **Food Photo Workflow**
1. **Take photos** of your meals during the day
2. **Upload to Drive folder** each evening
3. **Automatic processing** next morning extracts:
   - Original photo timestamps (when you took the photo)
   - AI food descriptions (e.g. "latte", "fried eggs with tomatoes")
   - Meal classification (breakfast/lunch/dinner based on photo time)

### 🛠️ **Manual Operations**

**Manual Sync (including today's data):**
```bash
# Local manual sync
python manual_sync_today.py

# Or use GitHub Actions:
# Go to Actions → "Manual Sync Today's Data" → Run workflow
```

**Fitbit-only sync:**
```bash
python sync_fitbit_notion.py
```

**Historical backfill:**
```bash
python backfill_fitbit_data.py --start-date 2025-07-01 --end-date 2025-07-10
```

## Files

**Core Scripts:**
- `sync_fitbit_notion.py` - Main daily sync script (Fitbit + food photos)
- `google_drive_food.py` - Google Drive food photo processing with AI
- `manual_sync_today.py` - Manual sync for current day testing
- `backfill_fitbit_data.py` - Historical Fitbit data backfill
- `update_notion_schema.py` - Add food tracking columns to Notion

**GitHub Actions:**
- `.github/workflows/sync-health-data.yml` - Daily automated sync
- `.github/workflows/manual-sync-today.yml` - On-demand manual sync
- `.github/workflows/manual-backfill.yml` - Historical data backfill

## AI Food Recognition

- **Powered by**: Gemini 2.0 Flash (state-of-the-art multimodal AI)
- **Output**: Concise food descriptions ("latte", "pizza", "fried eggs with tomatoes")
- **Cost**: Free (up to 1,500 requests/day)
- **Privacy**: Images analyzed via Google's secure platform

## Privacy & Security

- **GitHub Secrets**: All API keys stored securely
- **No data retention**: Personal health data never committed to repository
- **Temporary processing**: Food photos downloaded temporarily for AI analysis only
- **Original timestamps**: System preserves when photos were actually taken

## Troubleshooting

1. **Missing Fitbit Data**: Check device sync and token expiration
2. **Food Photos Not Found**: Verify Drive folder permissions and API enablement
3. **Token Errors**: Re-run OAuth flows and update GitHub Secrets
4. **Notion Errors**: Check database ID and integration permissions
5. **AI Analysis Issues**: Verify Gemini API key and request limits

## License

MIT License - See LICENSE file for details