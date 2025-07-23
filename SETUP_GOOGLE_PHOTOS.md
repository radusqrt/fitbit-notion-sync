# Google Photos Food Tracking Setup Guide

This guide will help you set up the Google Photos food tracking integration with your existing Fitbit-Notion sync system.

## Prerequisites

1. **Existing Setup**: Your Fitbit-Notion sync should already be working
2. **Google Account**: Access to Google Photos with food pictures
3. **OpenAI API Key**: For food recognition (alternatively, could use Google Vision API)

## Step 1: Install New Dependencies

```bash
pip install -r requirements.txt
```

The following new packages will be installed:
- `google-auth==2.29.0`
- `google-auth-oauthlib==1.2.0` 
- `google-api-python-client==2.137.0`
- `google-generativeai==0.8.3`

## Step 2: Set up Google Photos API

### 2.1 Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the **Photos Library API**

### 2.2 Create OAuth 2.0 Credentials
1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth 2.0 Client IDs**
3. Choose **Web application**
4. Add authorized redirect URI: `http://localhost:8080`
5. Download the credentials JSON or copy Client ID and Client Secret

### 2.3 Get Gemini API Key
1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click **Create API Key**
3. Copy the generated API key

### 2.4 Add Credentials to .env File
Add these lines to your `.env` file:

```bash
# Google Photos API credentials
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here

# Gemini API key for food recognition
GOOGLE_API_KEY=your_gemini_api_key_here
```

## Step 3: Initial OAuth Setup

Run the OAuth helper to get your initial tokens:

```bash
python google_photos_oauth.py
```

This will:
1. Open a browser window for Google authentication
2. Ask you to authorize access to your Google Photos
3. Save the access and refresh tokens to your `.env` file

## Step 4: Update Notion Database Schema

Run the schema update script to add food tracking columns:

```bash
python update_notion_schema.py
```

This adds these columns to your Notion database:
- **Breakfast** (Rich Text)
- **Lunch** (Rich Text) 
- **Dinner** (Rich Text)
- **Food Photos Processed** (Checkbox)

## Step 5: Test the Integration

Test the food photo processing:

```bash
python google_photos_food.py
```

This will process yesterday's photos and show you what foods were detected.

## Step 6: Run Full Sync

Your regular sync now includes Google Photos:

```bash
python sync_fitbit_notion.py
```

The sync will now:
1. ✅ Fetch Fitbit health data
2. 🆕 Process Google Photos for food pictures
3. 🆕 Classify photos by meal time (breakfast/lunch/dinner)
4. 🆕 Use AI to describe the food in each photo
5. ✅ Update Notion with all data

## How It Works

### Meal Time Classification
Photos are classified into meals based on when they were taken:
- **Breakfast**: 6:00 AM - 11:00 AM
- **Lunch**: 11:00 AM - 4:00 PM
- **Dinner**: 5:00 PM - 11:00 PM

### Food Recognition
The system uses **Gemini 2.0 Flash** (state-of-the-art multimodal AI) to:
1. Analyze photos with advanced visual understanding
2. Identify and describe food in natural language
3. Understand context (restaurant vs home cooking, meal types)
4. Generate rich descriptions like "Homemade pasta with marinara sauce and fresh basil"

### Privacy & Security
- Photos are only accessed via Google Photos API (no downloads stored)
- Images are analyzed using Gemini AI (Google's secure platform)
- Temporary image files are immediately deleted after analysis
- All credentials stored securely in `.env` file
- No permanent storage of personal photos

## Troubleshooting

### Common Issues

**"Missing Google OAuth credentials"**
- Check your `.env` file has `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`
- Ensure you've run `python google_photos_oauth.py`

**"Photos Library API not enabled"**
- Go to Google Cloud Console and enable the Photos Library API
- Wait a few minutes for the API to be activated

**"GOOGLE_API_KEY not found"**
- Get a Gemini API key from Google AI Studio: https://aistudio.google.com/app/apikey
- Add `GOOGLE_API_KEY=your_key_here` to your .env file

**"Token expired" errors**
- The system automatically refreshes tokens
- If it fails, run `python google_photos_oauth.py` again

**"No food photos found"**
- Check that you have photos in Google Photos for the target date
- Verify photos were taken during meal times (6 AM - 11 PM)
- The AI might not recognize some food photos (check logs)

### GitHub Actions Integration

To run this in GitHub Actions, add these secrets:
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET` 
- `GOOGLE_ACCESS_TOKEN`
- `GOOGLE_REFRESH_TOKEN`
- `GOOGLE_API_KEY`

The existing workflow will automatically use the food integration.

## Customization

### Meal Time Windows
Edit the `classify_meal_time()` function in `google_photos_food.py`:

```python
# Current windows
if 6 <= hour < 11:
    return 'breakfast'
elif 11 <= hour < 16:
    return 'lunch'
elif 17 <= hour < 23:
    return 'dinner'
```

### Gemini Prompt Customization
Modify the prompt in `analyze_food_image()` for different analysis styles:

```python
prompt = """Analyze this image and provide detailed nutritional information if it contains food.
Include estimated calories and main ingredients."""
```

### Alternative AI Models
You could replace Gemini with other multimodal models like GPT-4 Vision, Claude, or local models.

## Cost Considerations

- **Google Photos API**: Free (10,000 requests/day)
- **Gemini 2.0 Flash**: Free (15 requests/minute, 1,500/day)
- **Daily cost estimate**: $0 (3 photos/day = 90/month, well under free limit)

## Next Steps

Consider these enhancements:
1. **Nutritional analysis**: Ask AI for calories/macros estimation
2. **Meal tagging**: Add location, restaurant, or cuisine tags
3. **Recipe extraction**: Identify specific dishes or recipes
4. **Portion size**: Estimate serving sizes from photos
5. **Multiple formats**: Support for Instagram, camera roll sync