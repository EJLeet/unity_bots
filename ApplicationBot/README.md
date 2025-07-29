# Aus Unity Applications Discord Bot

A comprehensive Discord bot for managing clan applications with Google Sheets integration and Railway deployment support.

## Features

- **Interactive Application System**: Multi-step application process with Discord modals and buttons
- **Pre-Application Screening**: Ensures users have applied in-game before Discord application
- **Role Management**: Automatic role assignment for pending applications and approvals
- **Google Sheets Integration**: Automatic data entry and Discord ID conflict detection
- **Moderation Workflow**: Easy approve/deny system with reason collection
- **24/7 Hosting**: Ready for Railway deployment with proper configuration

## Project Structure

```
ApplicationBot/
├── bot/
│   ├── main.py              # Bot entry point
│   ├── cogs/
│   │   ├── applications.py  # Application flow handlers
│   │   └── moderation.py    # Moderation workflow
│   ├── utils/
│   │   ├── sheets.py        # Google Sheets integration
│   │   └── database.py      # In-memory storage
│   ├── config/
│   │   ├── config.py        # Configuration management
│   │   └── permissions.py   # Discord permissions
│   └── assets/              # Static files and images
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
├── service_account.json.example  # Google service account template
├── Procfile                # Railway deployment
├── runtime.txt             # Python version
└── README.md               # This file
```

## Prerequisites

1. **Python 3.11+**
2. **Discord Developer Account**
3. **Google Cloud Project with Sheets API enabled**
4. **Railway Account** (for deployment)

## Setup Instructions

### 1. Discord Bot Setup

