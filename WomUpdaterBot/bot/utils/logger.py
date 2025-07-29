import logging
import os
from typing import Optional
import discord

class DiscordLogHandler(logging.Handler):
    """Custom log handler that sends messages to a Discord channel"""
    
    def __init__(self, bot: Optional[discord.Client] = None, channel_id: Optional[int] = None):
        super().__init__()
        self.bot = bot
        self.channel_id = channel_id
        self.channel = None
        
    def set_bot(self, bot: discord.Client, channel_id: Optional[int] = None):
        """Set the bot instance after initialization"""
        self.bot = bot
        if channel_id:
            self.channel_id = channel_id
        
    def emit(self, record: logging.LogRecord):
        """Send log message to Discord channel"""
        if not self.bot or not self.bot.is_ready():
            return
            
        try:
            # Get the channel if not cached
            if not self.channel and self.channel_id:
                self.channel = self.bot.get_channel(self.channel_id)
            
            if self.channel and record.levelno >= logging.WARNING:
                # Only send WARNING and above to Discord
                message = self.format(record)
                # Truncate long messages
                if len(message) > 2000:
                    message = message[:1997] + "..."
                
                # Use asyncio to send message
                import asyncio
                asyncio.create_task(self.channel.send(f"```\n{message}\n```"))
                
        except Exception:
            # Don't let logging errors crash the bot
            pass

def setup_logger(name: str = "wom_bot", level: str = "INFO") -> logging.Logger:
    """Setup logger with console and optional Discord handlers"""
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Discord handler (will be configured later when bot is ready)
    discord_handler = DiscordLogHandler()
    discord_formatter = logging.Formatter(
        '[%(levelname)s] %(asctime)s - %(message)s'
    )
    discord_handler.setFormatter(discord_formatter)
    logger.addHandler(discord_handler)
    
    return logger

def get_discord_handler(logger: logging.Logger) -> Optional[DiscordLogHandler]:
    """Get the Discord handler from logger"""
    for handler in logger.handlers:
        if isinstance(handler, DiscordLogHandler):
            return handler
    return None