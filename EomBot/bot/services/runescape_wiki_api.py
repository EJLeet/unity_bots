import aiohttp
import asyncio
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from fuzzywuzzy import fuzz
import logging

logger = logging.getLogger(__name__)

class RuneScapeWikiAPI:
    def __init__(self):
        self.base_url = "https://prices.runescape.wiki/api/v1/osrs"
        self.session = None
        self._price_cache = {}
        self._cache_timestamp = None
        self.cache_duration = timedelta(hours=1)  # Cache prices for 1 hour
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'EOMBot Discord Bot - Price Lookup',
                'Content-Type': 'application/json'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_latest_prices(self, force_refresh: bool = False) -> Dict:
        """Get all current item prices from RuneScape Wiki API"""
        try:
            # Check if we have cached data that's still valid
            if (not force_refresh and 
                self._price_cache and 
                self._cache_timestamp and 
                datetime.now() - self._cache_timestamp < self.cache_duration):
                logger.debug("Using cached price data")
                return self._price_cache
            
            if not self.session:
                raise RuntimeError("RuneScapeWikiAPI must be used as async context manager")
            
            url = f"{self.base_url}/latest"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Cache the data
                    self._price_cache = data.get('data', {})
                    self._cache_timestamp = datetime.now()
                    
                    logger.info(f"Retrieved price data for {len(self._price_cache)} items")
                    return self._price_cache
                else:
                    logger.error(f"RuneScape Wiki API error: {response.status}")
                    return self._price_cache or {}
                    
        except asyncio.TimeoutError:
            logger.error("RuneScape Wiki API timeout")
            return self._price_cache or {}
        except Exception as e:
            logger.error(f"Error fetching prices: {e}")
            return self._price_cache or {}
    
    async def find_item_price(self, item_name: str) -> Optional[Tuple[str, int, int]]:
        """Find price for a specific item name
        
        Returns:
            Tuple of (matched_name, low_price, high_price) or None if not found
        """
        try:
            prices_data = await self.get_latest_prices()
            if not prices_data:
                return None
            
            # First, try to get item mapping (we'll need to create this)
            item_id = await self._find_item_id_by_name(item_name)
            if not item_id:
                return None
            
            price_info = prices_data.get(str(item_id))
            if not price_info:
                return None
            
            low_price = price_info.get('low', 0)
            high_price = price_info.get('high', 0)
            
            # Use average of high and low, or whichever is available
            if low_price and high_price:
                avg_price = (low_price + high_price) // 2
            else:
                avg_price = low_price or high_price
            
            return item_name, avg_price, high_price
            
        except Exception as e:
            logger.error(f"Error finding price for {item_name}: {e}")
            return None
    
    async def _find_item_id_by_name(self, item_name: str) -> Optional[int]:
        """Find item ID by name using fuzzy matching
        
        Note: This is a simplified implementation. In a production system,
        you'd want to maintain a proper item name -> ID mapping database.
        """
        
        # Common OSRS items mapping (you would expand this significantly)
        # This is a basic implementation - ideally you'd have a complete database
        item_name_to_id = {
            # Dragon items
            'dragon claws': 13652,
            'dragon dagger': 1215,
            'dragon longsword': 1305,
            'dragon scimitar': 4587,
            'dragon boots': 11840,
            
            # Barrows items
            'abyssal whip': 4151,
            'bandos chestplate': 11832,
            'bandos tassets': 11834,
            'armadyl helmet': 11826,
            'armadyl chestplate': 11828,
            'armadyl chainskirt': 11830,
            
            # High value items
            'twisted bow': 20997,
            'scythe of vitur': 22325,
            'avernic defender': 22322,
            'primordial boots': 13239,
            'pegasian boots': 13237,
            'eternal boots': 13235,
            
            # Raid items
            'avernic treads': 22322,  # Same as avernic defender
            'justiciar faceguard': 22326,
            'justiciar chestguard': 22327,
            'justiciar legguards': 22328,
            
            # Common supplies
            'dragon bones': 536,
            'prayer potion(4)': 2434,
            'super combat potion(4)': 12695,
            'ranging potion(4)': 2444,
            
            # Runes
            'nature rune': 561,
            'law rune': 563,
            'death rune': 560,
            'blood rune': 565,
            'soul rune': 566,
        }
        
        # Clean and normalize the item name
        clean_name = self._clean_item_name(item_name)
        
        # Try exact match first
        if clean_name in item_name_to_id:
            return item_name_to_id[clean_name]
        
        # Try fuzzy matching
        best_match = None
        best_score = 0
        
        for known_name, item_id in item_name_to_id.items():
            score = fuzz.ratio(clean_name, known_name)
            if score > best_score and score >= 80:  # 80% similarity threshold
                best_score = score
                best_match = item_id
        
        if best_match:
            logger.info(f"Fuzzy matched '{item_name}' with score {best_score}")
            return best_match
        
        logger.warning(f"No item ID found for: {item_name}")
        return None
    
    def _clean_item_name(self, name: str) -> str:
        """Clean and normalize item names for matching"""
        if not name:
            return ""
        
        # Convert to lowercase
        name = name.lower().strip()
        
        # Remove common prefixes/suffixes
        name = re.sub(r'^\d+\s*x\s*', '', name)  # Remove "1 x " prefix
        name = re.sub(r'\s*\([^)]*\)$', '', name)  # Remove parenthetical info at end
        
        # Normalize spacing
        name = re.sub(r'\s+', ' ', name).strip()
        
        # Handle common variations
        replacements = {
            'treads': 'defender',  # avernic treads -> avernic defender
            'threads': 'defender',
            'claws': 'claws',  # dragon claws
        }
        
        for old, new in replacements.items():
            if old in name:
                name = name.replace(old, new)
        
        return name
    
    async def calculate_loot_value(self, loot_items: List[str]) -> Tuple[int, List[Tuple[str, int]]]:
        """Calculate total value of a list of loot items
        
        Args:
            loot_items: List of item names/descriptions
            
        Returns:
            Tuple of (total_value, [(item_name, price), ...])
        """
        total_value = 0
        item_values = []
        
        try:
            for item_desc in loot_items:
                if not item_desc.strip():
                    continue
                
                # Extract item name and quantity
                item_name, quantity = self._parse_item_description(item_desc)
                
                # Get price for the item
                price_info = await self.find_item_price(item_name)
                if price_info:
                    matched_name, price, high_price = price_info
                    item_value = price * quantity
                    total_value += item_value
                    item_values.append((f"{quantity}x {matched_name}", item_value))
                    logger.debug(f"Valued {quantity}x {matched_name} at {item_value:,} gp")
                else:
                    # If we can't find the price, still record it
                    item_values.append((item_desc, 0))
                    logger.warning(f"Could not find price for: {item_desc}")
            
            return total_value, item_values
            
        except Exception as e:
            logger.error(f"Error calculating loot value: {e}")
            return 0, []
    
    def _parse_item_description(self, item_desc: str) -> Tuple[str, int]:
        """Parse item description to extract name and quantity
        
        Examples:
            "1 x Dragon claws" -> ("Dragon claws", 1)
            "50 x Dragon bones" -> ("Dragon bones", 50)
            "Dragon claws" -> ("Dragon claws", 1)
        """
        try:
            # Match patterns like "1 x Item name" or "50x Item name"
            match = re.match(r'^(\d+)\s*x\s*(.+)$', item_desc.strip(), re.IGNORECASE)
            if match:
                quantity = int(match.group(1))
                item_name = match.group(2).strip()
                return item_name, quantity
            else:
                # No quantity specified, assume 1
                return item_desc.strip(), 1
                
        except Exception as e:
            logger.warning(f"Error parsing item description '{item_desc}': {e}")
            return item_desc.strip(), 1
    
    def format_price(self, price: int) -> str:
        """Format price in a readable way"""
        if price >= 1_000_000:
            return f"{price / 1_000_000:.1f}M gp"
        elif price >= 1_000:
            return f"{price / 1_000:.1f}K gp"
        else:
            return f"{price:,} gp"

# Convenience functions
async def get_loot_value(loot_items: List[str]) -> Tuple[int, str]:
    """Get total loot value and formatted string
    
    Returns:
        Tuple of (total_value, formatted_string)
    """
    async with RuneScapeWikiAPI() as api:
        total_value, item_values = await api.calculate_loot_value(loot_items)
        
        if total_value > 0:
            formatted_value = api.format_price(total_value)
            return total_value, formatted_value
        else:
            return 0, "Unknown value"

async def get_single_item_price(item_name: str) -> Optional[str]:
    """Get formatted price for a single item"""
    async with RuneScapeWikiAPI() as api:
        price_info = await api.find_item_price(item_name)
        if price_info:
            matched_name, price, high_price = price_info
            return api.format_price(price)
        return None