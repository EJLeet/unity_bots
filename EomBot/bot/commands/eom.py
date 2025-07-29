import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
import asyncio
from datetime import datetime

from config.config import Config
from services.message_parser import MessageParser
from services.sheets_manager import SheetsManager
from services.rank_manager import RankManager
from services.wiseoldman_api import get_wise_old_man_summary
from utils.logger import get_logger, log_command_usage, log_error_with_context, log_achievement_parsing, log_rank_promotions
from utils.validators import validate_month, validate_channel_restriction, validate_user_permissions, validate_guild_setup, validate_bot_permissions

class EOMCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = get_logger()
        
        # Initialize services
        self.sheets_manager = None
        self.message_parser = None
        self.rank_manager = None
        
        # Initialize services after bot is ready
        bot.loop.create_task(self._initialize_services())
    
    async def _initialize_services(self):
        await self.bot.wait_until_ready()
        
        try:
            self.sheets_manager = SheetsManager()
            self.message_parser = MessageParser(self.bot)
            self.rank_manager = RankManager(self.bot, self.sheets_manager)
            self.logger.info("EOM services initialized successfully")
        except Exception as e:
            log_error_with_context(e, "service_initialization")
            raise
    
    @app_commands.command(name="eombot", description="Process end-of-month achievements and rank promotions")
    @app_commands.describe(month="The month to process (e.g., 'January' or 'Jan')")
    async def eombot_command(self, interaction: discord.Interaction, month: str):
        await interaction.response.defer(thinking=True)
        
        try:
            # Log command usage
            log_command_usage(
                interaction.user.id,
                str(interaction.user),
                f"eombot {month}",
                interaction.guild.id,
                interaction.guild.name
            )
            
            # Validate services are initialized
            if not all([self.sheets_manager, self.message_parser, self.rank_manager]):
                await interaction.followup.send("❌ Bot services are still initializing. Please try again in a few moments.")
                return
            
            # Validate month parameter
            is_valid_month, month_error = validate_month(month)
            if not is_valid_month:
                await interaction.followup.send(f"❌ {month_error}")
                return
            
            # Validate channel restriction
            is_valid_channel, channel_error = validate_channel_restriction(interaction.channel)
            if not is_valid_channel:
                await interaction.followup.send(f"❌ {channel_error}")
                return
            
            # Validate user permissions
            is_authorized, auth_error = validate_user_permissions(interaction.user)
            if not is_authorized:
                await interaction.followup.send(f"❌ {auth_error}")
                return
            
            # Validate guild setup
            is_setup_valid, setup_errors = validate_guild_setup(interaction.guild)
            if not is_setup_valid:
                error_list = "\n".join([f"• {error}" for error in setup_errors])
                await interaction.followup.send(f"❌ **Guild Setup Issues:**\n{error_list}")
                return
            
            # Validate bot permissions
            bot_member = interaction.guild.get_member(self.bot.user.id)
            has_perms, perm_errors = validate_bot_permissions(interaction.guild, bot_member)
            if not has_perms:
                error_list = "\n".join([f"• {error}" for error in perm_errors])
                await interaction.followup.send(f"❌ **Bot Permission Issues:**\n{error_list}")
                return
            
            # Start processing
            await interaction.followup.send(f"🔄 Processing {month.title()} achievements and promotions...")
            
            # Step 1: Parse achievements
            self.logger.info(f"Starting achievement parsing for {month}")
            achievements = await self.message_parser.parse_monthly_achievements(month.lower())
            
            if not achievements:
                await interaction.followup.send(f"ℹ️ No achievements found for {month.title()}.")
                return
            
            log_achievement_parsing(
                month,
                len(achievements),
                sum(len(member_data['achievements']) for member_data in achievements.values())
            )
            
            # Step 2: Process rank promotions
            self.logger.info("Processing rank promotions")
            members_with_achievements = list(achievements.keys())
            promotions = await self.rank_manager.process_rank_promotions(
                members_with_achievements,
                interaction.guild
            )
            
            log_rank_promotions(promotions)
            
            # Step 3: Get Wise Old Man monthly gains
            self.logger.info("Fetching Wise Old Man monthly gains")
            try:
                wom_summary = await get_wise_old_man_summary(limit=3)
            except Exception as e:
                self.logger.error(f"Failed to fetch Wise Old Man gains: {e}")
                wom_summary = "⚠️ Unable to fetch Wise Old Man gains data."
            
            # Step 4: Create and send summary
            await self._send_completion_summary(
                interaction,
                month.title(),
                achievements,
                promotions,
                wom_summary
            )
            
            self.logger.info(f"EOM processing completed for {month}")
            
        except Exception as e:
            log_error_with_context(
                e,
                "eombot_command",
                month=month,
                user=str(interaction.user),
                guild=str(interaction.guild)
            )
            
            try:
                await interaction.followup.send(
                    "❌ An error occurred while processing the command. Please check the logs and try again."
                )
            except:
                pass  # Interaction might have expired
    
    async def _send_completion_summary(self, interaction: discord.Interaction, 
                                     month: str, achievements: dict, promotions: dict, wom_summary: str = ""):
        try:
            # Create achievement summary
            achievement_summary = self.message_parser.get_achievement_summary(achievements)
            
            # Create promotion summary
            promotion_summary = self.rank_manager.get_promotion_summary(promotions)
            
            # Combine summaries
            full_summary = f"✅ **{month} EOM Processing Complete**\n\n"
            full_summary += f"{achievement_summary}\n\n"
            
            # Add Wise Old Man summary if available
            if wom_summary and wom_summary.strip():
                full_summary += f"{wom_summary}\n\n"
            
            full_summary += f"{promotion_summary}"
            
            # Split message if too long
            if len(full_summary) <= 2000:
                await interaction.followup.send(full_summary)
            else:
                # Send in parts
                parts = self._split_message(full_summary)
                for i, part in enumerate(parts):
                    if i == 0:
                        await interaction.followup.send(part)
                    else:
                        await interaction.followup.send(part)
                        await asyncio.sleep(1)  # Brief delay between messages
        
        except Exception as e:
            log_error_with_context(e, "send_completion_summary")
            await interaction.followup.send("✅ Processing completed, but there was an error sending the summary.")
    
    def _split_message(self, message: str, max_length: int = 2000) -> list[str]:
        if len(message) <= max_length:
            return [message]
        
        parts = []
        current_part = ""
        
        for line in message.split('\n'):
            if len(current_part) + len(line) + 1 <= max_length:
                current_part += line + '\n'
            else:
                if current_part:
                    parts.append(current_part.rstrip())
                current_part = line + '\n'
        
        if current_part:
            parts.append(current_part.rstrip())
        
        return parts
    
    @eombot_command.error
    async def eombot_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(
                f"⏰ Command is on cooldown. Try again in {error.retry_after:.1f} seconds.",
                ephemeral=True
            )
        else:
            log_error_with_context(
                error,
                "eombot_command_error",
                user=str(interaction.user),
                guild=str(interaction.guild) if interaction.guild else "DM"
            )
            
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ An unexpected error occurred. Please try again later.",
                    ephemeral=True
                )
    
    # Debug/Admin commands (you can remove these in production)
    @app_commands.command(name="eom-status", description="Check EOMBot configuration status")
    @app_commands.default_permissions(manage_guild=True)
    async def status_command(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Check guild setup
            is_setup_valid, setup_errors = validate_guild_setup(interaction.guild)
            
            # Check bot permissions
            bot_member = interaction.guild.get_member(self.bot.user.id)
            has_perms, perm_errors = validate_bot_permissions(interaction.guild, bot_member)
            
            # Check services
            services_status = {
                'Sheets Manager': self.sheets_manager is not None,
                'Message Parser': self.message_parser is not None,
                'Rank Manager': self.rank_manager is not None
            }
            
            # Create status message
            status_msg = "🔍 **EOMBot Status Check**\n\n"
            
            # Services status
            status_msg += "**Services:**\n"
            for service, status in services_status.items():
                emoji = "✅" if status else "❌"
                status_msg += f"{emoji} {service}\n"
            
            # Guild setup status
            status_msg += f"\n**Guild Setup:** {'✅ Valid' if is_setup_valid else '❌ Issues Found'}\n"
            if setup_errors:
                for error in setup_errors[:5]:  # Limit to first 5 errors
                    status_msg += f"  • {error}\n"
            
            # Bot permissions status
            status_msg += f"\n**Bot Permissions:** {'✅ Valid' if has_perms else '❌ Issues Found'}\n"
            if perm_errors:
                for error in perm_errors[:5]:  # Limit to first 5 errors
                    status_msg += f"  • {error}\n"
            
            await interaction.followup.send(status_msg)
            
        except Exception as e:
            log_error_with_context(e, "status_command")
            await interaction.followup.send("❌ Error checking status. Check logs for details.")

async def setup(bot: commands.Bot):
    await bot.add_cog(EOMCog(bot))