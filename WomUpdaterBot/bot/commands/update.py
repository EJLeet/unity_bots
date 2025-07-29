import discord
from discord.ext import commands
import logging
from bot.services.wiseoldman import WiseOldManAPI

class UpdateCommands(commands.Cog):
    """Commands for WiseOldMan updates"""
    
    def __init__(self, bot: commands.Bot, wom_api: WiseOldManAPI):
        self.bot = bot
        self.wom_api = wom_api
        self.logger = logging.getLogger("wom_bot.commands")
    
    @discord.app_commands.command(name="update", description="Manually trigger WiseOldMan group update")
    async def manual_update(self, interaction: discord.Interaction):
        """Manual trigger for WiseOldMan group update"""
        
        # Defer response since API call might take time
        await interaction.response.defer()
        
        self.logger.info(f"Manual update triggered by {interaction.user.name}")
        
        try:
            # Call WiseOldMan API
            result = await self.wom_api.update_all_members()
            
            if result["success"]:
                embed = discord.Embed(
                    title="✅ Update Successful",
                    description="WiseOldMan group update has been triggered successfully!",
                    color=0x00FF00
                )
                embed.add_field(
                    name="Group ID", 
                    value=self.wom_api.group_id, 
                    inline=True
                )
                embed.add_field(
                    name="Triggered by", 
                    value=interaction.user.mention, 
                    inline=True
                )
                embed.timestamp = discord.utils.utcnow()
                
                self.logger.info("Manual update completed successfully")
                
            else:
                embed = discord.Embed(
                    title="❌ Update Failed",
                    description=f"Failed to trigger WiseOldMan update: {result['message']}",
                    color=0xFF0000
                )
                embed.add_field(
                    name="Error Details", 
                    value=result.get('error', 'Unknown error'), 
                    inline=False
                )
                embed.timestamp = discord.utils.utcnow()
                
                self.logger.error(f"Manual update failed: {result['message']}")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            error_msg = f"Unexpected error during manual update: {str(e)}"
            self.logger.error(error_msg)
            
            embed = discord.Embed(
                title="❌ Update Error",
                description="An unexpected error occurred during the update.",
                color=0xFF0000
            )
            embed.add_field(
                name="Error", 
                value=str(e), 
                inline=False
            )
            embed.timestamp = discord.utils.utcnow()
            
            await interaction.followup.send(embed=embed)
    
    @discord.app_commands.command(name="status", description="Check bot and WiseOldMan group status")
    async def check_status(self, interaction: discord.Interaction):
        """Check bot status and WiseOldMan group info"""
        
        await interaction.response.defer()
        
        try:
            # Get group info from WiseOldMan API
            group_info = await self.wom_api.get_group_info()
            
            embed = discord.Embed(
                title="🤖 Bot Status",
                color=0x0099FF
            )
            
            # Bot status
            embed.add_field(
                name="Bot Status",
                value="✅ Online and Ready",
                inline=True
            )
            
            embed.add_field(
                name="Guilds Connected",
                value=len(self.bot.guilds),
                inline=True
            )
            
            # WiseOldMan group status
            if group_info["success"]:
                group_data = group_info["data"]
                embed.add_field(
                    name="WOM Group",
                    value=f"✅ {group_data.get('name', 'Unknown')}",
                    inline=True
                )
                embed.add_field(
                    name="Group ID",
                    value=self.wom_api.group_id,
                    inline=True
                )
                embed.add_field(
                    name="Member Count",
                    value=group_data.get('memberCount', 'Unknown'),
                    inline=True
                )
            else:
                embed.add_field(
                    name="WOM Group",
                    value="❌ Connection Failed",
                    inline=True
                )
            
            embed.timestamp = discord.utils.utcnow()
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            self.logger.error(f"Error checking status: {str(e)}")
            
            embed = discord.Embed(
                title="❌ Status Check Failed",
                description=f"Error checking status: {str(e)}",
                color=0xFF0000
            )
            
            await interaction.followup.send(embed=embed)

async def setup(bot: commands.Bot, wom_api: WiseOldManAPI):
    """Setup function to add the cog"""
    await bot.add_cog(UpdateCommands(bot, wom_api))