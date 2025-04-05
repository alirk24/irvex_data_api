# api_client/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from django.apps import apps
import asyncio
from django.http import JsonResponse  # Import jsonResponse


from django.views import View
from django.http import JsonResponse
from django.apps import apps
import asyncio
import traceback

class DebugApiView(View):
    def get(self, request):
        """View to manually trigger API fetch and see results"""
        try:
            # Import the API client
            from api_client.services.api_client import IranExchangeClient
            from api_client.services.cache_manager import get_cache
            
            # Create client and cache instances
            api_client = IranExchangeClient()
            cache = get_cache()
            
            # Run the data fetch in the current thread (for debugging)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Try to fetch data and update cache
                data = loop.run_until_complete(api_client.fetch_all_data())
                if data:
                    loop.run_until_complete(cache.update_data(data))
                    result = {
                        'success': True,
                        'client_types': len(data.get('client_type', {})),
                        'trades': len(data.get('trade_data', {})),
                        'limits': len(data.get('limits_data', {})),
                        'cache_status': 'updated'
                    }
                else:
                    result = {
                        'success': False, 
                        'error': 'No data returned from API'
                    }
            except Exception as e:
                result = {
                    'success': False,
                    'error': str(e),
                    'traceback': traceback.format_exc()
                }
            
            return JsonResponse(result)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            })


class StockDataView(APIView):
    """API view to get stock data from the cache"""
    
    def get(self, request, stock_code=None):
        # Get the cache instance
        cache_instance = apps.get_app_config('api_client').cache_instance
        
        # Use the event loop to run the async function
        loop = asyncio.get_event_loop()
        
        if stock_code:
            # Get data for a specific stock
            data = loop.run_until_complete(cache_instance.get_stock_data(stock_code))
            return Response(data)
        else:
            # Get summary data for all stocks
            all_data = loop.run_until_complete(cache_instance.get_all_data())
            # Create a summary to avoid huge payloads
            summary = {
                code: {
                    'last_price': data['pl'][-1] if data.get('pl') and data['pl'] else None,
                    'last_update': data['time'][-1].isoformat() if data.get('time') and data['time'] else None
                } 
                for code, data in all_data.items()
            }
            return Response(summary)


class DiagnosticView(View):
    def get(self, request):
        from api_client.services.cache_manager import get_cache
        cache_instance = get_cache()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Get a summary of the cache
        all_data = loop.run_until_complete(cache_instance.get_all_data())
        
        stats = {
            'total_stocks': len(all_data),
            'last_update': cache_instance.last_update.isoformat() if cache_instance.last_update else None,
            'sample_stocks': [],
        }
        
        # Add sample data for the first 5 stocks
        for i, (code, data) in enumerate(all_data.items()):
            if i >= 5:
                break
                
            stats['sample_stocks'].append({
                'code': code,
                'data_points': {
                    'time': len(data.get('time', [])),
                    'price': len(data.get('pl', [])),
                    'volume': len(data.get('tvol', []))
                },
                'last_price': data.get('pl', [-1])[-1] if data.get('pl') else None,
            })
            
        return JsonResponse(stats)