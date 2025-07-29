import discord
from discord.ext import commands
from discord import app_commands
import logging
from typing import List
from config.config import Config
from utils.database import db

logger = logging.getLogger(__name__)

class PreApplicationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        
    @discord.ui.button(label='Yes', style=discord.ButtonStyle.green, custom_id='pre_app_yes')
    async def pre_app_yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ApplicationModal())
        
    @discord.ui.button(label='No', style=discord.ButtonStyle.red, custom_id='pre_app_no')
    async def pre_app_no(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="❌ Application Error",
            description="Please apply in game before filling out this application.",
            color=discord.Color.red()
        )
        
        if Config.PRE_APPLICATION_IMAGE_URL:
            embed.set_image(url=Config.PRE_APPLICATION_IMAGE_URL)
            
        await interaction.response.send_message(embed=embed, view=PreApplicationView(), ephemeral=True)

class ApplicationModal(discord.ui.Modal, title='Clan Application Form'):
    def __init__(self):
        super().__init__(timeout=300)
        
    in_game_name = discord.ui.TextInput(
        label='In Game Name',
        placeholder='Enter your in-game name...',
        required=True,
        max_length=100
    )
    
    total_level = discord.ui.TextInput(
        label='Total Level',
        placeholder='Enter your total level...',
        required=True,
        max_length=20
    )
    
    how_found_us = discord.ui.TextInput(
        label='How did you find us?',
        placeholder='Tell us how you discovered our clan...',
        required=True,
        style=discord.TextStyle.paragraph,
        max_length=500
    )
    
    read_rules = discord.ui.TextInput(
        label='Have you read the rules?',
        placeholder='Please confirm you have read our rules...',
        required=True,
        max_length=200
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        user_data = {
            'in_game_name': self.in_game_name.value,
            'total_level': self.total_level.value,
            'how_found_us': self.how_found_us.value,
            'read_rules': self.read_rules.value,
            'discord_id': interaction.user.id,
            'step': 'rank_selection'
        }
        
        db.set_user_data(interaction.user.id, user_data)
        
        embed = discord.Embed(
            title="📋 Select Your Rank",
            description="Please select the rank you're applying for:",
            color=discord.Color.blue()
        )
        
        await interaction.response.send_message(embed=embed, view=RankSelectionView(), ephemeral=True)

class RankSelectionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        
    @discord.ui.button(label='Unholy', style=discord.ButtonStyle.primary, custom_id='rank_unholy')
    async def select_unholy(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_rank_selection(interaction, 'unholy')
        
    @discord.ui.button(label='Friend', style=discord.ButtonStyle.secondary, custom_id='rank_friend')
    async def select_friend(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_rank_selection(interaction, 'friend')
        
    async def _handle_rank_selection(self, interaction: discord.Interaction, rank: str):
        user_data = db.get_user_data(interaction.user.id)
        if not user_data:
            await interaction.response.send_message("❌ Application data not found. Please start over.", ephemeral=True)
            return
            
        db.update_user_data(interaction.user.id, {'rank': rank, 'step': 'alts_question'})
        
        embed = discord.Embed(
            title="🔄 Add Alts?",
            description="Do you want to add any alt accounts?",
            color=discord.Color.blue()
        )
        
        await interaction.response.send_message(embed=embed, view=AltsQuestionView(), ephemeral=True)

class AltsQuestionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        
    @discord.ui.button(label='Yes, Add Alts', style=discord.ButtonStyle.green, custom_id='add_alts_yes')
    async def add_alts_yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AltsModal())
        
    @discord.ui.button(label='No Alts', style=discord.ButtonStyle.red, custom_id='add_alts_no')
    async def add_alts_no(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_data = db.get_user_data(interaction.user.id)
        if not user_data:
            await interaction.response.send_message("❌ Application data not found. Please start over.", ephemeral=True)
            return
            
        db.update_user_data(interaction.user.id, {'alts': [], 'step': 'final_review'})
        await self._show_final_review(interaction)
        
    async def _show_final_review(self, interaction: discord.Interaction):
        user_data = db.get_user_data(interaction.user.id)
        
        embed = discord.Embed(
            title="📋 Review Your Application",
            description="Please review your application details:",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="In Game Name", value=user_data.get('in_game_name', 'N/A'), inline=True)
        embed.add_field(name="Total Level", value=user_data.get('total_level', 'N/A'), inline=True)
        embed.add_field(name="Rank", value=user_data.get('rank', 'N/A').title(), inline=True)
        embed.add_field(name="How Found Us", value=user_data.get('how_found_us', 'N/A'), inline=False)
        embed.add_field(name="Read Rules", value=user_data.get('read_rules', 'N/A'), inline=False)
        
        alts = user_data.get('alts', [])
        if alts:
            embed.add_field(name="Alts", value=', '.join(alts), inline=False)
        else:
            embed.add_field(name="Alts", value="None", inline=False)
            
        await interaction.response.send_message(embed=embed, view=FinalSubmissionView(), ephemeral=True)

class AltsModal(discord.ui.Modal, title='Add Alt Account'):
    def __init__(self):
        super().__init__(timeout=300)
        
    alt_name = discord.ui.TextInput(
        label='Alt In-Game Name',
        placeholder='Enter your alt account name...',
        required=True,
        max_length=100
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        user_data = db.get_user_data(interaction.user.id)
        if not user_data:
            await interaction.response.send_message("❌ Application data not found. Please start over.", ephemeral=True)
            return
            
        alts = user_data.get('alts', [])
        alts.append(self.alt_name.value)
        db.update_user_data(interaction.user.id, {'alts': alts})
        
        embed = discord.Embed(
            title="✅ Alt Added",
            description=f"Added: **{self.alt_name.value}**\n\nWould you like to add another alt?",
            color=discord.Color.green()
        )
        
        current_alts = ', '.join(alts)
        embed.add_field(name="Current Alts", value=current_alts, inline=False)
        
        await interaction.response.send_message(embed=embed, view=AddMoreAltsView(), ephemeral=True)

class AddMoreAltsView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        
    @discord.ui.button(label='Add Another Alt', style=discord.ButtonStyle.green, custom_id='add_more_alts')
    async def add_more_alts(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AltsModal())
        
    @discord.ui.button(label='Continue to Review', style=discord.ButtonStyle.primary, custom_id='continue_review')
    async def continue_review(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_data = db.get_user_data(interaction.user.id)
        
        embed = discord.Embed(
            title="📋 Review Your Application",
            description="Please review your application details:",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="In Game Name", value=user_data.get('in_game_name', 'N/A'), inline=True)
        embed.add_field(name="Total Level", value=user_data.get('total_level', 'N/A'), inline=True)
        embed.add_field(name="Rank", value=user_data.get('rank', 'N/A').title(), inline=True)
        embed.add_field(name="How Found Us", value=user_data.get('how_found_us', 'N/A'), inline=False)
        embed.add_field(name="Read Rules", value=user_data.get('read_rules', 'N/A'), inline=False)
        
        alts = user_data.get('alts', [])
        if alts:
            embed.add_field(name="Alts", value=', '.join(alts), inline=False)
        else:
            embed.add_field(name="Alts", value="None", inline=False)
            
        await interaction.response.send_message(embed=embed, view=FinalSubmissionView(), ephemeral=True)

class FinalSubmissionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        
    @discord.ui.button(label='Submit Application', style=discord.ButtonStyle.green, custom_id='submit_final')
    async def submit_application(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_data = db.get_user_data(interaction.user.id)
        if not user_data:
            await interaction.response.send_message("❌ Application data not found. Please start over.", ephemeral=True)
            return
            
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("❌ This command must be used in a server.", ephemeral=True)
            return
            
        try:
            pending_role = guild.get_role(Config.APPLICATION_PENDING_ROLE_ID)
            if pending_role:
                await interaction.user.add_roles(pending_role)
                
            try:
                dm_embed = discord.Embed(
                    title="✅ Application Submitted",
                    description="Thank you for applying, a mod will review your application as soon as possible. If you have any questions, please #make-a-ticket",
                    color=discord.Color.green()
                )
                await interaction.user.send(embed=dm_embed)
            except discord.Forbidden:
                logger.warning(f"Could not send DM to {interaction.user}")
                
            pending_channel = guild.get_channel(Config.APPLICATIONS_PENDING_CHANNEL_ID)
            if pending_channel:
                from cogs.moderation import create_pending_application_embed
                embed, view = create_pending_application_embed(user_data)
                await pending_channel.send(embed=embed, view=view)
                
            db.delete_user_data(interaction.user.id)
            
            await interaction.response.send_message("✅ Application submitted successfully!", ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error submitting application: {e}")
            await interaction.response.send_message("❌ An error occurred while submitting your application. Please try again.", ephemeral=True)

class InitialApplicationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        
    @discord.ui.button(label='Apply', style=discord.ButtonStyle.green, custom_id='start_application')
    async def start_application(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="📋 Before You Apply",
            description="**Have you applied in game?**\n\nPlease make sure you have submitted an in-game application before proceeding with this Discord application.",
            color=discord.Color.blue()
        )
        
        if Config.PRE_APPLICATION_IMAGE_URL:
            embed.set_image(url=Config.PRE_APPLICATION_IMAGE_URL)
            
        await interaction.response.send_message(embed=embed, view=PreApplicationView(), ephemeral=True)
        
    @discord.ui.button(label='Welcome', style=discord.ButtonStyle.secondary, custom_id='go_to_welcome')
    async def go_to_welcome(self, interaction: discord.Interaction, button: discord.ui.Button):
        welcome_channel = interaction.guild.get_channel(Config.WELCOME_CHANNEL_ID)
        if welcome_channel:
            await interaction.response.send_message(f"👋 Welcome! Please check out {welcome_channel.mention}", ephemeral=True)
        else:
            await interaction.response.send_message("👋 Welcome to the server!", ephemeral=True)

class ApplicationsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    async def cog_load(self):
        await db.start_cleanup_task()
        
    async def cog_unload(self):
        await db.stop_cleanup_task()
        
    @app_commands.command(name="setup_applications", description="Setup the application system in the current channel")
    @app_commands.default_permissions(administrator=True)
    async def setup_applications(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🏰 Aus Unity Applications",
            description="Welcome to Aus Unity! Click the buttons below to get started.",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="📝 Apply",
            value="Click to start your clan application process",
            inline=True
        )
        
        embed.add_field(
            name="👋 Welcome",
            value="New to the server? Check out our welcome channel",
            inline=True
        )
        
        view = InitialApplicationView()
        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(ApplicationsCog(bot))