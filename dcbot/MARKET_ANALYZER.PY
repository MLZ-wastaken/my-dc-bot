import requests
import asyncio
import time
import aiohttp

class CS2MarketAnalyzer:
    def __init__(self):
        self.cache = {}
        
    async def get_steam_market_data(self, count=20):
        try:
            url = "https://steamcommunity.com/market/search/render/"
            params = {
                'appid': 730,
                'count': count,
                'search_descriptions': 0,
                'sort_column': 'popular',
                'sort_dir': 'desc',
                'norender': 1
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('success'):
                            return self.process_real_data(data.get('results', []))
            return []
            
        except Exception as e:
            print(f"API error: {e}")
            return []
    
    def process_real_data(self, items):
        processed = []
        
        for item in items:
            try:
                name = item.get('name', 'Unknown')
                price = item.get('sell_price', 0) / 100
                volume = item.get('sell_listings', 0)
                hash_name = item.get('hash_name', '')
                
                market_url = f"https://steamcommunity.com/market/listings/730/{hash_name}"
                probability = self.calculate_probability(price, volume, name)
                
                processed.append({
                    'name': name,
                    'current_price': round(price, 2),
                    'volume': volume,
                    'investment_probability': probability,
                    'recommendation': self.get_recommendation(probability),
                    'market_url': market_url
                })
                
            except Exception as e:
                continue
        
        return processed
    
    def calculate_probability(self, price, volume, name):
        score = 50
        
        if 10 <= price <= 100:
            score += 15
            
        if volume < 100:
            score += 20
        elif volume < 500:
            score += 10
            
        if 'knife' in name.lower():
            score += 10
        elif 'glove' in name.lower():
            score += 8
            
        return min(score, 100)
    
    def get_recommendation(self, probability):
        if probability >= 80:
            return "STRONG BUY"
        elif probability >= 60:
            return "GOOD BUY"
        elif probability >= 40:
            return "MODERATE"
        else:
            return "HOLD"
    
    async def search_real_items(self, query, count=10):
        all_items = await self.get_steam_market_data(30)
        if not all_items:
            return []
        
        results = []
        for item in all_items:
            if query.lower() in item['name'].lower():
                results.append(item)
        
        return results[:count]
    
    async def get_top_opportunities(self, count=5):
        data = await self.get_steam_market_data(count * 2)
        return data[:count]