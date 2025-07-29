import discord
from discord.ext import commands
from discord import app_commands
import logging
from typing import Dict, Any, Tuple
from config.config import Config
from utils.sheets import sheets_manager

logger = logging.getLogger(__name__)

def create_pending_application_embed(user_data: Dict[str, Any]) -> Tuple[discord.Embed, discord.ui.View]:
    embed = discord.Embed(
        title="📋 New Application Pending Review",
        color=discord.Color.orange()
    )
    
    embed.add_field(name="Discord User", value=f"<@{user_data.get('discord_id')}>", inline=True)
    embed.add_field(name="Discord ID", value=str(user_data.get('discord_id')), inline=True)
    embed.add_field(name="In Game Name", value=user_data.get('in_game_name', 'N/A'), inline=True)
    embed.add_field(name="Total Level", value=user_data.get('total_level', 'N/A'), inline=True)
    embed.add_field(name="Rank Applied For", value=user_data.get('rank', 'N/A').title(), inline=True)
    embed.add_field(name="How Found Us", value=user_data.get('how_found_us', 'N/A'), inline=False)
    embed.add_field(name="Read Rules", value=user_data.get('read_rules', 'N/A'), inline=False)
    
    alts = user_data.get('alts', [])
    if alts:
        embed.add_field(name="Alts", value=', '.join(alts), inline=False)
    else:
        embed.add_field(name="Alts", value="None", inline=False)
    
    view = ApplicationReviewView(user_data)
    return embed, view

