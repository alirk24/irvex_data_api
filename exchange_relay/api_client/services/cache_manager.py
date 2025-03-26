import asyncio
import logging
from typing import Dict, Any
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)

# Global singleton instance
_instance = None

class ExchangeDataCache:
    def __init__(self):
        # Initialize the main data container
        self.data = {}
        # Create timestamps for tracking data age
        self.last_update = None
        # Set up locks for thread safety
        self._lock = asyncio.Lock()
        
    # Your existing cache methods...

class ExchangeDataCache:
    def __init__(self):
        # Initialize the main data container
        self.data = {}
        # Create timestamps for tracking data age
        self.last_update = None
        # Set up locks for thread safety
        self._lock = asyncio.Lock()
        
    async def initialize_stock(self, stock_id):
        """Initialize data structure for a new stock if it doesn't exist"""
        async with self._lock:
            if stock_id not in self.data:
                self.data[stock_id] = self._create_empty_stock_structure()
    
    def _create_empty_stock_structure(self):
        """Create an empty data structure for a stock"""
        # This matches the structure from the provided code
        return {
            # Time-related fields
            'time': [],
            'tim_index': [],
            
            # Price fields
            'pl': [],      # PDrCotVal
            'pc': [],      # PClosing
            'pf': [],      # PriceFirst
            'py': [],      # PriceYesterday
            'pmax': [],    # PriceMax
            'pmin': [],    # PriceMin
            
            # Transaction fields
            'tno': [],     # ZTotTran
            'tvol': [],    # QTotTran5J
            'tval': [],    # QTotCap
            
            # Demand and supply fields for 5 price levels
            **{f'{side}{num}': [] for side in ['zd', 'qd', 'pd', 'po', 'qo', 'zo'] for num in range(1, 6)},
            
            # Client type fields
            'Buy_I_Volume': [],
            'Buy_N_Volume': [],
            'Sell_I_Volume': [],
            'Sell_N_Volume': [],
            'Buy_CountI': [],
            'Buy_CountN': [],
            'Sell_CountI': [],
            'Sell_CountN': [],
            
            # Derived metrics
            'sa_kharid': [],
            'sa_forosh': [],
            'ghodratpol': [],
            'vorodpol': [],
            'Buy_N_Ratio': [],
            
            # Weighted transaction fields - high money buy/sell
            **{f'{prefix}-{field}': ([datetime.now().strftime('%H:%M:%S.%f')] if field == 'time' else [0]) 
               for prefix in ['hmb', 'hms', 'wmb', 'wms', 'Nhmb', 'Nhms'] 
               for field in ['time', 'vol', 'number', 'value', 'volume-comulative', 'value-comulative', 'count']}
        }
    
    async def update_data(self, api_data):
        """Update the cache with new data from the API"""
        self.last_update = datetime.now()
        
        # Process the data similar to the provided code's main_api function
        client_type_data = api_data['client_type']
        trade_data = api_data['trade_data']
        limits_data = api_data['limits_data']
        
        # Process and update cache for each stock
        for stock_code in trade_data:
            await self.process_stock_data(
                stock_code, 
                trade_data.get(stock_code), 
                client_type_data.get(stock_code), 
                limits_data.get(stock_code)
            )
    
    async def process_stock_data(self, stock_code, trade_item, client_type_item, limits_item):
        """Process and update data for a single stock"""
        # Initialize the stock if it doesn't exist
        await self.initialize_stock(stock_code)
        
        async with self._lock:
            # Update logic would go here, similar to the provided code
            # This is a simplified placeholder - would need to adapt the complex logic
            # from the original code based on your specific requirements
            
            # Example of a simple update:
            if trade_item:
                # Only update if we have newer data than what's already stored
                if not self.data[stock_code]['tno'] or float(trade_item['ZTotTran']) > self.data[stock_code]['tno'][-1]:
                    self.data[stock_code]['time'].append(datetime.now())
                    
                    # Update basic price and volume data
                    self.data[stock_code]['pl'].append(float(trade_item['PDrCotVal']))
                    self.data[stock_code]['pc'].append(float(trade_item['PClosing']))
                    self.data[stock_code]['pf'].append(float(trade_item['PriceFirst']))
                    self.data[stock_code]['py'].append(float(trade_item['PriceYesterday']))
                    self.data[stock_code]['pmax'].append(float(trade_item['PriceMax']))
                    self.data[stock_code]['pmin'].append(float(trade_item['PriceMin']))
                    self.data[stock_code]['tno'].append(float(trade_item['ZTotTran']))
                    self.data[stock_code]['tvol'].append(float(trade_item['QTotTran5J']))
                    self.data[stock_code]['tval'].append(float(trade_item['QTotCap']))
                    
                    # More updates would be needed based on the original code
            
            # Similar updates for client_type_item and limits_item
    
    async def get_stock_data(self, stock_code):
        """Get data for a specific stock"""
        async with self._lock:
            return self.data.get(stock_code, {})
    
    async def get_all_data(self):
        """Get all cached data"""
        async with self._lock:
            return self.data
        
        

def get_cache():
    """Get the singleton cache instance"""
    global _instance
    if _instance is None:
        _instance = ExchangeDataCache()
    return _instance
def get_cache_instance():
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = ExchangeDataCache()
    return _cache_instance