import asyncio
import logging
from typing import Dict, Any
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)

# Global singleton instance
_cache_instance = None

class ExchangeDataCache:
    def __init__(self):
        # Initialize the main data container
        self.data = {}
        # Create timestamps for tracking data age
        self.last_update = None
        # Set up locks for thread safety
        self._lock = asyncio.Lock()
        logger.info("Exchange data cache initialized")
    
   
    async def initialize_stock(self, stock_id):
        """Initialize data structure for a new stock if it doesn't exist"""
        async with self._lock:
            if stock_id not in self.data:
                self.data[stock_id] = self._create_empty_stock_structure()
    def _create_empty_stock_structure(self):
        """Create an empty data structure for a stock"""
        # This matches the structure from the provided code
        stock_data = {
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
        
        # Add metadata fields (these will be filled later)
        stock_data['metadata'] = {
            'name': '',
            'Full_name': '',
            'CGrValCot': '',
            'industry_num': '',
            'Exchange': '',
            'valid': '',
            'exchange_name': '',
            'industry_name': ''
        }
        
        return stock_data
    
    async def update_metadata(self, metadata):
        """Update the metadata for all stocks"""
        async with self._lock:
            self.metadata = metadata
            
            # Also update metadata for existing stocks in the cache
            for stock_id, stock_meta in metadata.items():
                if stock_id in self.data:
                    self.data[stock_id]['metadata'] = {
                        'name': stock_meta.get('name', ''),
                        'Full_name': stock_meta.get('Full_name', ''),
                        'CGrValCot': stock_meta.get('CGrValCot', ''),
                        'industry_num': stock_meta.get('industry_num', ''),
                        'Exchange': stock_meta.get('Exchange', ''),
                        'valid': stock_meta.get('valid', ''),
                        'exchange_name': stock_meta.get('exchange_name', ''),
                        'industry_name': stock_meta.get('industry_name', '')
                    }
    
    async def get_all_metadata(self):
        """Get metadata for all stocks"""
        async with self._lock:
            return self.metadata
            
    async def get_stock_metadata(self, stock_id):
        """Get metadata for a specific stock"""
        async with self._lock:
            if stock_id in self.data and 'metadata' in self.data[stock_id]:
                return self.data[stock_id]['metadata']
            elif stock_id in self.metadata:
                return self.metadata[stock_id]
            return {}
    async def update_data(self, api_data):
        """Update the cache with new data from the API"""
        if not api_data:
            logger.warning("Received empty API data, skipping update")
            return
            
        self.last_update = datetime.now()
        logger.info(f"Updating cache with new data at {self.last_update}")
        # Update metadata if available
        if 'metadata' in api_data and api_data['metadata']:
            await self.update_metadata(api_data['metadata'])
        # Process the data similar to the provided code's main_api function
        client_type_data = api_data.get('client_type', {})
        trade_data = api_data.get('trade_data', {})
        limits_data = api_data.get('limits_data', {})
        
        logger.info(f"Processing data for {len(trade_data)} stocks")
        
        # Process and update cache for each stock
        for stock_code in trade_data:
            await self.process_stock_data(
                stock_code, 
                trade_data.get(stock_code), 
                client_type_data.get(stock_code), 
                limits_data.get(stock_code)
            )
        
        logger.info("Cache update completed")
    
    async def process_stock_data(self, stock_code, trade_item, client_type_item, limits_item):
        """Process and update data for a single stock"""
        # Initialize the stock if it doesn't exist
        await self.initialize_stock(stock_code)
        
        async with self._lock:
            current_time = datetime.now()
            
            # Only proceed if we have trade data
            if trade_item:
                # Update basic price and volume data
                self.data[stock_code]['time'].append(current_time)
                
                self.data[stock_code]['pl'].append(float(trade_item.get('PDrCotVal', 0)))
                self.data[stock_code]['pc'].append(float(trade_item.get('PClosing', 0)))
                self.data[stock_code]['pf'].append(float(trade_item.get('PriceFirst', 0)))
                self.data[stock_code]['py'].append(float(trade_item.get('PriceYesterday', 0)))
                self.data[stock_code]['pmax'].append(float(trade_item.get('PriceMax', 0)))
                self.data[stock_code]['pmin'].append(float(trade_item.get('PriceMin', 0)))
                self.data[stock_code]['tno'].append(float(trade_item.get('ZTotTran', 0)))
                self.data[stock_code]['tvol'].append(float(trade_item.get('QTotTran5J', 0)))
                self.data[stock_code]['tval'].append(float(trade_item.get('QTotCap', 0)))
                
                # Update client type data if available
                if client_type_item:
                    self.data[stock_code]['Buy_I_Volume'].append(float(client_type_item.get('Buy_I_Volume', 0)))
                    self.data[stock_code]['Buy_N_Volume'].append(float(client_type_item.get('Buy_N_Volume', 0)))
                    self.data[stock_code]['Sell_I_Volume'].append(float(client_type_item.get('Sell_I_Volume', 0)))
                    self.data[stock_code]['Sell_N_Volume'].append(float(client_type_item.get('Sell_N_Volume', 0)))
                    self.data[stock_code]['Buy_CountI'].append(float(client_type_item.get('Buy_CountI', 0)))
                    self.data[stock_code]['Buy_CountN'].append(float(client_type_item.get('Buy_CountN', 0)))
                    self.data[stock_code]['Sell_CountI'].append(float(client_type_item.get('Sell_CountI', 0)))
                    self.data[stock_code]['Sell_CountN'].append(float(client_type_item.get('Sell_CountN', 0)))
                    
                    # Calculate derived metrics
                    buy_n = float(client_type_item.get('Buy_N_Volume', 0))
                    buy_i = float(client_type_item.get('Buy_I_Volume', 0))
                    sell_n = float(client_type_item.get('Sell_N_Volume', 0))
                    sell_i = float(client_type_item.get('Sell_I_Volume', 0))
                    
                    # Calculate money power and other metrics
                    sa_kharid = buy_i + buy_n
                    sa_forosh = sell_i + sell_n
                    
                    if sa_forosh != 0:
                        ghodratpol = sa_kharid / sa_forosh
                    else:
                        ghodratpol = 0
                        
                    if buy_i + buy_n != 0:
                        buy_n_ratio = buy_n / (buy_i + buy_n)
                    else:
                        buy_n_ratio = 0
                    
                    # Store calculated metrics
                    self.data[stock_code]['sa_kharid'].append(sa_kharid)
                    self.data[stock_code]['sa_forosh'].append(sa_forosh)
                    self.data[stock_code]['ghodratpol'].append(ghodratpol)
                    self.data[stock_code]['Buy_N_Ratio'].append(buy_n_ratio)
                
                # Update limits data if available
                if limits_item:
                    # Process best limit data
                    for i in range(1, 6):
                        if str(i) in limits_item:
                            limit_data = limits_item[str(i)]
                            self.data[stock_code][f'zd{i}'].append(float(limit_data.get('ZOrdMeDem', 0)))
                            self.data[stock_code][f'qd{i}'].append(float(limit_data.get('QTitMeDem', 0)))
                            self.data[stock_code][f'pd{i}'].append(float(limit_data.get('PMeDem', 0)))
                            self.data[stock_code][f'po{i}'].append(float(limit_data.get('PMeOf', 0)))
                            self.data[stock_code][f'qo{i}'].append(float(limit_data.get('QTitMeOf', 0)))
                            self.data[stock_code][f'zo{i}'].append(float(limit_data.get('ZOrdMeOf', 0)))
                        else:
                            # If this limit level doesn't exist, add zeros
                            self.data[stock_code][f'zd{i}'].append(0)
                            self.data[stock_code][f'qd{i}'].append(0)
                            self.data[stock_code][f'pd{i}'].append(0)
                            self.data[stock_code][f'po{i}'].append(0)
                            self.data[stock_code][f'qo{i}'].append(0)
                            self.data[stock_code][f'zo{i}'].append(0)
    
    async def get_stock_data(self, stock_code):
        """Get data for a specific stock"""
        async with self._lock:
            if stock_code in self.data:
                return self.data[stock_code]
            else:
                logger.warning(f"Stock code {stock_code} not found in cache")
                return {}
    
    async def get_all_data(self):
        """Get all cached data"""
        async with self._lock:
            return self.data


    async def get_all_stocks_summary(self):
        """Get a summary of all stocks with the most recent values"""
        async with self._lock:
            summary = {}
            
            for stock_id, stock_data in self.data.items():
                # Only include stocks that have actual data
                if stock_data and stock_data.get('time') and stock_data['time']:
                    # Calculate price change
                    last_price = stock_data['pl'][-1] if stock_data.get('pl') and stock_data['pl'] else 0
                    yesterday_price = stock_data['py'][-1] if stock_data.get('py') and stock_data['py'] else 0
                    price_change = last_price - yesterday_price if yesterday_price > 0 else 0
                    
                    # Get metadata including the new fields (pe, tmax, tmin, nav)
                    metadata = stock_data.get('metadata', self.metadata.get(stock_id, {}))
                    
                    # Create a summary with just the most recent values
                    summary[stock_id] = {
                        'pf': stock_data['pf'][-1] if stock_data.get('pf') and stock_data['pf'] else None,
                        'pl': last_price,
                        'pc': stock_data['pc'][-1] if stock_data.get('pc') and stock_data['pc'] else None,
                        'tval': stock_data['tval'][-1] if stock_data.get('tval') and stock_data['tval'] else None,
                        'py': yesterday_price,
                        'pchange': price_change,
                        'pmin': stock_data['pmin'][-1] if stock_data.get('pmin') and stock_data['pmin'] else None,
                        'pmax': stock_data['pmax'][-1] if stock_data.get('pmax') and stock_data['pmax'] else None,
                        
                        # Add the order book data
                        'qd1': stock_data['qd1'][-1] if stock_data.get('qd1') and stock_data['qd1'] else None,
                        'pd1': stock_data['pd1'][-1] if stock_data.get('pd1') and stock_data['pd1'] else None,
                        'qo1': stock_data['qo1'][-1] if stock_data.get('qo1') and stock_data['qo1'] else None,
                        'po1': stock_data['po1'][-1] if stock_data.get('po1') and stock_data['po1'] else None,
                        
                        'metadata': metadata
                    }
                    
            return summary
def get_cache():
    """Get the singleton cache instance"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = ExchangeDataCache()
    return _cache_instance