import os
import asyncio
from datetime import time
from dotenv import load_dotenv
import discord
from discord.ext import commands

from bot.services.wiseoldman import WiseOldManAPI
from bot.services.scheduler import TaskScheduler
from bot.utils.logger import setup_logger, get_discord_handler
from bot.commands.update import setup as setup_update_commands

# Load environment variables
load_dotenv()

class WOMUpdateBot(commands.Bot):
    """WiseOldMan Auto-Update Discord Bot"""
    
    def __init__(self):
        # Bot configuration
        intents = discord.Intents.default()
        intents.message_content = True
        
        super().__init__(
            command_prefix='!',  # Fallback prefix, we'll use slash commands
            intents=intents,
            help_command=None
        )
        
        # Setup logging
        self.logger = setup_logger(
            name="wom_bot",
            level=os.getenv("LOG_LEVEL", "INFO")
        )
        
        # Initialize services
        self.wom_api = WiseOldManAPI(
            api_key=os.getenv("WOM_API_KEY"),
            group_id=os.getenv("WOM_GROUP_ID")
        )
        
        self.scheduler = TaskScheduler(
            timezone=os.getenv("TIMEZONE", "Australia/Sydney")
        )
        
        self.update_channel_id = os.getenv("UPDATE_CHANNEL_ID")
        self.update_channel = None
        
    async def setup_hook(self):
        """Setup hook called when bot is starting"""
        self.logger.info("Setting up WOM Update Bot...")
        
        # Setup commands
        await setup_update_commands(self, self.wom_api)
        
        # Sync slash commands
        try:
            guild_id = os.getenv("GUILD_ID")
            if guild_id:
                guild = discord.Object(id=int(guild_id))
                self.tree.copy_global_to(guild=guild)
                await self.tree.sync(guild=guild)
                self.logger.info(f"Synced commands to guild {guild_id}")
            else:
                await self.tree.sync()
                self.logger.info("Synced commands globally")
        except Exception as e:
            self.logger.error(f"Failed to sync commands: {e}")
    
    async def on_ready(self):
        """Called when bot is ready"""
        self.logger.info(f"Bot logged in as {self.user.name} (ID: {self.user.id})")
        
        # Find update channel by ID
        if self.update_channel_id:
            self.update_channel = self.get_channel(int(self.update_channel_id))
            if self.update_channel:
                self.logger.info(f"Found update channel: #{self.update_channel.name} (ID: {self.update_channel_id})")
            else:
                self.logger.warning(f"Update channel with ID {self.update_channel_id} not found")
        else:
            self.logger.warning("UPDATE_CHANNEL_ID not set in environment variables")
        
        # Setup Discord logging handler
        discord_handler = get_discord_handler(self.logger)
        if discord_handler and self.update_channel_id:
            discord_handler.set_bot(self, int(self.update_channel_id))
        
        # Send startup message
        if self.update_channel:
            embed = discord.Embed(
                title="🤖 WOM Update Bot Started",
                description="Bot is online and ready to handle WiseOldMan updates!",
                color=0x00FF00
            )
            embed.add_field(
                name="Scheduled Updates",
                value="Daily at 12:00 AM AEST",
                inline=True
            )
            embed.add_field(
                name="Manual Commands",
                value="/update - Manual update\n/status - Check status",
                inline=True
            )
            embed.timestamp = discord.utils.utcnow()
            
            await self.update_channel.send(embed=embed)
        
        # Start scheduler and schedule midnight updates
        self.scheduler.start_scheduler()
        midnight = time(hour=0, minute=0)  # 12:00 AM
        await self.scheduler.schedule_daily_task(
            "midnight_update",
            midnight,
            self.scheduled_update
        )
        
        self.logger.info("WOM Update Bot is fully ready!")
    
    async def on_command_error(self, ctx, error):
        """Handle command errors"""
        self.logger.error(f"Command error: {error}")
        
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore unknown commands
        
        # Send error to update channel if available
        if self.update_channel:
            embed = discord.Embed(
                title="❌ Command Error",
                description=str(error),
                color=0xFF0000
            )
            await self.update_channel.send(embed=embed)
    
    def get_channel_by_id(self, channel_id: int):
        """Get channel by ID - more reliable than name lookup"""
        return self.get_channel(channel_id)
    
    async def scheduled_update(self):
        """Perform scheduled WiseOldMan update"""
        self.logger.info("Starting scheduled WiseOldMan update")
        
        try:
            result = await self.wom_api.update_all_members()
            
            if self.update_channel:
                if result["success"]:
                    embed = discord.Embed(
                        title="✅ Scheduled Update Complete",
                        description="Daily WiseOldMan group update completed successfully!",
                        color=0x00FF00
                    )
                    embed.add_field(
                        name="Update Time",
                        value="12:00 AM AEST (Scheduled)",
                        inline=True
                    )
                    embed.add_field(
                        name="Group ID",
                        value=self.wom_api.group_id,
                        inline=True
                    )
                else:
                    embed = discord.Embed(
                        title="❌ Scheduled Update Failed",
                        description=f"Daily update failed: {result['message']}",
                        color=0xFF0000
                    )
                    embed.add_field(
                        name="Error Details",
                        value=result.get('error', 'Unknown error'),
                        inline=False
                    )
                
                embed.timestamp = discord.utils.utcnow()
                await self.update_channel.send(embed=embed)
            
            self.logger.info("Scheduled update completed")
            
        except Exception as e:
            error_msg = f"Error during scheduled update: {str(e)}"
            self.logger.error(error_msg)
            
            if self.update_channel:
                embed = discord.Embed(
                    title="❌ Scheduled Update Error",
                    description="An error occurred during the scheduled update.",
                    color=0xFF0000
                )
                embed.add_field(
                    name="Error",
                    value=str(e),
                    inline=False
                )
                embed.timestamp = discord.utils.utcnow()
                await self.update_channel.send(embed=embed)
    
    async def close(self):
        """Cleanup when bot is shutting down"""
        self.logger.info("Shutting down WOM Update Bot...")
        await self.scheduler.stop_scheduler()
        await super().close()

async def main():
    """Main function to run the bot"""
    bot = WOMUpdateBot()
    
    try:
        token = os.getenv("DISCORD_TOKEN")
        if not token:
            raise ValueError("DISCORD_TOKEN environment variable is required")
        
        await bot.start(token)
    except KeyboardInterrupt:
        bot.logger.info("Bot shutdown requested by user")
    except Exception as e:
        bot.logger.error(f"Fatal error: {e}")
    finally:
        if not bot.is_closed():
            await bot.close()

if __name__ == "__main__":
    asyncio.run(main())