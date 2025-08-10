# Save this as fetch_data.py in the exchange_relay directory
import os
import sys
import django
import asyncio

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'exchange_relay.settings')
django.setup()

# Import after Django setup
from api_client.services.api_client import IranExchangeClient
from api_client.services.cache_manager import get_cache

async def fetch_data():
    print("Starting data fetch...")
    
    # Create the API client
    api_client = IranExchangeClient()
    
    # Get the shared cache instance
    cache = get_cache()
    
    # Fetch data
    print("Fetching data from Iran Exchange API...")
    data = await api_client.fetch_all_data()
    
    if data:
        print(f"Successfully fetched data:")
        print(f"- Client types: {len(data.get('client_type', {}))}")
        print(f"- Trade data: {len(data.get('trade_data', {}))}")
        print(f"- Limits data: {len(data.get('limits_data', {}))}")
        
        # Update the cache
        print("Updating cache...")
        await cache.update_data(data)
        print("Cache updated successfully")
    else:
        print("No data returned from API")

if __name__ == "__main__":
    # Run the fetch operation
    asyncio.run(fetch_data())