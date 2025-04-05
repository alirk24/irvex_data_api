# api_client/services/stock_metadata.py
import httpx
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class StockMetadataClient:
    def __init__(self):
        self.metadata_url = "http://213.232.126.219:2624/dideban/livetseids/"
        self.last_update = None
        self.metadata = {}
        self.update_interval = timedelta(days=1)  # Update once per day
        
    async def fetch_metadata(self, force=False):
        """Fetch stock metadata from the API"""
        # Only fetch if we haven't fetched today or if force=True
        if not force and self.last_update and datetime.now() - self.last_update < self.update_interval:
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
                        self.last_update = datetime.now()
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
    
    def get_stock_ids(self) -> List[str]:
        """Get list of all valid stock IDs"""
        return list(self.metadata.keys())
    
    def get_simplified_metadata(self) -> Dict[str, Dict[str, Any]]:
        """Get simplified metadata with only the needed fields"""
        simplified = {}
        for stock_id, data in self.metadata.items():
            if data.get('valid') == '1':  # Only include valid stocks
                simplified[stock_id] = {
                    'name': data.get('name', ''),
                    'Full_name': data.get('Full_name', ''),
                    'industry_num': data.get('industry_num', ''),
                    'Exchange': data.get('Exchange', ''),
                    'valid': data.get('valid', ''),
                    'exchange_name': data.get('exchange_name', ''),
                    'industry_name': data.get('industry_name', '')
                }
        return simplified
    
    def get_stock_metadata(self, stock_id: str) -> Dict[str, Any]:
        """Get metadata for a specific stock"""
        if stock_id in self.metadata:
            data = self.metadata[stock_id]
            return {
                'name': data.get('name', ''),
                'Full_name': data.get('Full_name', ''),
                'industry_num': data.get('industry_num', ''),
                'Exchange': data.get('Exchange', ''),
                'valid': data.get('valid', ''),
                'exchange_name': data.get('exchange_name', ''),
                'industry_name': data.get('industry_name', '')
            }
        return {}

# Global singleton instance
_metadata_client = None

def get_metadata_client():
    """Get the singleton metadata client instance"""
    global _metadata_client
    if _metadata_client is None:
        _metadata_client = StockMetadataClient()
    return _metadata_client