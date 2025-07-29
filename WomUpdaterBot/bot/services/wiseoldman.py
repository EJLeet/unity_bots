import aiohttp
import logging
from typing import Dict, Any, Optional

class WiseOldManAPI:
    """Service class for WiseOldMan API integration"""
    
    def __init__(self, api_key: str, group_id: str):
        self.api_key = api_key
        self.group_id = group_id
        self.base_url = "https://api.wiseoldman.net/v2"
        self.logger = logging.getLogger("wom_bot.api")
        
    async def update_all_members(self) -> Dict[str, Any]:
        """
        Trigger update for all members in the group
        Returns response data or raises exception
        """
        url = f"{self.base_url}/groups/{self.group_id}/update-all"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        self.logger.info(f"Triggering update for WOM group {self.group_id}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers) as response:
                    response_data = await response.json()
                    
                    if response.status == 200:
                        self.logger.info("WOM update request successful")
                        return {
                            "success": True,
                            "message": "Update triggered successfully",
                            "data": response_data
                        }
                    else:
                        error_msg = f"WOM API error: {response.status} - {response_data}"
                        self.logger.error(error_msg)
                        return {
                            "success": False,
                            "message": error_msg,
                            "status_code": response.status
                        }
                        
        except aiohttp.ClientError as e:
            error_msg = f"Network error calling WOM API: {str(e)}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "error": str(e)
            }
        except Exception as e:
            error_msg = f"Unexpected error calling WOM API: {str(e)}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "error": str(e)
            }
    
    async def get_group_info(self) -> Dict[str, Any]:
        """Get group information for verification"""
        url = f"{self.base_url}/groups/{self.group_id}"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    response_data = await response.json()
                    
                    if response.status == 200:
                        return {
                            "success": True,
                            "data": response_data
                        }
                    else:
                        return {
                            "success": False,
                            "message": f"Failed to get group info: {response.status}",
                            "status_code": response.status
                        }
                        
        except Exception as e:
            return {
                "success": False,
                "message": f"Error getting group info: {str(e)}",
                "error": str(e)
            }