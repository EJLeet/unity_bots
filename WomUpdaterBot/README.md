# WiseOldMan Auto-Update Discord Bot

A Discord bot that automatically updates all members in a WiseOldMan group using their API, with scheduled daily updates and manual trigger capabilities.

## Features

- **Automated Updates**: Runs daily at midnight AEST
- **Manual Triggers**: `/update` command for on-demand updates
- **Status Monitoring**: `/status` command to check bot and group status
- **Error Handling**: Comprehensive logging and Discord notifications
- **Railway Deployment**: Ready for cloud hosting

## Setup Instructions

### 1. Discord Bot Setup
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application named "WOM Updater Bot"
3. Go to "Bot" section and create a bot
4. Copy the bot token (you'll need this for environment variables)
5. Enable "Message Content Intent" in bot settings
6. Go to "OAuth2" → "URL Generator"
7. Select "bot" scope and "Send Messages", "Use Slash Commands" permissions
8. Use the generated URL to invite bot to your server

### 2. Environment Configuration
1. Copy `.env.example` to `.env`
2. Fill in your values:
   ```env
   DISCORD_TOKEN=your_discord_bot_token_here
   GUILD_ID=your_discord_server_id_here
   WOM_API_KEY=1234567
   WOM_GROUP_ID=4104
   UPDATE_CHANNEL_ID=your_channel_id_here
   LOG_LEVEL=INFO
   TIMEZONE=Australia/Sydney
   ```

### 3. Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# check the api lookup function i think its updateall()

# Run the bot
python bot/main.py
```

### 4. Railway Deployment
1. Connect your repository to Railway
2. Set environment variables in Railway dashboard
3. Deploy automatically via git push

## Commands

- `/update` - Manually trigger WiseOldMan group update
- `/status` - Check bot status and WiseOldMan group info

## Configuration

- **WOM_API_KEY**: Your WiseOldMan API key (currently: 1234567)
- **WOM_GROUP_ID**: Your WiseOldMan group ID (currently: 4104)
- **UPDATE_CHANNEL_ID**: Discord channel ID for updates and logs
- **TIMEZONE**: Timezone for scheduling (default: Australia/Sydney)

## Architecture

```
WomUpdaterBot/
├── bot/
│   ├── main.py              # Main bot client
│   ├── commands/
│   │   └── update.py        # Slash commands
│   ├── services/
│   │   ├── wiseoldman.py    # WOM API integration
│   │   └── scheduler.py     # Task scheduling
│   └── utils/
│       └── logger.py        # Logging configuration
├── requirements.txt         # Python dependencies
├── Procfile                # Railway deployment
├── .env.example            # Environment template
└── README.md               # This file
```

## Monitoring

The bot provides comprehensive logging and sends important messages to the configured Discord channel:

- Startup/shutdown notifications
- Successful/failed updates
- Error messages and warnings
- Status information

## Support

If you encounter issues:
1. Check the logs in your Discord channel
2. Use `/status` command to verify connectivity
3. Ensure all environment variables are set correctly
4. Verify WiseOldMan API key and group ID are valid