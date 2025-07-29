import discord
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from bot.config.config import Config
from bot.data.rank_data import RankData
from bot.services.sheets_manager import SheetsManager

logger = logging.getLogger(__name__)

class RankManager:
    def __init__(self, bot: discord.Client, sheets_manager: SheetsManager):
        self.bot = bot
        self.sheets_manager = sheets_manager
    
    async def process_rank_promotions(self, members_with_achievements: List[str], 
                                    guild: discord.Guild) -> Dict[str, str]:
        promotions = {}
        
        try:
            # Get all members from sheets
            all_members = self.sheets_manager.get_all_members()
            
            # Filter to only members who had achievements and are eligible for promotion
            eligible_members = []
            for member in all_members:
                if (member['name'] in members_with_achievements and 
                    RankData.is_promotable_rank(member['rank'])):
                    eligible_members.append(member)
            
            logger.info(f"Processing {len(eligible_members)} members for potential promotion")
            
            # Check each eligible member for promotion
            for member in eligible_members:
                promotion_result = await self._check_member_promotion(member, guild)
                if promotion_result:
                    old_rank, new_rank = promotion_result
                    promotions[member['name']] = {
                        'old_rank': old_rank,
                        'new_rank': new_rank,
                        'discord_id': member['discord_id']
                    }
            
            # Process the promotions in batch
            if promotions:
                await self._execute_promotions(promotions, guild)
            
            logger.info(f"Completed rank promotion processing. {len(promotions)} promotions made.")
            return promotions
            
        except Exception as e:
            logger.error(f"Failed to process rank promotions: {e}")
            return {}
    
    async def _check_member_promotion(self, member: Dict, guild: discord.Guild) -> Optional[Tuple[str, str]]:
        current_rank = member['rank']
        career_counter = member['career_counter']
        added_date_str = member['added_date']
        
        try:
            # Check if member is eligible for promotion
            if not RankData.is_promotable_rank(current_rank):
                return None
            
            next_rank = RankData.get_next_rank(current_rank)
            if not next_rank:
                return None
            
            # Handle time-based promotion (Mediator)
            if RankData.is_time_based_promotion(current_rank):
                if self._check_time_based_promotion(added_date_str, current_rank):
                    logger.info(f"{member['name']}: Time-based promotion {current_rank} -> {next_rank}")
                    return current_rank, next_rank
            
            # Handle career counter-based promotion
            else:
                threshold = RankData.get_promotion_threshold(next_rank)
                if career_counter >= threshold:
                    logger.info(f"{member['name']}: Counter-based promotion {current_rank} -> {next_rank} ({career_counter} >= {threshold})")
                    return current_rank, next_rank
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking promotion for {member['name']}: {e}")
            return None
    
    def _check_time_based_promotion(self, added_date_str: str, current_rank: str) -> bool:
        try:
            # Parse the added date (assuming format like "2023-01-15" or similar)
            # You may need to adjust the date format based on your sheet format
            if not added_date_str:
                logger.warning("No added date found for time-based promotion check")
                return False
            
            # Try different date formats
            date_formats = ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S']
            added_date = None
            
            for fmt in date_formats:
                try:
                    added_date = datetime.strptime(added_date_str, fmt)
                    break
                except ValueError:
                    continue
            
            if not added_date:
                logger.warning(f"Could not parse date: {added_date_str}")
                return False
            
            # Calculate days since added
            days_since_added = (datetime.now() - added_date).days
            required_days = RankData.get_time_requirement(current_rank)
            
            return days_since_added >= required_days
            
        except Exception as e:
            logger.error(f"Error in time-based promotion check: {e}")
            return False
    
    async def _execute_promotions(self, promotions: Dict, guild: discord.Guild) -> bool:
        try:
            # Prepare batch updates for sheets
            sheet_updates = []
            
            for member_name, promotion_info in promotions.items():
                # Add to sheet update batch
                sheet_updates.append({
                    'name': member_name,
                    'new_rank': promotion_info['new_rank'],
                    'increment_counter': True  # Increment career counter for promotion
                })
            
            # Execute sheet updates
            if sheet_updates:
                success = self.sheets_manager.batch_update_members(sheet_updates)
                if not success:
                    logger.error("Failed to update Google Sheets with promotions")
                    return False
            
            # Update Discord roles
            await self._update_discord_roles(promotions, guild)
            
            # Post promotion notifications
            await self._post_promotion_notifications(promotions, guild)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to execute promotions: {e}")
            return False
    
    async def _update_discord_roles(self, promotions: Dict, guild: discord.Guild) -> None:
        for member_name, promotion_info in promotions.items():
            try:
                discord_id = promotion_info['discord_id']
                old_rank = promotion_info['old_rank']
                new_rank = promotion_info['new_rank']
                
                # Get Discord member
                if not discord_id or discord_id == '':
                    logger.warning(f"No Discord ID found for {member_name}")
                    continue
                
                try:
                    discord_member = guild.get_member(int(discord_id))
                    if not discord_member:
                        logger.warning(f"Discord member not found: {discord_id} ({member_name})")
                        continue
                except ValueError:
                    logger.warning(f"Invalid Discord ID format: {discord_id} ({member_name})")
                    continue
                
                # Get role objects
                old_role_id = RankData.get_rank_role_id(old_rank)
                new_role_id = RankData.get_rank_role_id(new_rank)
                
                old_role = guild.get_role(old_role_id) if old_role_id else None
                new_role = guild.get_role(new_role_id) if new_role_id else None
                
                # Remove old role if it exists
                if old_role and old_role in discord_member.roles:
                    await discord_member.remove_roles(old_role, reason=f"EOMBot promotion: {old_rank} -> {new_rank}")
                    logger.info(f"Removed {old_rank} role from {member_name}")
                
                # Add new role if it exists
                if new_role and new_role not in discord_member.roles:
                    await discord_member.add_roles(new_role, reason=f"EOMBot promotion: {old_rank} -> {new_rank}")
                    logger.info(f"Added {new_rank} role to {member_name}")
                
                if not old_role and not new_role:
                    logger.warning(f"No roles found for promotion: {member_name} ({old_rank} -> {new_rank})")
                
            except discord.errors.Forbidden:
                logger.error(f"No permission to update roles for {member_name}")
            except Exception as e:
                logger.error(f"Failed to update Discord roles for {member_name}: {e}")
    
    async def _post_promotion_notifications(self, promotions: Dict, guild: discord.Guild) -> None:
        try:
            if not promotions:
                return
            
            # Get rank change channel
            rank_channel = guild.get_channel(Config.RANK_CHANGE_CHANNEL_ID)
            if not rank_channel:
                logger.warning("Rank change channel not found")
                return
            
            # Create promotion message
            promotion_lines = []
            promotion_lines.append("🎉 **Rank Promotions** 🎉\n")
            
            for member_name, promotion_info in promotions.items():
                old_rank = promotion_info['old_rank']
                new_rank = promotion_info['new_rank']
                discord_id = promotion_info['discord_id']
                
                # Try to mention the user if we have their Discord ID
                if discord_id:
                    try:
                        mention = f"<@{int(discord_id)}>"
                    except ValueError:
                        mention = member_name
                else:
                    mention = member_name
                
                promotion_lines.append(f"**{mention}** has been promoted from **{old_rank}** to **{new_rank}**!")
            
            message_content = "\n".join(promotion_lines)
            
            # Split message if too long (Discord 2000 char limit)
            if len(message_content) > 2000:
                # Send in chunks
                chunks = []
                current_chunk = "🎉 **Rank Promotions** 🎉\n"
                
                for line in promotion_lines[1:]:  # Skip the header
                    if len(current_chunk + line + "\n") > 1900:  # Leave some buffer
                        chunks.append(current_chunk)
                        current_chunk = line + "\n"
                    else:
                        current_chunk += line + "\n"
                
                if current_chunk.strip():
                    chunks.append(current_chunk)
                
                for chunk in chunks:
                    await rank_channel.send(chunk)
            else:
                await rank_channel.send(message_content)
            
            logger.info(f"Posted promotion notifications for {len(promotions)} members")
            
        except Exception as e:
            logger.error(f"Failed to post promotion notifications: {e}")
    
    def get_promotion_summary(self, promotions: Dict) -> str:
        if not promotions:
            return "No rank promotions this month."
        
        summary_lines = []
        summary_lines.append(f"**Rank Promotions Summary ({len(promotions)} promotions)**\n")
        
        for member_name, promotion_info in promotions.items():
            old_rank = promotion_info['old_rank']
            new_rank = promotion_info['new_rank']
            summary_lines.append(f"**{member_name}**: {old_rank} → {new_rank}")
        
        return "\n".join(summary_lines)