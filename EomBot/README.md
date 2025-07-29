# EOMBot (End of Month Bot)

A Discord bot that automates end-of-month achievement tracking and rank promotions for gaming communities. The bot parses achievement messages from Discord channels, cross-references with Google Sheets member data, and manages rank promotions automatically.

## Features

- 🎯 **Achievement Parsing**: Automatically parses messages from designated achievement channels
- 📊 **Google Sheets Integration**: Syncs with your member database for rank and counter management
- 🏆 **Automated Rank Promotions**: Promotes members based on configurable thresholds
- 📢 **Promotion Notifications**: Posts rank changes to a designated channel
- ⚙️ **Slash Commands**: Modern Discord slash command interface
- 🔒 **Permission System**: Configurable user permissions and channel restrictions
- 📝 **Comprehensive Logging**: Detailed logging for debugging and audit trails

## Bot Workflow

1. User executes `/eombot MONTH` in the designated EOM post channel
2. Bot searches achievement channels for messages from the specified month
3. Extracts member names and achievement details from messages
4. Cross-references member names with Google Sheets to get Discord IDs and current ranks
5. Processes rank promotions based on career counter and time-based criteria
6. Updates Google Sheets with new ranks and incremented career counters
7. Updates Discord roles for promoted members
8. Posts promotion notifications to the rank change channel
9. Sends a comprehensive summary to the command user

## Rank System

**Progression**: Mediator → Sage → Destroyer → Unholy → Legend

- **Mediator**: Time-based promotion (configurable days requirement)
- **Sage**: Career counter threshold-based (default: 5 achievements)
- **Destroyer**: Career counter threshold-based (default: 10 achievements)  
- **Unholy**: Career counter threshold-based (default: 15 achievements)
- **Legend**: Maximum rank (no further promotions)

## Setup Instructions

### 1. Discord Bot Creation

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give your bot a name (e.g., "EOMBot")
3. Go to the "Bot" section in the sidebar
4. Click "Add Bot" to create a bot user
5. Under the "Token" section, click "Copy" to get your bot token
6. Save this token securely - you'll need it for the `DISCORD_TOKEN` environment variable

#### Required Bot Permissions

Your bot needs these permissions:
- `Read Message History`
- `Send Messages`
- `Use Slash Commands`
- `Manage Roles`

#### Bot Invite Link

Generate an invite link with these permissions:
1. Go to the "OAuth2" → "URL Generator" section
2. Select scopes: `bot` and `applications.commands`
3. Select the permissions listed above
4. Use the generated URL to invite the bot to your server

### 2. Google Sheets API Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Sheets API:
   - Go to "APIs & Services" → "Library"
   - Search for "Google Sheets API" and enable it
4. Create service account credentials:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "Service Account"
   - Fill in the service account details
   - Click "Create and Continue"
   - Skip the optional steps and click "Done"
5. Generate a key for the service account:
   - Click on the created service account
   - Go to the "Keys" tab
   - Click "Add Key" → "Create New Key"
   - Choose "JSON" format and download the file
   - Rename the file to `service_account.json` and place it in your project root

#### Google Sheets Setup

1. Create a new Google Sheet or use an existing one
2. Set up columns as follows (or configure in .env):
   - Column A: Member Name
   - Column B: Discord ID
   - Column C: Current Rank
   - Column D: Career Counter
   - Column E: Added Date
3. Share the sheet with your service account:
   - Click "Share" in the top-right corner
   - Add the service account email (found in your JSON file)
   - Give it "Editor" permissions
4. Copy the Sheet ID from the URL (the long string between `/d/` and `/edit`)

### 3. Discord Channel Setup

Create or identify these channels in your Discord server:

- **#eom-post**: Where users can execute the `/eombot` command
- **#wise-old-man**: Achievement messages channel
- **#loot-notifications**: Loot notification messages channel
- **#log-notifications**: Log notification messages channel
- **#rank-change**: Where promotion notifications are posted

Get the channel IDs by:
1. Enable Developer Mode in Discord (User Settings → Advanced → Developer Mode)
2. Right-click each channel and select "Copy ID"

### 4. Discord Role Setup

Create or identify these roles in your Discord server:
- Mediator
- Sage
- Destroyer
- Unholy
- Legend

Get the role IDs by:
1. Enable Developer Mode in Discord
2. Go to Server Settings → Roles
3. Right-click each role and select "Copy ID"

### 5. Environment Configuration

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Fill in all the required values in `.env`:

