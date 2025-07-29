import discord
from discord.ext import commands
import asyncio
import sys
import os

# Add the bot directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.config import Config
from utils.logger import setup_logger, get_logger, log_error_with_context
from commands.eom import EOMCog

class EOMBot(commands.Bot):
    def __init__(self):
        # Set up intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True
        
        super().__init__(
            command_prefix='!',  # Fallback prefix (we'll use slash commands)
            intents=intents,
            help_command=None
        )
        
        # Set up logging
        self.logger = setup_logger('eombot', 'INFO')
        
    async def setup_hook(self):
        try:
            # Validate configuration
            Config.validate_config()
            self.logger.info("Configuration validated successfully")
            
            # Add cogs
            await self.add_cog(EOMCog(self))
            self.logger.info("EOM cog loaded successfully")
            
            # Sync slash commands
            try:
                synced = await self.tree.sync()
                self.logger.info(f"Synced {len(synced)} command(s)")
            except Exception as e:
                self.logger.error(f"Failed to sync commands: {e}")
            
        except Exception as e:
            log_error_with_context(e, "setup_hook")
            raise
    
    async def on_ready(self):
        self.logger.info(f'{self.user} has connected to Discord!')
        self.logger.info(f'Bot is in {len(self.guilds)} guilds')
        
        # Set bot status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="for /eombot commands"
            )
        )
        
        # Log guild information
        for guild in self.guilds:
            self.logger.info(f'Connected to guild: {guild.name} (ID: {guild.id})')
    
    async def on_guild_join(self, guild):
        self.logger.info(f'Joined new guild: {guild.name} (ID: {guild.id})')
        
        # Try to sync commands for the new guild
        try:
            await self.tree.sync(guild=guild)
            self.logger.info(f'Synced commands for {guild.name}')
        except Exception as e:
            self.logger.error(f'Failed to sync commands for {guild.name}: {e}')
    
    async def on_guild_remove(self, guild):
        self.logger.info(f'Removed from guild: {guild.name} (ID: {guild.id})')
    
    async def on_error(self, event, *args, **kwargs):
        self.logger.error(f'Error in event {event}', exc_info=True)
    
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore command not found errors
        
        log_error_with_context(
            error, 
            "command_error",
            command=ctx.command.name if ctx.command else "unknown",
            user=str(ctx.author),
            guild=str(ctx.guild) if ctx.guild else "DM"
        )

async def main():
    # Initialize and run bot
    bot = EOMBot()
    
    try:
        await bot.start(Config.DISCORD_TOKEN)
    except KeyboardInterrupt:
        bot.logger.info("Bot shutdown requested by user")
    except Exception as e:
        bot.logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        await bot.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot shutdown completed")
    except Exception as e:
        print(f"Failed to start bot: {e}")
        sys.exit(1)