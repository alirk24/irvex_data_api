# api_client/services/stock_metadata.py
import httpx
import asyncio
import json
import logging
from datetime import datetime, timedelta, time
import pytz
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class StockMetadataClient:
    def __init__(self):
        self.metadata_url = "http://213.232.126.219:2624/dideban/livetseids/"
        self.details_url = "http://213.232.126.219:2624/dideban/silver/stk_details/"
        self.last_update = None
        self.metadata = {}
        self.detail_data = {}
        self.update_interval = timedelta(days=1)  # Update once per day
        self.iran_timezone = pytz.timezone('Asia/Tehran')
        
    async def should_update(self, force=False):
        """Determine if we should update the metadata based on time"""
        if force:
            return True
            
        # If we've never updated, we should update
        if not self.last_update:
            return True
            
        # Get current time in Iran timezone
        now = datetime.now()
        iran_now = now.astimezone(self.iran_timezone) if now.tzinfo else self.iran_timezone.localize(now)
        
        # Define target update time (8 AM Iran time)
        update_time = time(8, 0, 0)
        
        # Check if it's past 8 AM today and we haven't updated today
        last_update_iran = self.last_update.astimezone(self.iran_timezone) if self.last_update.tzinfo else self.iran_timezone.localize(self.last_update)
        should_update = (
            iran_now.time() >= update_time and 
            (last_update_iran.date() < iran_now.date() or 
             (last_update_iran.date() == iran_now.date() and last_update_iran.time() < update_time))
        )
        
        logger.info(f"Should update metadata: {should_update} (Current Iran time: {iran_now.strftime('%Y-%m-%d %H:%M:%S')})")
        return should_update
        
    async def fetch_metadata(self, force=False):
        """Fetch stock metadata from the API"""
        # Only fetch if we should update
        if not await self.should_update(force):
            logger.info("Using cached metadata (last updated: %s)", self.last_update)
            return self.metadata
            
        logger.info("Fetching stock metadata from %s", self.metadata_url)
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.metadata_url, timeout=30.0)
                
                if response.status_code == 200:
                    # Parse JSON response
                    # The API returns an array with a single object
                    metadata_list = response.json()
                    if metadata_list and isinstance(metadata_list, list) and len(metadata_list) > 0:
                        # First item in the list contains all stock metadata
                        self.metadata = metadata_list[0]
                        # Also fetch the details data with PE, tmax, tmin, NAV
                        await self.fetch_stock_details()
                        
                        # Update last_update time with Iran timezone
                        now = datetime.now()
                        self.last_update = now.astimezone(self.iran_timezone) if now.tzinfo else self.iran_timezone.localize(now)
                        
                        logger.info("Successfully fetched metadata for %d stocks", len(self.metadata))
                        return self.metadata
                    else:
                        logger.error("Invalid metadata format received")
                else:
                    logger.error("Failed to fetch metadata: HTTP %d", response.status_code)
            
        except Exception as e:
            logger.error("Error fetching stock metadata: %s", str(e))
            import traceback
            logger.error(traceback.format_exc())
        
        return self.metadata  # Return whatever we have, even if unchanged
    
    async def fetch_stock_details(self):
        """Fetch additional stock details including PE, tmax, tmin, NAV"""
        logger.info("Fetching stock details from %s", self.details_url)
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.details_url, timeout=30.0)
                
                if response.status_code == 200:
                    # Parse JSON response
                    details_data = response.json()
                    if isinstance(details_data, dict) and "time" in details_data:
                        # Remove the time field and store the rest
                        details_data.pop("time", None)
                        self.detail_data = details_data
                        logger.info("Successfully fetched details for %d stocks", len(self.detail_data))
                    else:
                        logger.error("Invalid details format received")
                else:
                    logger.error("Failed to fetch stock details: HTTP %d", response.status_code)
        except Exception as e:
            logger.error("Error fetching stock details: %s", str(e))
            import traceback
            logger.error(traceback.format_exc())
    
    def get_stock_ids(self) -> List[str]:
        """Get list of all valid stock IDs"""
        return list(self.metadata.keys())
    
    def get_stock_detail(self, stock_id: str) -> Optional[Dict[str, Any]]:
        """Get additional details for a specific stock"""
        if stock_id in self.detail_data:
            return self.detail_data[stock_id]
        return None
    
    def get_simplified_metadata(self) -> Dict[str, Dict[str, Any]]:
        """Get simplified metadata with only the needed fields, including PE, tmax, tmin, NAV"""
        simplified = {}
        logger.info(f"Creating simplified metadata with {len(self.metadata)} stocks and {len(self.detail_data)} detail records")
        
        for stock_id, data in self.metadata.items():
            if data.get('valid') == '1':  # Only include valid stocks
                stock_info = {
                    'name': data.get('name', ''),
                    'Full_name': data.get('Full_name', ''),
                    'industry_num': data.get('industry_num', ''),
                    'Exchange': data.get('Exchange', ''),
                    'valid': data.get('valid', ''),
                    'exchange_name': data.get('exchange_name', ''),
                    'industry_name': data.get('industry_name', '')
                }
                
                # Add the additional details if available
                detail = self.get_stock_detail(stock_id)
                if detail:
                    # Try different field names that might be in the API response
                    pe_value = detail.get('pe', None)
                    if pe_value == "nan" or pe_value == "inf" or pe_value == "-inf":
                        pe_value = None
                        
                    tmax_value = detail.get('tmaxp', detail.get('tmax', None))
                    tmin_value = detail.get('tminp', detail.get('tmin', None))
                    nav_value = detail.get('nav', None)
                    
                    stock_info.update({
                        'pe': pe_value,
                        'tmax': tmax_value,
                        'tmin': tmin_value, 
                        'nav': nav_value
                    })
                else:
                    stock_info.update({
                        'pe': None,
                        'tmax': None,
                        'tmin': None,
                        'nav': None
                    })
                
                simplified[stock_id] = stock_info
                
        logger.info(f"Created simplified metadata with {len(simplified)} valid stocks")
        return simplified
        
    def get_stock_metadata(self, stock_id: str) -> Dict[str, Any]:
        """Get metadata for a specific stock, including PE, tmax, tmin, NAV"""
        result = {}
        
        if stock_id in self.metadata:
            data = self.metadata[stock_id]
            result = {
                'name': data.get('name', ''),
                'Full_name': data.get('Full_name', ''),
                'industry_num': data.get('industry_num', ''),
                'Exchange': data.get('Exchange', ''),
                'valid': data.get('valid', ''),
                'exchange_name': data.get('exchange_name', ''),
                'industry_name': data.get('industry_name', '')
            }
            
            # Add the additional details if available
            detail = self.get_stock_detail(stock_id)
            if detail:
                result.update({
                    'pe': detail.get('pe', '-'),
                    'tmax': detail.get('tmaxp', '-'),
                    'tmin': detail.get('tminp', '-'),
                    'nav': detail.get('nav', '-')
                })
        
        return result

# Global singleton instance
_metadata_client = None

def get_metadata_client():
    """Get the singleton metadata client instance"""
    global _metadata_client
    if _metadata_client is None:
        _metadata_client = StockMetadataClient()
    return _metadata_client