import discord
from discord.ext import commands
import asyncio
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AusUnityBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            case_insensitive=True,
            help_command=None
        )
        
    async def setup_hook(self):
        logger.info("Setting up bot...")
        
        try:
            await self.load_extension('cogs.applications')
            logger.info("Loaded applications cog")
        except Exception as e:
            logger.error(f"Failed to load applications cog: {e}")
            
        try:
            await self.load_extension('cogs.moderation')
            logger.info("Loaded moderation cog")
        except Exception as e:
            logger.error(f"Failed to load moderation cog: {e}")
            
        await self.tree.sync()
        logger.info("Command tree synced")
        
    async def on_ready(self):
        logger.info(f'{self.user} has connected to Discord!')
        logger.info(f'Bot is in {len(self.guilds)} guilds')
        
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="for clan applications"
        )
        await self.change_presence(activity=activity)
        
    async def on_error(self, event, *args, **kwargs):
        logger.error(f'An error occurred in {event}: {args}, {kwargs}', exc_info=True)
        
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to use this command.")
        else:
            logger.error(f'Command error: {error}', exc_info=True)
            await ctx.send("An error occurred while processing the command.")

async def main():
    bot = AusUnityBot()
    
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error("DISCORD_TOKEN not found in environment variables")
        return
        
    try:
        await bot.start(token)
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested")
        await bot.close()
    except Exception as e:
        logger.error(f"Bot encountered an error: {e}", exc_info=True)
        await bot.close()

if __name__ == "__main__":
    asyncio.run(main())