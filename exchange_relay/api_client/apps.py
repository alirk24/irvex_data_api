from django.apps import AppConfig

# api_client/apps.py
from django.apps import AppConfig
import asyncio
import aiocron
import logging
from threading import Thread

logger = logging.getLogger(__name__)

class ApiClientConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api_client'
    
    def ready(self):
        # Don't run on migrations or other management commands
        import sys
        if 'runserver' not in sys.argv and 'daphne' not in sys.argv:
            return
        
        # Start the background task for data fetching    
        self.start_background_task()
    
    def start_background_task(self):
        # Import here to avoid circular imports
        from .services.api_client import IranExchangeClient
        from .services.cache_manager import get_cache
        
        def run_fetcher():
            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Create the API client
            api_client = IranExchangeClient()
            
            # Define the data fetching task
            async def fetch_data_job():
                try:
                    logger.info("Fetching data from Iran Exchange API...")
                    await api_client.update_cache()
                    logger.info("Data fetched and cache updated successfully")
                except Exception as e:
                    logger.error(f"Error fetching data: {e}")
            
            # Run the initial fetch
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
            loop.create_task(scheduled_updates())
            
            # Run the event loop forever
            loop.run_forever()
        
        # Start the background thread
        self.thread = Thread(target=run_fetcher, daemon=True)
        self.thread.start()
    async def fetch_initial_data(self):
        """Fetch initial data on startup"""
        try:
            logger.info("Fetching initial data from Iran Exchange API...")
            data = await self.api_client.fetch_all_data()
            await self.cache_instance.update_data(data)
            logger.info("Initial data fetched successfully")
        except Exception as e:
            logger.error(f"Error fetching initial data: {e}")