import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Discord Configuration
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    EOM_POST_CHANNEL_ID = int(os.getenv('EOM_POST_CHANNEL_ID', 0))
    WISE_OLD_MAN_CHANNEL_ID = int(os.getenv('WISE_OLD_MAN_CHANNEL_ID', 0))
    LOOT_NOTIFICATIONS_CHANNEL_ID = int(os.getenv('LOOT_NOTIFICATIONS_CHANNEL_ID', 0))
    LOG_NOTIFICATIONS_CHANNEL_ID = int(os.getenv('LOG_NOTIFICATIONS_CHANNEL_ID', 0))
    RANK_CHANGE_CHANNEL_ID = int(os.getenv('RANK_CHANGE_CHANNEL_ID', 0))
    
    # Discord Role IDs
    MEDIATOR_ROLE_ID = int(os.getenv('MEDIATOR_ROLE_ID', 0))
    SAGE_ROLE_ID = int(os.getenv('SAGE_ROLE_ID', 0))
    DESTROYER_ROLE_ID = int(os.getenv('DESTROYER_ROLE_ID', 0))
    UNHOLY_ROLE_ID = int(os.getenv('UNHOLY_ROLE_ID', 0))
    LEGEND_ROLE_ID = int(os.getenv('LEGEND_ROLE_ID', 0))
    
    # Google Sheets Configuration
    GOOGLE_SHEETS_CREDENTIALS_FILE = os.getenv('GOOGLE_SHEETS_CREDENTIALS_FILE', 'service_account.json')
    GOOGLE_SHEETS_ID = os.getenv('GOOGLE_SHEETS_ID')
    MEMBER_NAME_COLUMN = os.getenv('MEMBER_NAME_COLUMN', 'A')
    DISCORD_ID_COLUMN = os.getenv('DISCORD_ID_COLUMN', 'B')
    RANK_COLUMN = os.getenv('RANK_COLUMN', 'C')
    CAREER_COUNTER_COLUMN = os.getenv('CAREER_COUNTER_COLUMN', 'D')
    ADDED_DATE_COLUMN = os.getenv('ADDED_DATE_COLUMN', 'E')
    
    # Rank Promotion Thresholds
    SAGE_PROMOTION_THRESHOLD = int(os.getenv('SAGE_PROMOTION_THRESHOLD', 5))
    DESTROYER_PROMOTION_THRESHOLD = int(os.getenv('DESTROYER_PROMOTION_THRESHOLD', 10))
    UNHOLY_PROMOTION_THRESHOLD = int(os.getenv('UNHOLY_PROMOTION_THRESHOLD', 15))
    MEDIATOR_TIME_REQUIREMENT_DAYS = int(os.getenv('MEDIATOR_TIME_REQUIREMENT_DAYS', 30))
    
    # Wise Old Man API Configuration
    WISE_OLD_MAN_GROUP_ID = int(os.getenv('WISE_OLD_MAN_GROUP_ID', 0))
    
    # Achievement Channels List
    ACHIEVEMENT_CHANNELS = [
        WISE_OLD_MAN_CHANNEL_ID,
        LOOT_NOTIFICATIONS_CHANNEL_ID,
        LOG_NOTIFICATIONS_CHANNEL_ID
    ]
    
    # Role Mapping
    ROLE_MAPPING = {
        'Mediator': MEDIATOR_ROLE_ID,
        'Sage': SAGE_ROLE_ID,
        'Destroyer': DESTROYER_ROLE_ID,
        'Unholy': UNHOLY_ROLE_ID,
        'Legend': LEGEND_ROLE_ID
    }
    
    @classmethod
    def validate_config(cls):
        required_vars = [
            'DISCORD_TOKEN',
            'GOOGLE_SHEETS_ID',
            'WISE_OLD_MAN_GROUP_ID'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True