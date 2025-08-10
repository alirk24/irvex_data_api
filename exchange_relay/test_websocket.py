import os
import sys
import django
import asyncio
import json

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'exchange_relay.settings')
django.setup()

# Import after Django setup
from socket_api.consumers import ExchangeDataConsumer
from api_client.services.cache_manager import get_cache

async def test_websocket():
    print("Testing WebSocket consumer...")
    
    # Get the shared cache instance
    cache = get_cache()
    
    # Get all cached data
    data = await cache.get_all_data()
    print(f"Cache contains data for {len(data)} stocks")
    
    # Create a consumer instance
    consumer = ExchangeDataConsumer()
    # Set the cache instance directly (this bypasses the normal WebSocket connection)
    consumer.cache_instance = cache
    
    # Get a sample stock code if available
    sample_stock = None
    if data:
        sample_stock = list(data.keys())[0]
        print(f"Sample stock code: {sample_stock}")
        
        # Get sample stock data
        stock_data = await cache.get_stock_data(sample_stock)
        print(f"Sample stock data fields: {list(stock_data.keys())}")
        
        # Test converting stock data to the format expected by the WebSocket client
        if stock_data and stock_data.get('time') and stock_data['time']:
            sample = {
                'timestamp': stock_data['time'][-1].isoformat() if stock_data.get('time') and stock_data['time'] else None,
                'price': {
                    'last': stock_data['pl'][-1] if stock_data.get('pl') and stock_data['pl'] else None,
                    'closing': stock_data['pc'][-1] if stock_data.get('pc') and stock_data['pc'] else None,
                    'min': stock_data['pmin'][-1] if stock_data.get('pmin') and stock_data['pmin'] else None,
                    'max': stock_data['pmax'][-1] if stock_data.get('pmax') and stock_data['pmax'] else None
                },
                'volume': stock_data['tvol'][-1] if stock_data.get('tvol') and stock_data['tvol'] else None,
                'value': stock_data['tval'][-1] if stock_data.get('tval') and stock_data['tval'] else None,
                'transactions': stock_data['tno'][-1] if stock_data.get('tno') and stock_data['tno'] else None,
            }
            print(f"Sample WebSocket data: {json.dumps(sample, indent=2)}")
        else:
            print("Stock data is missing time field or is empty")
    else:
        print("No stocks found in cache")

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_websocket())