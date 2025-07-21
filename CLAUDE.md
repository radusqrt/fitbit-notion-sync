# Claude Development Notes

This project was developed with assistance from Claude Code. Here are some key technical decisions and development notes for future reference.

## Architecture Decisions

### Data Source: Fitbit Web API vs Health Connect
- **Chosen**: Fitbit Web API (Server application type)
- **Reasoning**: Platform-agnostic, comprehensive data access, supports intraday metrics
- **Alternative**: Android Health Connect was considered but limited to on-device data

### Automation Platform: GitHub Actions
- **Chosen**: GitHub Actions with cron scheduling
- **Reasoning**: Free, reliable, integrated with git workflow, built-in secrets management
- **Schedule**: `0 7 * * *` (7 AM UTC = 9 AM Zurich summer time)
- **Alternatives**: AWS Lambda, Google Cloud Functions were considered but added complexity

### Programming Language: Python
- **Libraries**: `requests`, `python-dotenv`, `notion-client`
- **Reasoning**: Simple, excellent API libraries, minimal dependencies
- **Alternative**: Node.js was considered but Python was simpler for this use case

## Technical Challenges Solved

### Sleep Data Format Compatibility
**Problem**: Fitbit API returns different formats for sleep data
- **New format**: `levels.summary` with detailed deep/light/REM stages
- **Old format**: `minuteData` with numeric codes (1=asleep, 2=restless, 3=awake)

**Solution**: Implemented dual format parser in `get_fitbit_data()`:
```python
if levels:
    # New format with detailed stages
    data['deep_sleep'] = levels.get('deep', {}).get('minutes', 0)
else:
    # Old format - parse minuteData
    asleep_minutes = sum(1 for m in minute_data if m.get('value') == '1')
    data['light_sleep'] = asleep_minutes
```

### Main Sleep vs Naps
**Problem**: API returns multiple sleep sessions (main sleep + naps)
**Solution**: Prioritize `isMainSleep: true` sessions for daily metrics

### Notion Database Schema Management
**Problem**: Database columns had wrong types (Date vs Text for sleep times)
**Solution**: Used Notion API to programmatically update schema:
```python
notion.databases.update(
    database_id=database_id,
    properties={
        "Sleep Start": {"type": "rich_text", "rich_text": {}}
    }
)
```

### Token Management
**Problem**: Fitbit OAuth tokens expire regularly
**Solution**: Implemented automatic token refresh in sync script with `.env` file updates

## Development Process

### Initial Setup
1. Created Fitbit Developer application (Server type for intraday access)
2. Built OAuth flow helper script for initial token acquisition
3. Set up Notion integration and database structure
4. Implemented basic sync script with core metrics

### Iterative Enhancement
1. **Basic sync** → Steps and resting heart rate only
2. **Comprehensive metrics** → Added all activity, sleep, and heart rate zones
3. **Schema fixes** → Automated database column type corrections
4. **Sleep data debugging** → Fixed format compatibility issues
5. **Data accuracy** → Prioritized main sleep over naps

### Error Handling Strategy
- Graceful handling of missing data (optional properties)
- API error logging with descriptive messages
- Token refresh on authentication failures
- Fallback values for missing metrics

## Security Considerations

### Secrets Management
- All API keys stored in GitHub Secrets
- Local `.env` file for development (gitignored)
- No hardcoded credentials in source code

### Data Privacy
- Personal health data CSV files accidentally committed, then removed from git history
- Added `*.csv` to gitignore to prevent future data leaks
- Used `git filter-branch` to completely remove sensitive data from commit history

### API Permissions
- Fitbit: Read-only access to health data
- Notion: Edit access to specific database only
- Minimal required scopes for each service

## Future Improvements

### Potential Enhancements
1. **Timezone handling**: More robust timezone conversion for international users
2. **Data validation**: Add validation for unrealistic health metrics
3. **Retry logic**: Implement exponential backoff for API failures
4. **Historical sync**: Option to backfill missing days
5. **Multiple databases**: Support for different Notion workspaces

### Monitoring
- Consider adding health checks or notification on sync failures
- Log analysis for performance optimization
- Token expiration alerts

## Lessons Learned

1. **API Documentation**: Fitbit API docs don't clearly explain format differences between devices
2. **Real Data Testing**: Always test with actual user data, not just documentation examples
3. **Schema Evolution**: Database schemas change over time, build flexibility early
4. **Git Security**: Be extra careful with personal data in version control
5. **Error Messages**: Good error messages save significant debugging time

## Dependencies

### Core Libraries
- `requests==2.32.4` - HTTP client for API calls
- `python-dotenv==1.1.1` - Environment variable management
- `notion-client==2.4.0` - Official Notion API client

### Development Tools
- GitHub Actions for CI/CD and scheduling
- git for version control with security considerations

## Usage Commands

```bash
# Setup virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Initial OAuth flow
python oauth_helper.py

# Run sync manually
python sync_fitbit_notion.py

# Debug sleep data
python debug_sleep_data.py
```

---

*This file serves as technical documentation for future development and maintenance of the Fitbit-Notion sync automation.*