class DenyReasonModal(discord.ui.Modal, title='Denial Reason'):
    def __init__(self, user_data: Dict[str, Any]):
        super().__init__(timeout=300)
        self.user_data = user_data
        
    reason = discord.ui.TextInput(
        label='Reason for Denial',
        placeholder='Enter the reason for denying this application...',
        required=True,
        style=discord.TextStyle.paragraph,
        max_length=1000
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            guild = interaction.guild
            user_id = self.user_data.get('discord_id')
            user = guild.get_member(user_id)
            
            if user:
                pending_role = guild.get_role(Config.APPLICATION_PENDING_ROLE_ID)
                deny_role = guild.get_role(Config.APPLICATION_DENY_ROLE_ID)
                
                if pending_role and pending_role in user.roles:
                    await user.remove_roles(pending_role)
                    
                if deny_role:
                    await user.add_roles(deny_role)
                
                try:
                    dm_embed = discord.Embed(
                        title="❌ Application Denied",
                        description=f"Sorry, your application has been denied for this reason: {self.reason.value}",
                        color=discord.Color.red()
                    )
                    await user.send(embed=dm_embed)
                except discord.Forbidden:
                    logger.warning(f"Could not send denial DM to user {user_id}")
                    
            embed = discord.Embed(
                title="❌ Application Denied",
                description=f"Application denied by {interaction.user.mention}",
                color=discord.Color.red()
            )
            embed.add_field(name="Applicant", value=f"<@{user_id}>", inline=True)
            embed.add_field(name="Reason", value=self.reason.value, inline=False)
            
            await interaction.response.edit_message(embed=embed, view=None)
            
        except Exception as e:
            logger.error(f"Error processing denial: {e}")
            await interaction.response.send_message("❌ An error occurred while processing the denial.", ephemeral=True)

class ApplicationReviewView(discord.ui.View):
    def __init__(self, user_data: Dict[str, Any]):
        super().__init__(timeout=None)
        self.user_data = user_data
        
    @discord.ui.button(label='Accept - Unholy', style=discord.ButtonStyle.green, custom_id='accept_unholy')
    async def accept_unholy(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_acceptance(interaction, 'unholy')
        
    @discord.ui.button(label='Accept - Friend', style=discord.ButtonStyle.green, custom_id='accept_friend')
    async def accept_friend(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_acceptance(interaction, 'friend')
        
    @discord.ui.button(label='Deny', style=discord.ButtonStyle.red, custom_id='deny_application')
    async def deny_application(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(DenyReasonModal(self.user_data))
        
    async def _handle_acceptance(self, interaction: discord.Interaction, accepted_rank: str):
        try:
            guild = interaction.guild
            user_id = self.user_data.get('discord_id')
            user = guild.get_member(user_id)
            
            if not user:
                await interaction.response.send_message("❌ User not found in server.", ephemeral=True)
                return
                
            pending_role = guild.get_role(Config.APPLICATION_PENDING_ROLE_ID)
            if pending_role and pending_role in user.roles:
                await user.remove_roles(pending_role)
                
            if accepted_rank == 'unholy':
                target_role = guild.get_role(Config.UNHOLY_ROLE_ID)
            else:  # friend
                target_role = guild.get_role(Config.FRIEND_ROLE_ID)
                
            if target_role:
                await user.add_roles(target_role)
                
            accepted_channel = guild.get_channel(Config.APPLICATIONS_ACCEPTED_CHANNEL_ID)
            if accepted_channel:
                accept_embed = discord.Embed(
                    title="✅ Application Accepted",
                    description=f"Welcome to the clan, {user.mention}!",
                    color=discord.Color.green()
                )
                accept_embed.add_field(name="Rank", value=accepted_rank.title(), inline=True)
                accept_embed.add_field(name="Discord ID", value=str(user_id), inline=True)
                accept_embed.add_field(name="In Game Name", value=self.user_data.get('in_game_name', 'N/A'), inline=True)
                
                await accepted_channel.send(embed=accept_embed)
                
            existing_entry = sheets_manager.search_discord_id(str(user_id))
            
            if existing_entry:
                mod_review_channel = guild.get_channel(Config.MOD_REVIEW_CHANNEL_ID)
                if mod_review_channel:
                    review_embed = discord.Embed(
                        title="⚠️ Duplicate Discord ID Found",
                        description=f"User <@{user_id}> already exists in the spreadsheet.",
                        color=discord.Color.yellow()
                    )
                    review_embed.add_field(name="New Application Data", value="", inline=False)
                    review_embed.add_field(name="In Game Name", value=self.user_data.get('in_game_name', 'N/A'), inline=True)
                    review_embed.add_field(name="Total Level", value=self.user_data.get('total_level', 'N/A'), inline=True)
                    review_embed.add_field(name="Rank", value=accepted_rank.title(), inline=True)
                    
                    alts = self.user_data.get('alts', [])
                    if alts:
                        review_embed.add_field(name="Alts", value=', '.join(alts), inline=False)
                        
                    review_embed.add_field(name="Existing Entry", value="", inline=False)
                    review_embed.add_field(name="Worksheet", value=existing_entry['worksheet'], inline=True)
                    review_embed.add_field(name="Row", value=str(existing_entry['row']), inline=True)
                    review_embed.add_field(name="Discord ID", value=str(user_id), inline=False)
                    
                    await mod_review_channel.send(embed=review_embed)
            else:
                application_data = {
                    'in_game_name': self.user_data.get('in_game_name'),
                    'rank': accepted_rank,
                    'total_level': self.user_data.get('total_level'),
                    'alts': self.user_data.get('alts', []),
                    'discord_id': user_id
                }
                
                success = sheets_manager.add_new_entry(application_data)
                if not success:
                    logger.error(f"Failed to add user {user_id} to Google Sheets")
                    
            embed = discord.Embed(
                title="✅ Application Accepted",
                description=f"Application accepted by {interaction.user.mention}",
                color=discord.Color.green()
            )
            embed.add_field(name="Applicant", value=f"<@{user_id}>", inline=True)
            embed.add_field(name="Rank", value=accepted_rank.title(), inline=True)
            embed.add_field(name="In Game Name", value=self.user_data.get('in_game_name', 'N/A'), inline=True)
            
            await interaction.response.edit_message(embed=embed, view=None)
            
        except Exception as e:
            logger.error(f"Error processing acceptance: {e}")
            await interaction.response.send_message("❌ An error occurred while processing the acceptance.", ephemeral=True)

class ModerationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @app_commands.command(name="test_sheets", description="Test Google Sheets connection")
    @app_commands.default_permissions(administrator=True)
    async def test_sheets(self, interaction: discord.Interaction):
        try:
            if sheets_manager.test_connection():
                embed = discord.Embed(
                    title="✅ Sheets Connection Test",
                    description="Successfully connected to Google Sheets!",
                    color=discord.Color.green()
                )
                
                headers = sheets_manager.get_worksheet_headers()
                if headers:
                    embed.add_field(name="Headers Found", value=', '.join(headers), inline=False)
                    
            else:
                embed = discord.Embed(
                    title="❌ Sheets Connection Test",
                    description="Failed to connect to Google Sheets. Check your configuration.",
                    color=discord.Color.red()
                )
                
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Sheets Connection Test",
                description=f"Error: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
    @app_commands.command(name="search_discord_id", description="Search for a Discord ID in the spreadsheet")
    @app_commands.default_permissions(administrator=True)
    async def search_discord_id(self, interaction: discord.Interaction, discord_id: str):
        try:
            result = sheets_manager.search_discord_id(discord_id)
            
            if result:
                embed = discord.Embed(
                    title="✅ Discord ID Found",
                    description=f"Found Discord ID `{discord_id}` in the spreadsheet",
                    color=discord.Color.green()
                )
                embed.add_field(name="Worksheet", value=result['worksheet'], inline=True)
                embed.add_field(name="Row", value=str(result['row']), inline=True)
                embed.add_field(name="Data", value=str(result['data']), inline=False)
            else:
                embed = discord.Embed(
                    title="❌ Discord ID Not Found",
                    description=f"Discord ID `{discord_id}` was not found in any worksheet",
                    color=discord.Color.red()
                )
                
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Search Error",
                description=f"Error searching for Discord ID: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(ModerationCog(bot))