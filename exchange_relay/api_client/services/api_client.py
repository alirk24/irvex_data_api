# api_client/services/api_client.py
import httpx
import asyncio
import xmltodict
import datetime
import traceback
from typing import Dict, Any
from .stock_metadata import get_metadata_client
class IranExchangeClient:
    def __init__(self):
        self.base_url = "http://service.tsetmc.com/webservice/TsePublicV2.asmx"
        self.headers = {
            'Content-Type': 'application/soap+xml; charset=utf-8',
            'Host': 'service.tsetmc.com'
        }
        self.username = "stocksgame"
        self.password = "$T030K$g@m3.!r"
        
    async def fetch_client_type(self) -> Dict[str, Any]:
        """Fetch client type data from the exchange API"""
        body = f"""<?xml version="1.0" encoding="utf-8"?>
        <soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
          <soap12:Body>
            <ClientType xmlns="http://tsetmc.com/">
              <UserName>{self.username}</UserName>
              <Password>{self.password}</Password>
            </ClientType>
          </soap12:Body>
        </soap12:Envelope>"""
        
        async with httpx.AsyncClient() as client:
            response = await client.post(self.base_url, headers=self.headers, data=body)
            dict_data = xmltodict.parse(response.content)
            data = dict_data['soap:Envelope']['soap:Body']['ClientTypeResponse']['ClientTypeResult']['diffgr:diffgram']['Data']['Data']
            
            cli_data = {}
            for i in data:
                cli_data[i['InsCode']] = i
                
            return cli_data
    
    async def fetch_trade_last_day_all(self, flow: int) -> Dict[str, Any]:
        """Fetch last day's trading data for all instruments with given flow"""
        body = f"""<?xml version="1.0" encoding="utf-8"?>
        <soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
          <soap12:Body>
            <TradeLastDayAll xmlns="http://tsetmc.com/">
              <UserName>{self.username}</UserName>
              <Password>{self.password}</Password>
              <Flow>{flow}</Flow>
            </TradeLastDayAll>
          </soap12:Body>
        </soap12:Envelope>"""
        
        async with httpx.AsyncClient() as client:
            response = await client.post(self.base_url, headers=self.headers, data=body)
            dict_data = xmltodict.parse(response.content)
            data = dict_data['soap:Envelope']['soap:Body']['TradeLastDayAllResponse']['TradeLastDayAllResult']['diffgr:diffgram']['TradeLastDayAll']['TradeLastDayAll']
            
            dict_trade_last_day = {}
            for i in data:
                dict_trade_last_day[i['InsCode']] = i
                
            return dict_trade_last_day
    
    async def fetch_best_limits_all_ins(self, flow: int) -> Dict[str, Any]:
        """Fetch best limits for all instruments with given flow"""
        body = f"""<?xml version="1.0" encoding="utf-8"?>
        <soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
        <soap12:Body>
            <BestLimitsAllIns xmlns="http://tsetmc.com/">
            <UserName>{self.username}</UserName>
            <Password>{self.password}</Password>
            <Flow>{flow}</Flow>
            </BestLimitsAllIns>
        </soap12:Body>
        </soap12:Envelope>"""
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self.base_url, headers=self.headers, data=body)
                
                # Handle potential XML errors
                try:
                    dict_data = xmltodict.parse(response.content)
                    
                    # Check if the expected path exists
                    if ('soap:Envelope' in dict_data and 
                        'soap:Body' in dict_data['soap:Envelope'] and 
                        'BestLimitsAllInsResponse' in dict_data['soap:Envelope']['soap:Body'] and
                        'BestLimitsAllInsResult' in dict_data['soap:Envelope']['soap:Body']['BestLimitsAllInsResponse'] and
                        'diffgr:diffgram' in dict_data['soap:Envelope']['soap:Body']['BestLimitsAllInsResponse']['BestLimitsAllInsResult'] and
                        'AllBestLimits' in dict_data['soap:Envelope']['soap:Body']['BestLimitsAllInsResponse']['BestLimitsAllInsResult']['diffgr:diffgram'] and
                        'InstBestLimit' in dict_data['soap:Envelope']['soap:Body']['BestLimitsAllInsResponse']['BestLimitsAllInsResult']['diffgr:diffgram']['AllBestLimits']):
                        
                        data = dict_data['soap:Envelope']['soap:Body']['BestLimitsAllInsResponse']['BestLimitsAllInsResult']['diffgr:diffgram']['AllBestLimits']['InstBestLimit']
                        
                        b = {}
                        for i in data:
                            if i['InsCode'] not in b:
                                b[i['InsCode']] = {}
                            b[i['InsCode']][i['number']] = i
                        
                        return b
                    else:
                        print(f"Unexpected XML structure: {dict_data.keys()}")
                        return {}
                        
                except Exception as xml_err:
                    print(f"XML Parsing error in fetch_best_limits_all_ins for flow {flow}: {xml_err}")
                    print(f"First 200 chars of response: {response.content[:200]}")
                    
                    # Try to clean or fix the XML before parsing
                    # Sometimes SOAP responses have character issues
                    cleaned_xml = response.content.decode('utf-8', errors='replace')
                    try:
                        dict_data = xmltodict.parse(cleaned_xml)
                        # Rest of your code to process the data...
                        # This is a simplified version - you'd need to add the full processing logic
                        return {}
                    except Exception as e:
                        print(f"Failed to parse even after cleaning: {e}")
                        return {}
                    
            except Exception as e:
                print(f"Error in fetch_best_limits_all_ins for flow {flow}: {e}")
                return {}
    
  
    
    async def fetch_all_data(self):
        try:
            """Fetch all data from the exchange API in parallel"""
            print("Starting to fetch data from Iran Exchange API...")
            
            # First, get the metadata client and ensure it's updated
            metadata_client = get_metadata_client()
            await metadata_client.fetch_metadata() # This will fetch metadata AND details with pe, tmax, tmin, nav
            
            # Get the list of valid stock IDs to filter data
            valid_stock_ids = metadata_client.get_stock_ids()
            print(f"Found {len(valid_stock_ids)} valid stocks in metadata")
            
            # Existing code to fetch data...
            tasks = [
                self.fetch_client_type(),
                self.fetch_trade_last_day_all(1),
                self.fetch_best_limits_all_ins(1),
                self.fetch_trade_last_day_all(2),
                self.fetch_best_limits_all_ins(2),
                self.fetch_trade_last_day_all(4),
                self.fetch_best_limits_all_ins(4),
                self.fetch_trade_last_day_all(7),
                self.fetch_best_limits_all_ins(7)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results, handling any exceptions
            processed_results = []
            for result in results:
                if isinstance(result, Exception):
                    print(f"Error in one of the fetch tasks: {result}")
                    processed_results.append({})  # Add empty dict for failed tasks
                else:
                    processed_results.append(result)
            
            # Extract data from processed results
            client_type_data = processed_results[0] if not isinstance(processed_results[0], Exception) else {}
            
            # Combine trade data from different flows, handling potential exceptions
            trade_data = {}
            trade_data.update(processed_results[1] or {})  # Flow 1
            trade_data.update(processed_results[3] or {})  # Flow 2
            trade_data.update(processed_results[5] or {})  # Flow 4
            trade_data.update(processed_results[7] or {})  # Flow 7
            
            # Combine best limits data from different flows, handling potential exceptions
            limits_data = {}
            limits_data.update(processed_results[2] or {})  # Flow 1
            limits_data.update(processed_results[4] or {})  # Flow 2
            limits_data.update(processed_results[6] or {})  # Flow 4
            limits_data.update(processed_results[8] or {})  # Flow 7
            
            # Filter data to only include valid stocks from metadata
            filtered_client_type = {k: v for k, v in client_type_data.items() if k in valid_stock_ids}
            filtered_trade_data = {k: v for k, v in trade_data.items() if k in valid_stock_ids}
            filtered_limits_data = {k: v for k, v in limits_data.items() if k in valid_stock_ids}
            
            print(f"Successfully fetched data: {len(filtered_client_type)} client types, {len(filtered_trade_data)} trades, {len(filtered_limits_data)} limits (after filtering)")
            
            # Get the complete metadata with all fields including pe, tmax, tmin, nav
            stock_metadata = metadata_client.get_simplified_metadata()
            
            return {
                'client_type': filtered_client_type,
                'trade_data': filtered_trade_data,
                'limits_data': filtered_limits_data,
                'metadata': stock_metadata
            }
            
        except Exception as e:
            print(f"Error fetching data: {type(e).__name__}: {str(e)}")
            traceback.print_exc()
            # Return an empty result rather than raising an exception
            return {
                'client_type': {},
                'trade_data': {},
                'limits_data': {},
                'metadata': {}
            }
            
        except Exception as e:
            print(f"Error fetching data: {type(e).__name__}: {str(e)}")
            traceback.print_exc()
            # Return an empty result rather than raising an exception
            return {
                'client_type': {},
                'trade_data': {},
                'limits_data': {},
                'metadata': {}
            }
    async def update_cache(self):
        """Fetch all data and update the cache"""
        from api_client.services.cache_manager import get_cache
        try:
            data = await self.fetch_all_data()
            if data:
                cache = get_cache()
                await cache.update_data(data)
                print(f"Cache updated successfully with {len(data.get('trade_data', {}))} stocks")
            else:
                print("No data received from API to update cache")
            return data
        except Exception as e:
            print(f"Error updating cache: {e}")
            traceback.print_exc()
            return None