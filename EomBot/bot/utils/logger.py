import logging
import sys
from datetime import datetime
import os

def setup_logger(name: str = 'eombot', level: str = 'INFO') -> logging.Logger:
    # Create logs directory if it doesn't exist
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Create logger
    logger = logging.getLogger(name)
    
    # Clear existing handlers to avoid duplication
    logger.handlers.clear()
    
    # Set level
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # File handler for detailed logs
    today = datetime.now().strftime('%Y-%m-%d')
    file_handler = logging.FileHandler(f'{log_dir}/eombot_{today}.log', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    
    # Console handler for general output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(console_formatter)
    
    # Error file handler for errors only
    error_handler = logging.FileHandler(f'{log_dir}/eombot_errors_{today}.log', encoding='utf-8')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.addHandler(error_handler)
    
    return logger

def get_logger(name: str = 'eombot') -> logging.Logger:
    return logging.getLogger(name)

def log_command_usage(user_id: int, username: str, command: str, guild_id: int, guild_name: str):
    logger = get_logger()
    logger.info(f"Command used: {command} | User: {username} ({user_id}) | Guild: {guild_name} ({guild_id})")

def log_error_with_context(error: Exception, context: str, **kwargs):
    logger = get_logger()
    context_info = " | ".join([f"{k}: {v}" for k, v in kwargs.items()])
    logger.error(f"Error in {context}: {str(error)} | Context: {context_info}", exc_info=True)

def log_achievement_parsing(month: str, total_members: int, total_achievements: int):
    logger = get_logger()
    logger.info(f"Achievement parsing completed | Month: {month} | Members: {total_members} | Achievements: {total_achievements}")

def log_rank_promotions(promotions: dict):
    logger = get_logger()
    if promotions:
        promotion_summary = ", ".join([f"{name}: {info['old_rank']} -> {info['new_rank']}" for name, info in promotions.items()])
        logger.info(f"Rank promotions processed | Count: {len(promotions)} | Promotions: {promotion_summary}")
    else:
        logger.info("No rank promotions this month")

def log_sheets_operation(operation: str, success: bool, details: str = ""):
    logger = get_logger()
    status = "SUCCESS" if success else "FAILED"  
    message = f"Google Sheets {operation}: {status}"
    if details:
        message += f" | Details: {details}"
    
    if success:
        logger.info(message)
    else:
        logger.error(message)