1. **Create Discord Application:**
   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Click "New Application" and name it "Aus Unity Applications"
   - Go to "Bot" section and click "Add Bot"
   - Copy the bot token (you'll need this for `.env`)

2. **Set Bot Permissions:**
   - In Bot section, enable these Privileged Gateway Intents:
     - ✅ Server Members Intent
     - ✅ Message Content Intent
   - In OAuth2 > URL Generator:
     - Scopes: `bot`, `applications.commands`
     - Bot Permissions:
       - Manage Roles
       - Send Messages
       - Use Slash Commands
       - Read Message History
       - Embed Links
       - Attach Files

3. **Invite Bot to Server:**
   - Use the generated OAuth2 URL to invite the bot
   - Ensure bot role is positioned above the roles it needs to manage

### 2. Google Sheets Setup

1. **Create Google Cloud Project:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable Google Sheets API and Google Drive API

2. **Create Service Account:**
   - Go to IAM & Admin > Service Accounts
   - Click "Create Service Account"
   - Name it "discord-bot-sheets"
   - Click "Create and Continue"
   - Skip role assignment (click "Continue")
   - Click "Done"

3. **Generate Service Account Key:**
   - Click on your service account
   - Go to "Keys" tab
   - Click "Add Key" > "Create New Key"
   - Choose JSON format
   - Download the file and rename it to `service_account.json`
   - Place it in the ApplicationBot root directory

4. **Setup Google Sheet:**
   - Create a new Google Sheet for your clan data
   - Set up headers in first row: `Name`, `Rank`, `Total`, `Alts`, `Discord ID`
   - Share the sheet with your service account email (found in the JSON file)
   - Give it "Editor" permissions
   - Copy the Sheet ID from the URL (between `/d/` and `/edit`)

### 3. Google Drive Image Setup

1. **Upload Pre-Application Image:**
   - Upload your image to Google Drive
   - Right-click the image and select "Get link"
   - Change permissions to "Anyone with the link can view"
   - Copy the link

2. **Convert Link Format:**
   - Original: `https://drive.google.com/file/d/FILE_ID/view?usp=sharing`
   - Discord format: `https://drive.google.com/uc?export=view&id=FILE_ID`
   - Replace `FILE_ID` with the actual ID from your link

### 4. Discord Server Configuration

1. **Create Required Channels:**
   - `#applications` - Where users start applications
   - `#applications-pending` - Where moderators review applications  
   - `#applications-accepted` - Where accepted applications are posted
   - `#mod-review` - Where duplicate Discord IDs are flagged
   - `#welcome` - Welcome channel for new users (optional)

2. **Create Required Roles:**
   - `application-pending` - Assigned during application process
   - `unholy` - For unholy rank applications
   - `friend` - For friend rank applications  
   - `application-deny` - For denied applications

3. **Get Channel and Role IDs:**
   - Enable Developer Mode in Discord (User Settings > Advanced)
   - Right-click channels/roles and "Copy ID"

### 5. Environment Configuration

1. **Copy Environment Template:**
   ```bash
   cp .env.example .env
   ```

2. **Fill in Your Values:**
   ```env
   # Discord Bot Configuration
   DISCORD_TOKEN=your_discord_bot_token

   # Google Sheets Configuration  
   GOOGLE_SHEETS_ID=your_google_sheets_id

   # Discord Channel IDs
   APPLICATIONS_CHANNEL_ID=123456789012345678
   APPLICATIONS_PENDING_CHANNEL_ID=123456789012345678
   APPLICATIONS_ACCEPTED_CHANNEL_ID=123456789012345678
   WELCOME_CHANNEL_ID=123456789012345678
   MOD_REVIEW_CHANNEL_ID=123456789012345678

   # Discord Role IDs
   APPLICATION_PENDING_ROLE_ID=123456789012345678
   UNHOLY_ROLE_ID=123456789012345678
   FRIEND_ROLE_ID=123456789012345678
   APPLICATION_DENY_ROLE_ID=123456789012345678

   # Google Drive Image URLs
   PRE_APPLICATION_IMAGE_URL=https://drive.google.com/uc?export=view&id=YOUR_FILE_ID
   ```

### 6. Local Testing

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Bot:**
   ```bash
   cd bot
   python main.py
   ```

3. **Test Setup Commands:**
   - Use `/setup_applications` in your applications channel
   - Use `/test_sheets` to verify Google Sheets connection
   - Try the application flow with a test user

### 7. Railway Deployment

1. **Prepare for Deployment:**
   - Ensure all files are in place
   - Verify `.gitignore` excludes sensitive files
   - Test locally first

2. **Deploy to Railway:**
   - Connect your GitHub repository to Railway
   - Railway will auto-detect Python and use `Procfile`
   - Set environment variables in Railway dashboard
   - Upload `service_account.json` content as environment variable:
     ```
     GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}
     ```

3. **Update Sheets Integration for Railway:**
   - Modify `utils/sheets.py` to use environment variable instead of file:
   ```python
   import json
   credentials_info = json.loads(os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON'))
   credentials = Credentials.from_service_account_info(credentials_info, scopes=scope)
   ```

## Usage

### For Server Admins

1. **Setup the Bot:**
   ```
   /setup_applications
   ```
   Run this in your applications channel to create the initial interface.

2. **Test Google Sheets:**
   ```
   /test_sheets
   ```
   Verify your Google Sheets connection is working.

3. **Search Discord IDs:**
   ```
   /search_discord_id <discord_id>
   ```
   Search for existing entries in your spreadsheet.

### For Users

1. **Start Application:**
   - Click "Apply" button in applications channel
   - Answer in-game application question
   - Fill out the application form
   - Add alt accounts if desired
   - Submit application

2. **Application Process:**
   - Receives "application-pending" role
   - Gets confirmation DM
   - Waits for moderator review

### For Moderators

1. **Review Applications:**
   - Check applications-pending channel
   - Click "Accept - Unholy", "Accept - Friend", or "Deny"
   - For denials, provide a reason

2. **Monitor Duplicates:**
   - Check mod-review channel for duplicate Discord IDs
   - Handle conflicts manually if needed

## Security Notes

- Never commit `.env` or `service_account.json` files
- Use Railway's environment variables for sensitive data
- Regularly rotate Discord bot token and Google service account keys
- Monitor bot permissions and limit access to admin commands

## Troubleshooting

### Common Issues

1. **Bot Not Responding:**
   - Check bot permissions in server
   - Verify bot token in environment variables
   - Check Railway logs for errors

2. **Google Sheets Errors:**
   - Verify service account has access to sheet
   - Check Google Sheets API is enabled
   - Confirm Sheet ID is correct

3. **Role Assignment Issues:**
   - Ensure bot role is above target roles
   - Verify role IDs in environment variables
   - Check bot has "Manage Roles" permission

4. **Railway Deployment Issues:**
   - Verify `Procfile` and `runtime.txt` are correct
   - Check all environment variables are set
   - Monitor Railway deployment logs

### Support

If you encounter issues:
1. Check Railway deployment logs
2. Test locally first to isolate the problem  
3. Verify all environment variables are correctly set
4. Ensure all Discord permissions are properly configured

## Version Information

- **Discord.py:** 2.5.2
- **Python:** 3.11+  
- **Google Sheets API:** v4
- **Deployment:** Railway optimized

---

Built for Aus Unity Clan Management 🏰