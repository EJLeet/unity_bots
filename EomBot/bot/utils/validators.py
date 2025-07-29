import re
from datetime import datetime
import calendar
from typing import Optional
import discord
from bot.config.config import Config

def validate_month(month: str) -> tuple[bool, Optional[str]]:
    if not month:
        return False, "Month cannot be empty"
    
    month = month.strip().lower()
    
    # Valid month names (full and abbreviated)
    valid_months = [
        'january', 'february', 'march', 'april', 'may', 'june',
        'july', 'august', 'september', 'october', 'november', 'december',
        'jan', 'feb', 'mar', 'apr', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'
    ]
    
    if month not in valid_months:
        return False, f"Invalid month: {month}. Please use a valid month name (e.g., 'January' or 'Jan')"
    
    return True, None

def validate_channel_restriction(channel: discord.TextChannel) -> tuple[bool, Optional[str]]:
    if channel.id != Config.EOM_POST_CHANNEL_ID:
        return False, f"This command can only be used in <#{Config.EOM_POST_CHANNEL_ID}>"
    
    return True, None

def validate_user_permissions(member: discord.Member) -> tuple[bool, Optional[str]]:
    # Check if user has permission to use the bot
    # You can customize this based on your server's permission structure
    
    # Example: Check if user has manage_messages permission or specific role
    if member.guild_permissions.manage_messages:
        return True, None
    
    # Check for specific roles (you can customize these role names)
    allowed_roles = ['Admin', 'Moderator', 'EOM Manager']  # Customize as needed
    
    user_roles = [role.name for role in member.roles]
    if any(role in allowed_roles for role in user_roles):
        return True, None
    
    return False, "You don't have permission to use this command"

def validate_guild_setup(guild: discord.Guild) -> tuple[bool, list[str]]:
    errors = []
    
    # Check if required channels exist
    required_channels = {
        'EOM Post': Config.EOM_POST_CHANNEL_ID,
        'Wise Old Man': Config.WISE_OLD_MAN_CHANNEL_ID,
        'Loot Notifications': Config.LOOT_NOTIFICATIONS_CHANNEL_ID,
        'Log Notifications': Config.LOG_NOTIFICATIONS_CHANNEL_ID,
        'Rank Change': Config.RANK_CHANGE_CHANNEL_ID
    }
    
    for channel_name, channel_id in required_channels.items():
        if channel_id == 0:
            errors.append(f"{channel_name} channel ID not configured")
        elif not guild.get_channel(channel_id):
            errors.append(f"{channel_name} channel not found (ID: {channel_id})")
    
    # Check if required roles exist
    required_roles = {
        'Mediator': Config.MEDIATOR_ROLE_ID,
        'Sage': Config.SAGE_ROLE_ID, 
        'Destroyer': Config.DESTROYER_ROLE_ID,
        'Unholy': Config.UNHOLY_ROLE_ID,
        'Legend': Config.LEGEND_ROLE_ID
    }
    
    for role_name, role_id in required_roles.items():
        if role_id == 0:
            errors.append(f"{role_name} role ID not configured")
        elif not guild.get_role(role_id):
            errors.append(f"{role_name} role not found (ID: {role_id})")
    
    return len(errors) == 0, errors

def validate_bot_permissions(guild: discord.Guild, bot_member: discord.Member) -> tuple[bool, list[str]]:
    errors = []
    
    # Required permissions
    required_permissions = [
        'read_message_history',
        'send_messages',
        'manage_roles',
        'use_slash_commands'
    ]
    
    bot_permissions = bot_member.guild_permissions
    
    for perm in required_permissions:
        if not getattr(bot_permissions, perm, False):
            errors.append(f"Missing permission: {perm}")
    
    # Check channel-specific permissions
    channels_to_check = [
        Config.EOM_POST_CHANNEL_ID,
        Config.WISE_OLD_MAN_CHANNEL_ID,
        Config.LOOT_NOTIFICATIONS_CHANNEL_ID,
        Config.LOG_NOTIFICATIONS_CHANNEL_ID,
        Config.RANK_CHANGE_CHANNEL_ID
    ]
    
    for channel_id in channels_to_check:
        if channel_id == 0:
            continue
            
        channel = guild.get_channel(channel_id)
        if channel:
            channel_perms = channel.permissions_for(bot_member)
            
            if not channel_perms.read_message_history:
                errors.append(f"Cannot read message history in #{channel.name}")
            
            if channel_id == Config.RANK_CHANGE_CHANNEL_ID and not channel_perms.send_messages:
                errors.append(f"Cannot send messages in #{channel.name}")
    
    return len(errors) == 0, errors

def validate_date_format(date_str: str) -> tuple[bool, Optional[datetime]]:
    if not date_str:
        return False, None
    
    # Common date formats to try
    formats = [
        '%Y-%m-%d',
        '%m/%d/%Y',
        '%d/%m/%Y',
        '%Y-%m-%d %H:%M:%S',
        '%m/%d/%Y %H:%M:%S'
    ]
    
    for fmt in formats:
        try:
            parsed_date = datetime.strptime(date_str, fmt)
            return True, parsed_date
        except ValueError:
            continue
    
    return False, None

def validate_member_name(name: str) -> tuple[bool, Optional[str]]:
    if not name or not name.strip():
        return False, "Member name cannot be empty"
    
    name = name.strip()
    
    # Check for reasonable length
    if len(name) > 50:
        return False, "Member name is too long (max 50 characters)"
    
    if len(name) < 2:
        return False, "Member name is too short (min 2 characters)"
    
    # Check for valid characters (allow letters, numbers, spaces, common symbols)
    if not re.match(r'^[a-zA-Z0-9\s\-_\.]+$', name):
        return False, "Member name contains invalid characters"
    
    return True, None

def validate_discord_id(discord_id: str) -> tuple[bool, Optional[int]]:
    if not discord_id:
        return False, None
    
    try:
        # Discord IDs are typically 17-19 digits
        id_int = int(discord_id)
        if len(str(id_int)) < 15 or len(str(id_int)) > 20:
            return False, None
        return True, id_int
    except ValueError:
        return False, None

def validate_rank(rank: str) -> tuple[bool, Optional[str]]:
    from bot.data.rank_data import RankData
    
    if not rank:
        return False, "Rank cannot be empty"
    
    if rank not in RankData.RANK_HIERARCHY:
        valid_ranks = ', '.join(RankData.RANK_HIERARCHY)
        return False, f"Invalid rank: {rank}. Valid ranks: {valid_ranks}"
    
    return True, None

def sanitize_input(text: str) -> str:
    if not text:
        return ""
    
    # Remove potential harmful characters and excessive whitespace
    sanitized = re.sub(r'[<>@&]', '', text)  # Remove potential mention/injection chars
    sanitized = re.sub(r'\s+', ' ', sanitized)  # Normalize whitespace
    sanitized = sanitized.strip()
    
    return sanitized