# api_client/services/api_client.py
import httpx
import asyncio
import xmltodict
import datetime
from typing import Dict, Any

class IranExchangeClient:
    def __init__(self):
        self.base_url = "http://service.tsetmc.com/webservice/TsePublicV2.asmx"
        self.headers = {
            'Content-Type': 'application/soap+xml; charset=utf-8',
            'Host': 'service.tsetmc.com'
        }
        self.username = "aryasarmaye.ir"
        self.password = "@rY@sar1\/1ayE.!R"
        
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
    
    # api_client/services/api_client.py

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
                        
                except xml.parsers.expat.ExpatError as xml_err:
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
            """Fetch all data from the exchange API in parallel"""
            print("Starting to fetch data from Iran Exchange API...")
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
            
            results = await asyncio.gather(*tasks)
            
            client_type_data = results[0]
            
            # Combine trade data from different flows
            trade_data = {}
            trade_data.update(results[1])  # Flow 1
            trade_data.update(results[3])  # Flow 2
            trade_data.update(results[5])  # Flow 4
            trade_data.update(results[7])  # Flow 7
            
            # Combine best limits data from different flows
            limits_data = {}
            limits_data.update(results[2])  # Flow 1
            limits_data.update(results[4])  # Flow 2
            limits_data.update(results[6])  # Flow 4
            limits_data.update(results[8])  # Flow 7
            print(f"Successfully fetched data: {len(client_type_data)} client types, {len(trade_data)} trades, {len(limits_data)} limits")
            return {
                'client_type': client_type_data,
                'trade_data': trade_data,
                'limits_data': limits_data
            }
        except Exception as e:
            print(f"Error fetching data: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
    async def update_cache(self):
        """Fetch all data and update the cache"""
        data = await self.fetch_all_data()
        cache = get_cache()
        await cache.update_data(data)
        return data