# api_client/apps.py
from django.apps import AppConfig
import asyncio
import logging
import sys
import os
from threading import Thread

logger = logging.getLogger(__name__)

class ApiClientConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api_client'
    
    def ready(self):
        from .services.cache_manager import get_cache
        self.cache_instance = get_cache()
        # For commands like migrate, collectstatic, etc.
        if len(sys.argv) > 1 and sys.argv[1] in ['check', 'test', 'makemigrations', 'migrate', 'collectstatic']:
            logger.info("Not starting background task: Django command")
            return
            
        # Always start background task when running with Daphne
        is_daphne = 'daphne' in sys.argv[0] if len(sys.argv) > 0 else False
        
        # For runserver, only start in the main process
        is_runserver = 'runserver' in sys.argv if len(sys.argv) > 1 else False
        is_main_process = not os.environ.get('RUN_MAIN', False)

        # We want to start the background task either:
        # 1. When running with Daphne, or
        # 2. When running with runserver in the main process
        if is_daphne or (is_runserver and not is_main_process):
            logger.info(f"Starting background task: is_daphne={is_daphne}, is_runserver={is_runserver}")
            self.start_background_task()
        else:
            logger.info(f"Not starting background task: is_daphne={is_daphne}, is_runserver={is_runserver}, is_main={is_main_process}")
    
    def start_background_task(self):
        # Import here to avoid circular imports
        from .services.api_client import IranExchangeClient
        from .services.cache_manager import get_cache
        
        def run_fetcher():
            try:
                logger.info("Starting data fetcher thread")
                
                # Create a new event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Create the API client
                api_client = IranExchangeClient()
                
                # Get the shared cache instance
                cache_instance = get_cache()
                
                # Set the cache instance as a class attribute to make it accessible to views
                from django.apps import apps
                apps.get_app_config('api_client').cache_instance = cache_instance
                
                # Define the data fetching task
                async def fetch_data_job():
                    try:
                        logger.info("Fetching data from Iran Exchange API...")
                        data = await api_client.fetch_all_data()
                        if data:
                            # Update the cache with metadata first
                            if 'metadata' in data and data['metadata']:
                                await cache_instance.update_metadata(data['metadata'])
                                logger.info(f"Metadata updated successfully with {len(data['metadata'])} stocks")
                            
                            # Then update with the actual data
                            await cache_instance.update_data(data)
                            logger.info(f"Data fetched and cache updated successfully with {len(data.get('trade_data', {}))} stocks")
                        else:
                            logger.error("No data returned from API")
                    except Exception as e:
                        logger.error(f"Error fetching data: {e}")
                        import traceback
                        logger.error(traceback.format_exc())
                
                # Run the initial fetch
                logger.info("Running initial data fetch...")
                loop.run_until_complete(fetch_data_job())
                
                # Schedule regular updates (every 60 seconds)
                async def scheduled_updates():
                    while True:
                        try:
                            await asyncio.sleep(60)  # Wait 60 seconds between updates
                            await fetch_data_job()
                        except Exception as e:
                            logger.error(f"Error in scheduled update: {e}")
                            await asyncio.sleep(5)  # Wait 5 seconds before retrying after an error
                
                # Start the scheduled updates
                logger.info("Starting scheduled updates...")
                loop.create_task(scheduled_updates())
                
                # Run the event loop forever
                logger.info("Running event loop")
                loop.run_forever()
                
            except Exception as e:
                logger.error(f"Error in background thread: {e}")
                import traceback
                logger.error(traceback.format_exc())
        # Start the background thread
        logger.info("Creating background thread for data fetching")
        self.thread = Thread(target=run_fetcher, daemon=True)
        self.thread.start()
        logger.info("Background thread for data fetching started")