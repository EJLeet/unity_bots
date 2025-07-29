import gspread
from google.oauth2.service_account import Credentials
import logging
from typing import Optional, List, Dict, Any
from config.config import Config

logger = logging.getLogger(__name__)

class GoogleSheetsManager:
    def __init__(self):
        self.client = None
        self.spreadsheet = None
        self._initialize_client()
        
    def _initialize_client(self):
        try:
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            
            credentials = Credentials.from_service_account_file(
                'service_account.json',
                scopes=scope
            )
            
            self.client = gspread.authorize(credentials)
            self.spreadsheet = self.client.open_by_key(Config.GOOGLE_SHEETS_ID)
            logger.info("Google Sheets client initialized successfully")
            
        except FileNotFoundError:
            logger.error("service_account.json file not found")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets client: {e}")
            raise
            
    def search_discord_id(self, discord_id: str) -> Optional[Dict[str, Any]]:
        try:
            worksheets = self.spreadsheet.worksheets()
            
            for worksheet in worksheets:
                try:
                    records = worksheet.get_all_records()
                    
                    for i, record in enumerate(records, start=2):  # Start from row 2 (after headers)
                        if str(record.get('Discord ID', '')).strip() == str(discord_id).strip():
                            return {
                                'worksheet': worksheet.title,
                                'row': i,
                                'data': record
                            }
                            
                except Exception as e:
                    logger.warning(f"Error searching worksheet {worksheet.title}: {e}")
                    continue
                    
            return None
            
        except Exception as e:
            logger.error(f"Error searching for Discord ID {discord_id}: {e}")
            return None
            
    def add_new_entry(self, application_data: Dict[str, Any]) -> bool:
        try:
            worksheet = self.spreadsheet.sheet1
            
            rank = application_data.get('rank', '').lower()
            if rank == 'friend':
                rank_value = 'goblin'
            else:
                rank_value = rank
                
            alts_list = application_data.get('alts', [])
            alts_string = ', '.join(alts_list) if alts_list else ''
            
            row_data = [
                application_data.get('in_game_name', ''),     # Name
                rank_value,                                    # Rank
                application_data.get('total_level', ''),      # Total
                alts_string,                                   # Alts
                str(application_data.get('discord_id', ''))   # Discord ID
            ]
            
            worksheet.append_row(row_data)
            logger.info(f"Added new entry for Discord ID: {application_data.get('discord_id')}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding new entry: {e}")
            return False
            
    def get_worksheet_headers(self, worksheet_name: str = None) -> List[str]:
        try:
            if worksheet_name:
                worksheet = self.spreadsheet.worksheet(worksheet_name)
            else:
                worksheet = self.spreadsheet.sheet1
                
            headers = worksheet.row_values(1)
            return headers
            
        except Exception as e:
            logger.error(f"Error getting headers: {e}")
            return []
            
    def test_connection(self) -> bool:
        try:
            worksheets = self.spreadsheet.worksheets()
            logger.info(f"Successfully connected to spreadsheet with {len(worksheets)} worksheets")
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

sheets_manager = GoogleSheetsManager()