```env
# Discord Configuration
DISCORD_TOKEN=your_actual_bot_token_here
EOM_POST_CHANNEL_ID=123456789012345678
WISE_OLD_MAN_CHANNEL_ID=123456789012345678
LOOT_NOTIFICATIONS_CHANNEL_ID=123456789012345678
LOG_NOTIFICATIONS_CHANNEL_ID=123456789012345678
RANK_CHANGE_CHANNEL_ID=123456789012345678

# Discord Role IDs
MEDIATOR_ROLE_ID=123456789012345678
SAGE_ROLE_ID=123456789012345678
DESTROYER_ROLE_ID=123456789012345678
UNHOLY_ROLE_ID=123456789012345678
LEGEND_ROLE_ID=123456789012345678

# Google Sheets Configuration
GOOGLE_SHEETS_CREDENTIALS_FILE=service_account.json
GOOGLE_SHEETS_ID=your_actual_sheet_id_here
MEMBER_NAME_COLUMN=A
DISCORD_ID_COLUMN=B
RANK_COLUMN=C
CAREER_COUNTER_COLUMN=D
ADDED_DATE_COLUMN=E

# Rank Promotion Thresholds (customize as needed)
SAGE_PROMOTION_THRESHOLD=5
DESTROYER_PROMOTION_THRESHOLD=10
UNHOLY_PROMOTION_THRESHOLD=15
MEDIATOR_TIME_REQUIREMENT_DAYS=30
```

## Local Development

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. Clone the repository or download the files
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up your `.env` file as described above
4. Place your `service_account.json` file in the project root
5. Run the bot:
   ```bash
   python bot/main.py
   ```

## Railway Deployment 

### Automatic Git Deployment

1. Create a [Railway](https://railway.app/) account
2. Connect your GitHub repository
3. Create a new project and select your repository
4. Railway will automatically detect the `Procfile` and deploy
5. Set up environment variables in Railway:
   - Go to your project dashboard
   - Click on "Variables"
   - Add all the environment variables from your `.env` file
   - Upload your `service_account.json` content as a variable or use Railway's file system

### Manual Deployment

1. Install Railway CLI:
   ```bash
   npm install -g @railway/cli
   ```
2. Login and link your project:
   ```bash
   railway login
   railway link
   ```
3. Set environment variables:
   ```bash
   railway variables set DISCORD_TOKEN=your_token_here
   # Add all other variables...
   ```
4. Deploy:
   ```bash
   railway up
   ```

## Usage

### Primary Command

- `/eombot <month>` - Process achievements and promotions for the specified month
  - Example: `/eombot January` or `/eombot Jan`
  - Restricted to the EOM post channel
  - Requires appropriate permissions

### Admin Commands

- `/eom-status` - Check bot configuration and status (requires Manage Server permission)

## Message Format Examples

The bot parses these message formats:

### Achievement Messages
```
NMZ WARRI0R - :defence: 99 Defence
PlayerName - :attack: 85 Attack  
```

### Loot/Log Notifications
```
OhYaPapi:

Doom of Mokhaiotl:
1 x Avernic treads
```

## Troubleshooting

### Common Issues

1. **"Bot services are still initializing"**
   - Wait a few moments after bot startup
   - Check logs for Google Sheets connection errors

2. **"No achievements found"**
   - Verify channel IDs are correct
   - Check bot has read message history permission in achievement channels
   - Ensure messages exist for the specified month

3. **"Guild Setup Issues"**
   - Verify all channel and role IDs in .env
   - Ensure channels and roles exist in the server

4. **Google Sheets errors**
   - Verify service account JSON file is correct
   - Check sheet is shared with service account email
   - Confirm sheet ID is correct

### Logging

Logs are saved to the `logs/` directory:
- `eombot_YYYY-MM-DD.log` - General activity logs
- `eombot_errors_YYYY-MM-DD.log` - Error logs only

### Permission Issues

Ensure the bot has these permissions in relevant channels:
- Read Message History (achievement channels)
- Send Messages (rank change channel, EOM post channel)
- Manage Roles (for rank promotions)
- Use Slash Commands (server-wide)

## Configuration Customization

### Promotion Thresholds

Adjust these values in your `.env` file:
- `SAGE_PROMOTION_THRESHOLD` - Career counter needed for Sage promotion
- `DESTROYER_PROMOTION_THRESHOLD` - Career counter needed for Destroyer promotion  
- `UNHOLY_PROMOTION_THRESHOLD` - Career counter needed for Unholy promotion
- `MEDIATOR_TIME_REQUIREMENT_DAYS` - Days required before Mediator promotion

### Google Sheets Columns

If your sheet has different column layouts, update these in `.env`:
- `MEMBER_NAME_COLUMN` - Column containing member names
- `DISCORD_ID_COLUMN` - Column containing Discord IDs
- `RANK_COLUMN` - Column containing current ranks
- `CAREER_COUNTER_COLUMN` - Column containing career counters
- `ADDED_DATE_COLUMN` - Column containing member join dates

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review the logs in the `logs/` directory
3. Verify all configuration values in `.env`
4. Ensure proper Discord and Google Sheets permissions

## Security Notes

- Never commit your `.env` file or `service_account.json` to version control
- Keep your Discord bot token secure
- Regularly rotate your Google service account keys
- Use appropriate Discord permissions to restrict bot usage