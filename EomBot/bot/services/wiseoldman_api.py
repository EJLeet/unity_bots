import aiohttp
import asyncio
from typing import Dict, List, Optional, Tuple
import logging
from bot.config.config import Config

logger = logging.getLogger(__name__)

class WiseOldManAPI:
    def __init__(self):
        self.base_url = "https://api.wiseoldman.net/v2"
        self.group_id = Config.WISE_OLD_MAN_GROUP_ID
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'Content-Type': 'application/json'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_monthly_ehp_gains(self, limit: int = 3) -> List[Dict]:
        """Get top monthly EHP gains for the group"""
        try:
            url = f"{self.base_url}/groups/{self.group_id}/gained"
            params = {
                'metric': 'ehp',
                'period': 'month',
                'limit': limit
            }
            
            if not self.session:
                raise RuntimeError("WiseOldManAPI must be used as async context manager")
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Retrieved {len(data)} EHP gains from Wise Old Man API")
                    return data
                else:
                    logger.error(f"Wise Old Man API error for EHP gains: {response.status}")
                    return []
                    
        except asyncio.TimeoutError:
            logger.error("Wise Old Man API timeout for EHP gains")
            return []
        except Exception as e:
            logger.error(f"Error fetching EHP gains: {e}")
            return []
    
    async def get_monthly_ehb_gains(self, limit: int = 3) -> List[Dict]:
        """Get top monthly EHB gains for the group"""
        try:
            url = f"{self.base_url}/groups/{self.group_id}/gained"
            params = {
                'metric': 'ehb',
                'period': 'month', 
                'limit': limit
            }
            
            if not self.session:
                raise RuntimeError("WiseOldManAPI must be used as async context manager")
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Retrieved {len(data)} EHB gains from Wise Old Man API")
                    return data
                else:
                    logger.error(f"Wise Old Man API error for EHB gains: {response.status}")
                    return []
                    
        except asyncio.TimeoutError:
            logger.error("Wise Old Man API timeout for EHB gains")
            return []
        except Exception as e:
            logger.error(f"Error fetching EHB gains: {e}")
            return []
    
    async def get_monthly_gains_summary(self, limit: int = 3) -> Tuple[List[Dict], List[Dict]]:
        """Get both EHP and EHB gains in one call"""
        try:
            # Make both API calls concurrently
            ehp_task = asyncio.create_task(self.get_monthly_ehp_gains(limit))
            ehb_task = asyncio.create_task(self.get_monthly_ehb_gains(limit))
            
            ehp_gains, ehb_gains = await asyncio.gather(ehp_task, ehb_task, return_exceptions=True)
            
            # Handle any exceptions in the results
            if isinstance(ehp_gains, Exception):
                logger.error(f"EHP gains task failed: {ehp_gains}")
                ehp_gains = []
            
            if isinstance(ehb_gains, Exception):
                logger.error(f"EHB gains task failed: {ehb_gains}")
                ehb_gains = []
            
            return ehp_gains, ehb_gains
            
        except Exception as e:
            logger.error(f"Error fetching monthly gains summary: {e}")
            return [], []
    
    def format_gains_summary(self, ehp_gains: List[Dict], ehb_gains: List[Dict]) -> str:
        """Format the gains data into a readable summary"""
        if not ehp_gains and not ehb_gains:
            return "ℹ️ No Wise Old Man gains data available for this month."
        
        summary_lines = []
        summary_lines.append("🏆 **Top Monthly Gains**\n")
        
        # Format EHP gains
        if ehp_gains:
            summary_lines.append("**🧠 EHP (Efficient Hours Played):**")
            for i, entry in enumerate(ehp_gains, 1):
                try:
                    player_name = entry.get('player', {}).get('displayName', 'Unknown')
                    ehp_gained = entry.get('data', {}).get('ehp', {}).get('gained', 0)
                    
                    # Format the EHP value nicely
                    if ehp_gained >= 1:
                        ehp_str = f"{ehp_gained:.1f}"
                    else:
                        ehp_str = f"{ehp_gained:.2f}"
                    
                    summary_lines.append(f"{i}. **{player_name}** - {ehp_str} EHP")
                    
                except (KeyError, TypeError) as e:
                    logger.warning(f"Error formatting EHP entry {i}: {e}")
                    continue
        else:
            summary_lines.append("**🧠 EHP (Efficient Hours Played):**")
            summary_lines.append("No EHP data available")
        
        summary_lines.append("")  # Empty line between sections
        
        # Format EHB gains  
        if ehb_gains:
            summary_lines.append("**⚔️ EHB (Efficient Hours Bossing):**")
            for i, entry in enumerate(ehb_gains, 1):
                try:
                    player_name = entry.get('player', {}).get('displayName', 'Unknown')
                    ehb_gained = entry.get('data', {}).get('ehb', {}).get('gained', 0)
                    
                    # Format the EHB value nicely
                    if ehb_gained >= 1:
                        ehb_str = f"{ehb_gained:.1f}"
                    else:
                        ehb_str = f"{ehb_gained:.2f}"
                    
                    summary_lines.append(f"{i}. **{player_name}** - {ehb_str} EHB")
                    
                except (KeyError, TypeError) as e:
                    logger.warning(f"Error formatting EHB entry {i}: {e}")
                    continue
        else:
            summary_lines.append("**⚔️ EHB (Efficient Hours Bossing):**")
            summary_lines.append("No EHB data available")
        
        return "\n".join(summary_lines)
    
    def validate_group_id(self) -> bool:
        """Validate that group ID is configured"""
        if not self.group_id or self.group_id == 0:
            logger.error("Wise Old Man group ID not configured in environment variables")
            return False
        return True

# Standalone functions for easy usage
async def get_wise_old_man_summary(limit: int = 3) -> str:
    """Convenience function to get formatted Wise Old Man gains summary"""
    async with WiseOldManAPI() as api:
        if not api.validate_group_id():
            return "⚠️ Wise Old Man group ID not configured."
        
        ehp_gains, ehb_gains = await api.get_monthly_gains_summary(limit)
        return api.format_gains_summary(ehp_gains, ehb_gains)