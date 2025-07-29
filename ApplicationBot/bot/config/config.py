import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    GOOGLE_SHEETS_ID = os.getenv('GOOGLE_SHEETS_ID')
    
    APPLICATIONS_CHANNEL_ID = int(os.getenv('APPLICATIONS_CHANNEL_ID', 0))
    APPLICATIONS_PENDING_CHANNEL_ID = int(os.getenv('APPLICATIONS_PENDING_CHANNEL_ID', 0))
    APPLICATIONS_ACCEPTED_CHANNEL_ID = int(os.getenv('APPLICATIONS_ACCEPTED_CHANNEL_ID', 0))
    WELCOME_CHANNEL_ID = int(os.getenv('WELCOME_CHANNEL_ID', 0))
    MOD_REVIEW_CHANNEL_ID = int(os.getenv('MOD_REVIEW_CHANNEL_ID', 0))
    
    APPLICATION_PENDING_ROLE_ID = int(os.getenv('APPLICATION_PENDING_ROLE_ID', 0))
    UNHOLY_ROLE_ID = int(os.getenv('UNHOLY_ROLE_ID', 0))
    FRIEND_ROLE_ID = int(os.getenv('FRIEND_ROLE_ID', 0))
    APPLICATION_DENY_ROLE_ID = int(os.getenv('APPLICATION_DENY_ROLE_ID', 0))
    
    PRE_APPLICATION_IMAGE_URL = os.getenv('PRE_APPLICATION_IMAGE_URL', '')
    
    @classmethod
    def validate(cls):
        required_vars = [
            'DISCORD_TOKEN',
            'GOOGLE_SHEETS_ID',
            'APPLICATIONS_CHANNEL_ID',
            'APPLICATIONS_PENDING_CHANNEL_ID',
            'APPLICATION_PENDING_ROLE_ID',
            'UNHOLY_ROLE_ID',
            'FRIEND_ROLE_ID'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
                
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True