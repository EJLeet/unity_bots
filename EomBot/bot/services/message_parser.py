import discord
import re
from datetime import datetime, timedelta
from typing import List, Dict, Set, Tuple, Optional
import calendar
import logging
from bot.config.config import Config
from bot.services.runescape_wiki_api import get_loot_value

logger = logging.getLogger(__name__)

class MessageParser:
    def __init__(self, bot: discord.Client):
        self.bot = bot
        
        # Regex patterns for different message types
        self.achievement_pattern = r"^(.+?)\s*-\s*:.+?:\s*\d+\s*.+"
        self.loot_pattern = r"^(.+?):"
        self.log_pattern = r"^(.+?):"
    
    async def parse_monthly_achievements(self, month: str, year: int = None) -> Dict[str, Dict]:
        if year is None:
            year = datetime.now().year
        
        try:
            # Convert month name to number
            month_num = self._month_name_to_number(month)
            if month_num is None:
                logger.error(f"Invalid month name: {month}")
                return {}
            
            # Get date range for the month
            start_date, end_date = self._get_month_date_range(month_num, year)
            
            achievements = {}
            
            # Parse messages from all achievement channels
            for channel_id in Config.ACHIEVEMENT_CHANNELS:
                if channel_id == 0:  # Skip if not configured
                    continue
                    
                try:
                    channel = self.bot.get_channel(channel_id)
                    if not channel:
                        logger.warning(f"Channel {channel_id} not found")
                        continue
                    
                    channel_achievements = await self._parse_channel_messages(
                        channel, start_date, end_date
                    )
                    
                    # Merge achievements
                    for member, member_data in channel_achievements.items():
                        if member not in achievements:
                            achievements[member] = {
                                'achievements': [],
                                'loot_items': [],
                                'total_loot_value': 0
                            }
                        
                        achievements[member]['achievements'].extend(member_data['achievements'])
                        achievements[member]['loot_items'].extend(member_data['loot_items'])
                        achievements[member]['total_loot_value'] += member_data['total_loot_value']
                    
                    logger.info(f"Parsed {len(channel_achievements)} members from #{channel.name}")
                    
                except Exception as e:
                    logger.error(f"Failed to parse channel {channel_id}: {e}")
                    continue
            
            # Remove duplicates and clean up
            for member in achievements:
                achievements[member]['achievements'] = list(set(achievements[member]['achievements']))
                # Note: keeping loot_items as is since duplicates might be legitimate
            
            logger.info(f"Total achievements parsed for {month} {year}: {len(achievements)} members")
            return achievements
            
        except Exception as e:
            logger.error(f"Failed to parse monthly achievements: {e}")
            return {}
    
    async def _parse_channel_messages(self, channel: discord.TextChannel, 
                                    start_date: datetime, end_date: datetime) -> Dict[str, Dict]:
        achievements = {}
        
        try:
            async for message in channel.history(
                after=start_date, 
                before=end_date, 
                limit=None
            ):
                # Skip bot messages
                if message.author.bot:
                    continue
                
                # Skip empty messages
                if not message.content.strip():
                    continue
                
                # Parse the message based on channel type
                parsed_data = await self._parse_single_message(message, channel)
                
                if parsed_data:
                    member_name, achievement, loot_items, loot_value = parsed_data
                    
                    # Clean up member name
                    member_name = self._clean_member_name(member_name)
                    
                    if member_name not in achievements:
                        achievements[member_name] = {
                            'achievements': [],
                            'loot_items': [],
                            'total_loot_value': 0
                        }
                    
                    achievements[member_name]['achievements'].append(achievement)
                    achievements[member_name]['loot_items'].extend(loot_items)
                    achievements[member_name]['total_loot_value'] += loot_value
        
        except discord.errors.Forbidden:
            logger.error(f"No permission to read messages in #{channel.name}")
        except Exception as e:
            logger.error(f"Error parsing messages in #{channel.name}: {e}")
        
        return achievements
    
    async def _parse_single_message(self, message: discord.Message, 
                            channel: discord.TextChannel) -> Optional[Tuple[str, str, List[str], int]]:
        content = message.content.strip()
        
        # Skip messages that start with common bot patterns
        if any(content.startswith(prefix) for prefix in ['!', '/', '<@', 'http']):
            return None
        
        try:
            # Achievement messages (e.g., "NMZ WARRI0R - :defence: 99 Defence")
            if channel.id == Config.WISE_OLD_MAN_CHANNEL_ID:
                return await self._parse_achievement_message(content)
            
            # Loot/Log notifications (e.g., "OhYaPapi:" followed by loot info)
            elif channel.id in [Config.LOOT_NOTIFICATIONS_CHANNEL_ID, Config.LOG_NOTIFICATIONS_CHANNEL_ID]:
                return await self._parse_notification_message(content)
            
            else:
                # Generic parsing for unknown channel types
                return await self._parse_generic_message(content)
                
        except Exception as e:
            logger.debug(f"Failed to parse message: {content[:50]}... - {e}")
            return None
    
    async def _parse_achievement_message(self, content: str) -> Optional[Tuple[str, str, List[str], int]]:
        # Pattern: "NMZ WARRI0R - :defence: 99 Defence"
        match = re.match(self.achievement_pattern, content)
        if match:
            member_name = match.group(1).strip()
            achievement = content  # Store full achievement text
            # Achievement messages don't have loot, so return empty loot data
            return member_name, achievement, [], 0
        
        return None
    
    async def _parse_notification_message(self, content: str) -> Optional[Tuple[str, str, List[str], int]]:
        # Pattern: "OhYaPapi:" followed by loot/log info
        lines = content.split('\n')
        first_line = lines[0].strip()
        
        # Check if first line ends with ':'
        if first_line.endswith(':'):
            member_name = first_line[:-1].strip()  # Remove the colon
            
            # Get the rest of the message as achievement description
            if len(lines) > 1:
                achievement_details = '\n'.join(lines[1:]).strip()
                achievement = f"{first_line} {achievement_details}"
                
                # Extract loot items from the details
                loot_items = self._extract_loot_items(achievement_details)
                
                # Calculate loot value
                if loot_items:
                    total_value, formatted_value = await get_loot_value(loot_items)
                    logger.debug(f"Calculated loot value for {member_name}: {formatted_value}")
                    return member_name, achievement, loot_items, total_value
                else:
                    return member_name, achievement, [], 0
            else:
                achievement = first_line
                return member_name, achievement, [], 0
        
        # Fallback pattern matching
        match = re.match(self.loot_pattern, first_line)
        if match:
            member_name = match.group(1).strip()
            achievement = content
            
            # Try to extract loot items from the full content
            loot_items = self._extract_loot_items(content)
            if loot_items:
                total_value, formatted_value = await get_loot_value(loot_items)
                return member_name, achievement, loot_items, total_value
            else:
                return member_name, achievement, [], 0
        
        return None
    
    async def _parse_generic_message(self, content: str) -> Optional[Tuple[str, str, List[str], int]]:
        # Try both patterns as fallback
        
        # Try achievement pattern first
        match = re.match(self.achievement_pattern, content)
        if match:
            member_name = match.group(1).strip()
            return member_name, content, [], 0
        
        # Try notification pattern
        match = re.match(self.loot_pattern, content)
        if match:
            member_name = match.group(1).strip()
            
            # Try to extract loot items
            loot_items = self._extract_loot_items(content)
            if loot_items:
                total_value, formatted_value = await get_loot_value(loot_items)
                return member_name, content, loot_items, total_value
            else:
                return member_name, content, [], 0
        
        return None
    
    def _clean_member_name(self, name: str) -> str:
        # Remove common prefixes/suffixes and clean up the name
        name = name.strip()
        
        # Remove mentions
        name = re.sub(r'<@!?\d+>', '', name)
        
        # Remove extra whitespace
        name = re.sub(r'\s+', ' ', name).strip()
        
        # Remove trailing punctuation except for names that might legitimately end with it
        name = name.rstrip('.,!?;')
        
        return name
    
    def _extract_loot_items(self, text: str) -> List[str]:
        """Extract loot items from message text
        
        Examples:
        "1 x Avernic treads" -> ["1 x Avernic treads"]
        "Dragon claws\n50 x Dragon bones" -> ["Dragon claws", "50 x Dragon bones"]
        """
        if not text.strip():
            return []
        
        loot_items = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Skip common non-loot lines
            skip_patterns = [
                r'^Total value:',
                r'^Loot from',
                r'^Drops from',
                r'has received',
                r'has gained',
                r'^\d+:\d+',  # Time stamps
                r'^Image$',   # Image indicators
                r'^-+$',      # Separator lines
            ]
            
            if any(re.match(pattern, line, re.IGNORECASE) for pattern in skip_patterns):
                continue
            
            # Look for item patterns
            # Pattern 1: "1 x Item name" or "50x Item name"
            if re.match(r'^\d+\s*x\s*.+', line, re.IGNORECASE):
                loot_items.append(line)
                continue
            
            # Pattern 2: Just item names (assume quantity 1)
            # Filter out very short or obviously non-item text
            if len(line) > 3 and not line.isdigit():
                # Check if it looks like an item name (contains letters)
                if re.search(r'[a-zA-Z]', line):
                    # Don't include lines that are too long (likely descriptions)
                    if len(line) <= 50:
                        loot_items.append(line)
        
        return loot_items
    
    def _month_name_to_number(self, month_name: str) -> int:
        try:
            # Handle both full names and abbreviations
            month_name = month_name.strip().lower()
            
            # Full month names
            month_mapping = {
                'january': 1, 'february': 2, 'march': 3, 'april': 4,
                'may': 5, 'june': 6, 'july': 7, 'august': 8,
                'september': 9, 'october': 10, 'november': 11, 'december': 12,
                'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
                'jun': 6, 'jul': 7, 'aug': 8, 'sep': 9,
                'oct': 10, 'nov': 11, 'dec': 12
            }
            
            return month_mapping.get(month_name)
            
        except Exception:
            return None
    
    def _get_month_date_range(self, month: int, year: int) -> tuple[datetime, datetime]:
        # Get first day of the month
        start_date = datetime(year, month, 1)
        
        # Get last day of the month
        last_day = calendar.monthrange(year, month)[1]
        end_date = datetime(year, month, last_day, 23, 59, 59)
        
        return start_date, end_date
    
    def get_unique_members_with_achievements(self, achievements: Dict[str, Dict]) -> Set[str]:
        return set(achievements.keys())
    
    def get_achievement_summary(self, achievements: Dict[str, Dict]) -> str:
        if not achievements:
            return "No achievements found for the specified month."
        
        summary_lines = []
        total_achievements = sum(len(member_data['achievements']) for member_data in achievements.values())
        total_loot_value = sum(member_data['total_loot_value'] for member_data in achievements.values())
        
        summary_lines.append(f"**Achievement Summary ({len(achievements)} members, {total_achievements} total achievements)**\n")
        
        # Sort members by number of achievements (descending)
        sorted_members = sorted(achievements.items(), key=lambda x: len(x[1]['achievements']), reverse=True)
        
        for member, member_data in sorted_members:
            member_achievements = member_data['achievements']
            member_loot_value = member_data['total_loot_value']
            
            # Format loot value
            if member_loot_value > 0:
                if member_loot_value >= 1_000_000:
                    loot_str = f", {member_loot_value / 1_000_000:.1f}M gp in loot"
                elif member_loot_value >= 1_000:
                    loot_str = f", {member_loot_value / 1_000:.1f}K gp in loot"
                else:
                    loot_str = f", {member_loot_value:,} gp in loot"
            else:
                loot_str = ""
            
            summary_lines.append(f"**{member}** ({len(member_achievements)} achievements{loot_str})")
            
            for achievement in member_achievements[:3]:  # Show first 3 achievements
                # Truncate long achievements
                if len(achievement) > 100:
                    achievement = achievement[:97] + "..."
                summary_lines.append(f"  • {achievement}")
            
            if len(member_achievements) > 3:
                summary_lines.append(f"  • ... and {len(member_achievements) - 3} more")
            
            summary_lines.append("")  # Empty line between members
        
        # Add total loot value summary if there's any loot
        if total_loot_value > 0:
            if total_loot_value >= 1_000_000:
                total_loot_str = f"{total_loot_value / 1_000_000:.1f}M gp"
            elif total_loot_value >= 1_000:
                total_loot_str = f"{total_loot_value / 1_000:.1f}K gp"
            else:
                total_loot_str = f"{total_loot_value:,} gp"
            
            summary_lines.append(f"**Total Loot Value: {total_loot_str}**")
        
        return "\n".join(summary_lines)