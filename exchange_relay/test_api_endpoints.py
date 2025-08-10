#!/usr/bin/env python
"""
Test script to verify that API endpoints are working correctly
Run with: python test_api_endpoints.py
"""

import os
import sys
import django
import asyncio
import requests

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'exchange_relay.settings')
django.setup()

# Import after Django setup
from api_client.services.api_client import IranExchangeClient
from api_client.services.cache_manager import get_cache
from api_client.services.stock_metadata import get_metadata_client

def test_cache_and_metadata():
    """Test that cache and metadata services are working"""
    print("Testing cache and metadata services...")
    
    # Test cache instance
    cache = get_cache()
    print(f"✓ Cache instance created: {type(cache)}")
    
    # Test metadata client
    metadata_client = get_metadata_client()
    print(f"✓ Metadata client created: {type(metadata_client)}")
    
    # Test that metadata client can get stock IDs (this should work without async)
    try:
        stock_ids = metadata_client.get_all_ids_and_names()
        print(f"✓ Stock IDs available: {len(stock_ids)} stocks")
        return True
    except Exception as e:
        print(f"✗ Error getting stock IDs: {e}")
        return False

async def test_async_operations():
    """Test async operations"""
    print("\nTesting async operations...")
    
    cache = get_cache()
    
    try:
        # Test getting all data (should return empty dict initially)
        all_data = await cache.get_all_data()
        print(f"✓ Cache.get_all_data() works: {len(all_data)} stocks in cache")
        
        # Test getting all metadata
        metadata = await cache.get_all_metadata()
        print(f"✓ Cache.get_all_metadata() works: {len(metadata)} metadata entries")
        
        # Test getting stock summary
        summary = await cache.get_all_stocks_summary()
        print(f"✓ Cache.get_all_stocks_summary() works: {len(summary)} stock summaries")
        
        return True
    except Exception as e:
        print(f"✗ Error in async operations: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_endpoints():
    """Test API endpoints via HTTP requests"""
    print("\nTesting API endpoints...")
    
    base_url = "http://127.0.0.1:8000"  # Adjust if running on different host/port
    
    endpoints = [
        "/api/stock-ids/",
        "/api/stocks/",
        "/api/metadata/",
        "/diagnostic/",
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✓ {endpoint} - Status: {response.status_code}, Data keys: {list(data.keys()) if isinstance(data, dict) else 'non-dict'}")
            else:
                print(f"✗ {endpoint} - Status: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"? {endpoint} - Server not running (ConnectionError)")
        except Exception as e:
            print(f"✗ {endpoint} - Error: {e}")

if __name__ == "__main__":
    print("=== API Endpoint Testing ===\n")
    
    # Test 1: Basic cache and metadata services
    cache_ok = test_cache_and_metadata()
    
    # Test 2: Async operations
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    async_ok = loop.run_until_complete(test_async_operations())
    
    # Test 3: HTTP API endpoints (requires server to be running)
    test_api_endpoints()
    
    print(f"\n=== Summary ===")
    print(f"Cache/Metadata: {'✓' if cache_ok else '✗'}")
    print(f"Async operations: {'✓' if async_ok else '✗'}")
    print("HTTP endpoints: Check results above")
    
    if cache_ok and async_ok:
        print("\n✓ All internal tests passed! The async/cache issues should be fixed.")
        print("If HTTP endpoints show ConnectionError, start the Django server with:")
        print("python manage.py runserver")
    else:
        print("\n✗ Some internal tests failed. Check the error messages above.")
