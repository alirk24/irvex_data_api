# socket_api/consumers.py
import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from django.apps import apps
from api_client.services.cache_manager import get_cache
import logging
from datetime import datetime


logger = logging.getLogger(__name__)
# socket_api/consumers.py - Add this new consumer class
# 
# 

class AllStocksDataConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.update_task = None
        # Get the shared cache instance
        self.cache_instance = get_cache()
        
    async def connect(self):
        logger.info("Client connecting to AllStocksData WebSocket")
        await self.accept()
        logger.info("Client connected successfully to AllStocksData")
        await self.send(text_data=json.dumps({
            'type': 'connection_status',
            'status': 'connected',
            'message': 'Connected to all stocks data service'
        }))
        
        # Start sending updates immediately
        self.update_task = asyncio.create_task(self.send_all_stocks_updates())
    
    async def disconnect(self, close_code):
        logger.info(f"Client disconnected from AllStocksData with code: {close_code}")
        # Cancel the update task if it's running
        if self.update_task:
            self.update_task.cancel()
            try:
                await self.update_task
            except asyncio.CancelledError:
                logger.info("Update task cancelled successfully")
            except Exception as e:
                logger.error(f"Error cancelling update task: {e}")
            
    async def receive(self, text_data):
        """Handle incoming messages, but since this is a broadcast channel, we just acknowledge"""
        logger.info(f"Received message on AllStocksData: {text_data}")
        try:
            data = json.loads(text_data)
            
            # For now, just echo back any messages
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
    
    async def send_all_stocks_updates(self):
        """Background task to send updates for all stocks to the client"""
        try:
            # Make sure we're using the same event loop as the consumer
            loop = asyncio.get_event_loop()
            
            while True:
                try:
                    # Get optimized summary data for all stocks
                    # Use the same event loop for all async operations
                    stock_updates = await self.cache_instance.get_all_stocks_summary()
                    
                    if not stock_updates:
                        logger.info("No data in cache yet, waiting for initial data load...")
                        await asyncio.sleep(5)  # Wait longer for initial data
                        continue
                    
                    # Process stocks in smaller batches to avoid timeout issues
                    batch_size = 100
                    stock_ids = list(stock_updates.keys())
                    enhanced_updates = {}
                    
                    # Process stocks in batches
                    for i in range(0, len(stock_ids), batch_size):
                        batch_ids = stock_ids[i:i+batch_size]
                        
                        for stock_id in batch_ids:
                            stock_data = stock_updates[stock_id]
                            # Skip processing if the connection is closed
                            if not self.is_connected:
                                return
                                
                            # Start with the basic data
                            enhanced_data = stock_data.copy()
                            
                            try:
                                # Get the complete stock data to access additional fields
                                full_stock_data = await self.cache_instance.get_stock_data(stock_id)
                                
                                # Add order book data (best bid/ask)
                                if full_stock_data:
                                    # Add best bid (demand)
                                    if full_stock_data.get('qd1') and full_stock_data['qd1']:
                                        enhanced_data['qd1'] = full_stock_data['qd1'][-1] if len(full_stock_data['qd1']) > 0 else None
                                    if full_stock_data.get('pd1') and full_stock_data['pd1']:
                                        enhanced_data['pd1'] = full_stock_data['pd1'][-1] if len(full_stock_data['pd1']) > 0 else None
                                        
                                    # Add best ask (offer)
                                    if full_stock_data.get('qo1') and full_stock_data['qo1']:
                                        enhanced_data['qo1'] = full_stock_data['qo1'][-1] if len(full_stock_data['qo1']) > 0 else None
                                    if full_stock_data.get('po1') and full_stock_data['po1']:
                                        enhanced_data['po1'] = full_stock_data['po1'][-1] if len(full_stock_data['po1']) > 0 else None
                                    
                                    # Add volume and trade volume data
                                    if full_stock_data.get('tvol') and full_stock_data['tvol']:
                                        enhanced_data['tvol'] = full_stock_data['tvol'][-1] if len(full_stock_data['tvol']) > 0 else None
                                        
                                    # Some APIs use 'vol' instead of 'tvol', check for both
                                    if full_stock_data.get('vol') and full_stock_data['vol']:
                                        enhanced_data['vol'] = full_stock_data['vol'][-1] if len(full_stock_data['vol']) > 0 else None
                                    # If 'vol' isn't explicitly available, use tvol as a fallback for vol
                                    elif 'tvol' in enhanced_data and enhanced_data['tvol'] is not None:
                                        enhanced_data['vol'] = enhanced_data['tvol']
                                
                                # Make sure the metadata includes all the new fields
                                metadata = enhanced_data.get('metadata', {})
                                
                                # Explicitly add them at the top level too for easy access
                                enhanced_data['pe'] = metadata.get('pe', '-')
                                enhanced_data['tmax'] = metadata.get('tmax', '-')
                                enhanced_data['tmin'] = metadata.get('tmin', '-')
                                enhanced_data['nav'] = metadata.get('nav', '-')
                            except Exception as e:
                                logger.error(f"Error processing stock {stock_id}: {e}")
                                # Continue with basic data if there's an error
                            
                            # Store the enhanced data
                            enhanced_updates[stock_id] = enhanced_data
                            
                        # Add a small delay between batches to avoid blocking the event loop
                        await asyncio.sleep(0.01)
                    
                    # Only send if we have updates and we're still connected
                    if enhanced_updates and self.is_connected:
                        logger.info(f"Sending updates for {len(enhanced_updates)} stocks on AllStocksData channel")
                        
                        try:
                            await self.send(text_data=json.dumps({
                                'type': 'all_stocks_update',
                                'timestamp': datetime.now().isoformat(),
                                'count': len(enhanced_updates),
                                'data': enhanced_updates
                            }))
                        except Exception as send_error:
                            logger.error(f"Error sending updates: {send_error}")
                            # If we fail to send, the connection might be closed
                            if not self.is_connected:
                                return
                    elif self.is_connected:
                        logger.info("No updates to send on AllStocksData channel")
                    else:
                        return  # Exit if we're no longer connected
                    
                    # Wait before sending the next update (5 seconds)
                    await asyncio.sleep(5)
                    
                except Exception as loop_error:
                    logger.error(f"Error in update loop: {loop_error}")
                    import traceback
                    logger.error(traceback.format_exc())
                    # Continue running even after an error, with a small delay
                    await asyncio.sleep(5)
                
        except asyncio.CancelledError:
            # Task was cancelled, clean up
            logger.info("AllStocksData update task cancelled")
            raise  # Re-raise to properly handle cancellation
            
        except Exception as e:
            # Log any errors
            logger.error(f"Error in send_all_stocks_updates: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Try to notify the client if we're still connected
            if self.is_connected:
                try:
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': f'Update service encountered an error: {str(e)}'
                    }))
                except:
                    pass
    
    @property
    def is_connected(self):
        """Check if the WebSocket is still connected"""
        return hasattr(self, 'scope') and self.scope is not None and 'client' in self.scope


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
                try:
                    # Check if we have any data at all in the cache
                    all_data = await self.cache_instance.get_all_data()
                    if not all_data:
                        print("No data in cache yet, waiting for initial data load...")
                        await asyncio.sleep(2)  # Wait longer for initial data
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
                                },
                                # Include metadata
                                'metadata': stock_data.get('metadata', {})
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
                except Exception as inner_error:
                    # Log the error but continue the loop
                    print(f"Error processing updates: {inner_error}")
                    import traceback
                    traceback.print_exc()
                    # Notify the client about the error
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': f'Error processing updates: {str(inner_error)}'
                    }))
                        
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