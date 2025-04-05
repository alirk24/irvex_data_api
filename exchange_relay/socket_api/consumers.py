# socket_api/consumers.py
import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from django.apps import apps
from api_client.services.cache_manager import get_cache

class ExchangeDataConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subscribed_stocks = set()
        self.update_task = None
        # Get the shared cache instance
        self.cache_instance = get_cache()
        
    async def connect(self):
        print("Client connecting to WebSocket")
        await self.accept()
        print("Client connected successfully")
        await self.send(text_data=json.dumps({
            'type': 'connection_status',
            'status': 'connected',
            'message': 'Connected to exchange data service'
        }))
    
    async def disconnect(self, close_code):
        print(f"Client disconnected with code: {close_code}")
        # Cancel the update task if it's running
        if self.update_task:
            self.update_task.cancel()
            
    async def receive(self, text_data):
        print(f"Received message: {text_data}")
        try:
            data = json.loads(text_data)
            
            if data.get('type') == 'subscribe':
                # Handle subscription request
                stocks = data.get('stocks', [])
                if not isinstance(stocks, list):
                    stocks = [stocks]  # Convert single item to list
                
                # Update our subscription set
                self.subscribed_stocks.update(stocks)
                
                await self.send(text_data=json.dumps({
                    'type': 'subscription_update',
                    'status': 'success',
                    'subscribed_stocks': list(self.subscribed_stocks)
                }))
                
                # Start sending updates if not already started
                if not self.update_task or self.update_task.done():
                    self.update_task = asyncio.create_task(self.send_stock_updates())
            
            elif data.get('type') == 'unsubscribe':
                # Handle unsubscription request
                stocks = data.get('stocks', [])
                if not isinstance(stocks, list):
                    stocks = [stocks]
                
                # Remove from our subscription set
                for stock in stocks:
                    self.subscribed_stocks.discard(stock)
                
                await self.send(text_data=json.dumps({
                    'type': 'subscription_update',
                    'status': 'success',
                    'subscribed_stocks': list(self.subscribed_stocks)
                }))
                
                # If no more subscriptions, cancel the update task
                if not self.subscribed_stocks and self.update_task:
                    self.update_task.cancel()
                    self.update_task = None
            
            else:
                # Echo back unknown message types
                await self.send(text_data=json.dumps({
                    'type': 'echo',
                    'data': data
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Error processing request: {str(e)}'
            }))
    
    async def send_stock_updates(self):
        """Background task to send stock updates to the client"""
        try:
            while True:
                if not self.subscribed_stocks:
                    # No stocks to update, sleep briefly and check again
                    await asyncio.sleep(1)
                    continue
                
                # Check if we have any data at all in the cache
                all_data = await self.cache_instance.get_all_data()
                if not all_data:
                    print("No data in cache yet, waiting for initial data load...")
                    await asyncio.sleep(5)  # Wait longer for initial data
                    continue
                
                # Debug print to check if data is available
                missing_stocks = []
                for stock_code in self.subscribed_stocks:
                    stock_data = await self.cache_instance.get_stock_data(stock_code)
                    if not stock_data or not stock_data.get('time'):
                        missing_stocks.append(stock_code)
                
                if missing_stocks:
                    print(f"Missing data for stocks: {missing_stocks}")
                
                # Gather updates for all subscribed stocks
                updates = {}
                for stock_code in self.subscribed_stocks:
                    # Get the latest data for this stock
                    stock_data = await self.cache_instance.get_stock_data(stock_code)
                    
                    if stock_data and stock_data.get('time') and stock_data['time']:
                        # Create a summary with the most important fields
                        updates[stock_code] = {
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
                            'client_type': {
                                'buy_legal': stock_data['Buy_I_Volume'][-1] if stock_data.get('Buy_I_Volume') and stock_data['Buy_I_Volume'] else None,
                                'buy_natural': stock_data['Buy_N_Volume'][-1] if stock_data.get('Buy_N_Volume') and stock_data['Buy_N_Volume'] else None,
                                'sell_legal': stock_data['Sell_I_Volume'][-1] if stock_data.get('Sell_I_Volume') and stock_data['Sell_I_Volume'] else None,
                                'sell_natural': stock_data['Sell_N_Volume'][-1] if stock_data.get('Sell_N_Volume') and stock_data['Sell_N_Volume'] else None
                            }
                        }
                
                # Only send if we have updates
                if updates:
                    print(f"Sending updates for {len(updates)} stocks")
                    await self.send(text_data=json.dumps({
                        'type': 'stock_update',
                        'timestamp': asyncio.get_event_loop().time(),
                        'data': updates
                    }))
                else:
                    print("No updates to send")
                
                # Wait before sending the next update (2 seconds)
                await asyncio.sleep(2)
                
        except asyncio.CancelledError:
            # Task was cancelled, clean up
            print("Update task cancelled")
            
        except Exception as e:
            # Log any errors
            print(f"Error in send_stock_updates: {e}")
            import traceback
            traceback.print_exc()
            # Try to notify the client
            try:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'Update service encountered an error: {str(e)}'
                }))
            except:
                pass