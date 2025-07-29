import gspread
from google.auth.exceptions import GoogleAuthError
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime
from bot.config.config import Config

logger = logging.getLogger(__name__)

class SheetsManager:
    def __init__(self):
        self.gc = None
        self.sheet = None
        self._authenticate()
    
    def _authenticate(self):
        try:
            self.gc = gspread.service_account(filename=Config.GOOGLE_SHEETS_CREDENTIALS_FILE)
            self.sheet = self.gc.open_by_key(Config.GOOGLE_SHEETS_ID).sheet1
            logger.info("Successfully authenticated with Google Sheets")
        except GoogleAuthError as e:
            logger.error(f"Google Sheets authentication failed: {e}")
            raise
        except FileNotFoundError:
            logger.error(f"Google Sheets credentials file not found: {Config.GOOGLE_SHEETS_CREDENTIALS_FILE}")
            raise
        except Exception as e:
            logger.error(f"Failed to open Google Sheets: {e}")
            raise
    
    def get_all_members(self) -> List[Dict[str, str]]:
        try:
            all_records = self.sheet.get_all_records()
            members = []
            
            for record in all_records:
                # Map column letters to actual column names from the sheet
                member = {
                    'name': record.get(self._get_column_header(Config.MEMBER_NAME_COLUMN), ''),
                    'discord_id': record.get(self._get_column_header(Config.DISCORD_ID_COLUMN), ''),
                    'rank': record.get(self._get_column_header(Config.RANK_COLUMN), ''),
                    'career_counter': record.get(self._get_column_header(Config.CAREER_COUNTER_COLUMN), 0),
                    'added_date': record.get(self._get_column_header(Config.ADDED_DATE_COLUMN), '')
                }
                
                # Convert career_counter to int if it's a string
                try:
                    member['career_counter'] = int(member['career_counter']) if member['career_counter'] else 0
                except (ValueError, TypeError):
                    member['career_counter'] = 0
                
                members.append(member)
            
            logger.info(f"Retrieved {len(members)} members from Google Sheets")
            return members
            
        except Exception as e:
            logger.error(f"Failed to get members from Google Sheets: {e}")
            raise
    
    def find_member_by_name(self, name: str) -> Optional[Dict[str, str]]:
        try:
            members = self.get_all_members()
            
            # Try exact match first
            for member in members:
                if member['name'].lower() == name.lower():
                    return member
            
            # Try partial match
            for member in members:
                if name.lower() in member['name'].lower() or member['name'].lower() in name.lower():
                    logger.info(f"Found partial match: '{name}' -> '{member['name']}'")
                    return member
            
            logger.warning(f"Member not found: {name}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to find member {name}: {e}")
            return None
    
    def update_member_rank(self, member_name: str, new_rank: str) -> bool:
        try:
            # Find the member's row
            members = self.get_all_members()
            row_index = None
            
            for i, member in enumerate(members):
                if member['name'].lower() == member_name.lower():
                    row_index = i + 2  # +2 because sheets are 1-indexed and we skip header
                    break
            
            if row_index is None:
                logger.error(f"Member {member_name} not found for rank update")
                return False
            
            # Update the rank column
            rank_column = Config.RANK_COLUMN
            self.sheet.update(f'{rank_column}{row_index}', new_rank)
            
            logger.info(f"Updated {member_name} rank to {new_rank}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update rank for {member_name}: {e}")
            return False
    
    def increment_career_counter(self, member_name: str) -> bool:
        try:
            # Find the member's row and current counter
            members = self.get_all_members()
            row_index = None
            current_counter = 0
            
            for i, member in enumerate(members):
                if member['name'].lower() == member_name.lower():
                    row_index = i + 2  # +2 because sheets are 1-indexed and we skip header
                    current_counter = member['career_counter']
                    break
            
            if row_index is None:
                logger.error(f"Member {member_name} not found for career counter update")
                return False
            
            # Increment and update the career counter
            new_counter = current_counter + 1
            counter_column = Config.CAREER_COUNTER_COLUMN
            self.sheet.update(f'{counter_column}{row_index}', new_counter)
            
            logger.info(f"Incremented {member_name} career counter to {new_counter}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to increment career counter for {member_name}: {e}")
            return False
    
    def batch_update_members(self, updates: List[Dict]) -> bool:
        try:
            batch_updates = []
            
            for update in updates:
                member_name = update['name']
                new_rank = update.get('new_rank')
                increment_counter = update.get('increment_counter', False)
                
                # Find member row
                members = self.get_all_members()
                row_index = None
                current_counter = 0
                
                for i, member in enumerate(members):
                    if member['name'].lower() == member_name.lower():
                        row_index = i + 2
                        current_counter = member['career_counter']
                        break
                
                if row_index is None:
                    logger.warning(f"Member {member_name} not found for batch update")
                    continue
                
                # Add rank update
                if new_rank:
                    batch_updates.append({
                        'range': f'{Config.RANK_COLUMN}{row_index}',
                        'values': [[new_rank]]
                    })
                
                # Add career counter update
                if increment_counter:
                    new_counter = current_counter + 1
                    batch_updates.append({
                        'range': f'{Config.CAREER_COUNTER_COLUMN}{row_index}',
                        'values': [[new_counter]]
                    })
            
            if batch_updates:
                self.sheet.batch_update(batch_updates)
                logger.info(f"Completed batch update of {len(batch_updates)} cells")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to perform batch update: {e}")
            return False
    
    def _get_column_header(self, column_letter: str) -> str:
        try:
            # Get the header row to map column letters to actual names
            headers = self.sheet.row_values(1)
            
            # Convert column letter to index (A=0, B=1, etc.)
            col_index = ord(column_letter.upper()) - ord('A')
            
            if col_index < len(headers):
                return headers[col_index]
            else:
                logger.warning(f"Column {column_letter} not found, using column letter as fallback")
                return column_letter
                
        except Exception as e:
            logger.error(f"Failed to get column header for {column_letter}: {e}")
            return column_letter
    
    def backup_sheet(self) -> bool:
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"EOMBot_Backup_{timestamp}"
            
            # Create a copy of the sheet
            backup_sheet = self.gc.copy(Config.GOOGLE_SHEETS_ID, title=backup_name)
            logger.info(f"Created backup sheet: {backup_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return False