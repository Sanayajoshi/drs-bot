import asyncio
import logging
import re
from typing import Optional, List, Dict, Tuple
import aiohttp
from bs4 import BeautifulSoup


class BonusService:
    BASE_URL = "https://ws.tsl.rocks/corp/"
    
    def __init__(self, db):
        self.db = db
        self.logger = logging.getLogger("bonus_service")
        self.session: aiohttp.ClientSession = None
        self._update_task = None
        
    async def initialize(self):
        """Initialize the aiohttp session."""
        if not self.session:
            self.session = aiohttp.ClientSession()
            self.logger.info("BonusService initialized with aiohttp session")
    
    async def close(self):
        """Close the aiohttp session."""
        if self.session:
            await self.session.close()
            self.logger.info("BonusService closed aiohttp session")
    
    async def fetch_corp_page(self, corp_id: str) -> Tuple[bool, Optional[str], Optional[int]]:
        """
        Fetch corporation page and extract name and bonus.
        Returns: (success, corp_name, bonus_pct)
        """
        url = f"{self.BASE_URL}{corp_id}/"
        try:
            async with self.session.get(url, timeout=15) as response:
                if response.status != 200:
                    self.logger.warning(f"Failed to fetch {url}: HTTP {response.status}")
                    return False, None, None
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extract corporation name (usually in h1)
                corp_name = None
                h1 = soup.find('h1')
                if h1:
                    corp_name = h1.get_text(strip=True)
                
                # Extract bonus percentage
                bonus_pct = None
                # Look for text containing "Bonus" and "%"
                for element in soup.find_all(['div', 'p', 'span', 'h2', 'h3']):
                    text = element.get_text(strip=True)
                    if 'Bonus' in text and '%' in text:
                        # Match pattern like "Bonus ✅ 54%" or "Bonus 54%"
                        match = re.search(r'Bonus.*?(\d+)%', text)
                        if match:
                            bonus_pct = int(match.group(1))
                            break
                
                return True, corp_name, bonus_pct
                
        except asyncio.TimeoutError:
            self.logger.error(f"Timeout fetching {url}")
            return False, None, None
        except Exception as e:
            self.logger.error(f"Error fetching {url}: {e}")
            return False, None, None
    
    async def validate_corp_id(self, corp_id: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a corporation ID by checking if the page exists.
        Returns: (is_valid, corp_name)
        """
        # Validate format: 64 hex characters
        if not re.match(r'^[a-f0-9]{64}$', corp_id):
            return False, None
        
        success, corp_name, _ = await self.fetch_corp_page(corp_id)
        return success, corp_name
    
    async def add_corp(self, corp_id: str, custom_name: str = None) -> dict:
        """
        Add a corporation to track.
        Returns result dict with status and message.
        """
        # Validate the corp ID
        is_valid, corp_name = await self.validate_corp_id(corp_id)
        if not is_valid:
            return {
                "success": False, 
                "message": "Invalid corporation ID - page not found or invalid format"
            }
        
        # Use custom name if provided, otherwise use scraped name
        final_name = custom_name or corp_name or "Unknown"
        
        # Try to fetch bonus
        success, _, bonus_pct = await self.fetch_corp_page(corp_id)
        
        # Add to database
        if self.db.add_tracked_corp(corp_id, final_name, bonus_pct):
            if bonus_pct is not None:
                return {
                    "success": True,
                    "message": f"Added **{final_name}** with {bonus_pct}% bonus",
                    "corp_name": final_name,
                    "bonus": bonus_pct
                }
            else:
                return {
                    "success": True,
                    "message": f"Added **{final_name}** (bonus not found yet - will retry hourly)",
                    "corp_name": final_name,
                    "bonus": None
                }
        
        return {"success": False, "message": "Database error while adding corporation"}
    
    async def remove_corp(self, corp_id: str) -> dict:
        """Remove a corporation from tracking."""
        if self.db.remove_tracked_corp(corp_id):
            return {"success": True, "message": f"Removed corporation `{corp_id}`"}
        return {"success": False, "message": "Corporation not found or database error"}
    
    async def fetch_corp_bonus_only(self, corp_id: str) -> Optional[int]:
        """Fetch only the bonus percentage for a corporation."""
        success, _, bonus_pct = await self.fetch_corp_page(corp_id)
        return bonus_pct if success else None
    
    async def update_all_bonuses(self) -> int:
        """Update bonuses for all active tracked corporations."""
        corp_ids = self.db.get_all_active_corp_ids()
        if not corp_ids:
            self.logger.info("No corporations to update")
            return 0
        
        updated = 0
        for corp_id in corp_ids:
            try:
                success, _, bonus_pct = await self.fetch_corp_page(corp_id)
                
                if success and bonus_pct is not None:
                    if self.db.update_corp_bonus(corp_id, bonus_pct):
                        updated += 1
                        self.logger.debug(f"Updated bonus for corp {corp_id[:16]}...: {bonus_pct}%")
                elif success and bonus_pct is None:
                    # Page exists but no bonus found
                    self.db.set_corp_fetch_error(corp_id, "No bonus found on page")
                else:
                    # Fetch failed
                    self.db.set_corp_fetch_error(corp_id, "Page fetch failed")
                
                # Be gentle to the website
                await asyncio.sleep(0.5)
                
            except Exception as e:
                self.logger.error(f"Error updating corp {corp_id}: {e}")
                self.db.set_corp_fetch_error(corp_id, str(e)[:100])
        
        self.logger.info(f"Updated {updated} corporation bonuses")
        return updated
    
    def get_active_bonuses(self) -> List[Dict]:
        """Get all active corporations with bonuses, sorted by bonus descending."""
        return self.db.get_active_corps_with_bonus()
    
    def get_all_tracked(self) -> List[Dict]:
        """Get all tracked corporations (for admin listing)."""
        return self.db.get_tracked_corps(active_only=True)
