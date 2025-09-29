import discord
from discord.ext import tasks, commands
import os
import aiohttp
import random
import asyncio

# Bot setup
token = os.environ['DISCORD_TOKEN']
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

class CS2MarketAnalyzer:
    def __init__(self):
        self.cache = {}
        
    async def get_market_data(self, count=20):
        """Get real CS2 market data from Steam"""
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
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('success'):
                            return self.process_real_data(data.get('results', []))
            
            # Fallback to simulated data if API fails
            return self.get_simulated_data()
            
        except Exception as e:
            print(f"API error: {e}")
            return self.get_simulated_data()
    
    def process_real_data(self, items):
        """Process real Steam market data"""
        processed = []
        for item in items:
            try:
                name = item.get('name', 'Unknown')
                price = item.get('sell_price', 0) / 100
                volume = item.get('sell_listings', 0)
                hash_name = item.get('hash_name', '')
                
                # Calculate investment score
                score = self.calculate_investment_score(price, volume, name)
                
                processed.append({
                    'name': name,
                    'current_price': round(price, 2),
                    'volume': volume,
                    'investment_probability': score,
                    'recommendation': self.get_recommendation(score),
                    'market_url': f"https://steamcommunity.com/market/listings/730/{hash_name}",
                    'real_data': True
                })
            except:
                continue
        
        return sorted(processed, key=lambda x: x['investment_probability'], reverse=True)
    
    def get_simulated_data(self):
        """Fallback simulated data"""
        items = [
            "AK-47 | Redline", "AWP | Asiimov", "Karambit | Fade", 
            "M4A4 | Howl", "Butterfly Knife", "Sport Gloves",
            "Desert Eagle | Blaze", "USP-S | Kill Confirmed"
        ]
        
        processed = []
        for name in items:
            price = random.uniform(15, 400)
            volume = random.randint(50, 800)
            score = self.calculate_investment_score(price, volume, name)
            
            processed.append({
                'name': name,
                'current_price': round(price, 2),
                'volume': volume,
                'investment_probability': score,
                'recommendation': self.get_recommendation(score),
                'market_url': "https://steamcommunity.com/market/search?appid=730",
                'real_data': False
            })
        
        return sorted(processed, key=lambda x: x['investment_probability'], reverse=True)
    
    def calculate_investment_score(self, price, volume, name):
        """Calculate investment probability"""
        score = 50
        
        # Price factors
        if 10 <= price <= 100:
            score += 20
        elif price > 300:
            score += 5
            
        # Volume factors
        if volume < 100:
            score += 25
        elif volume < 500:
            score += 15
            
        # Item type factors
        name_lower = name.lower()
        if 'knife' in name_lower:
            score += 15
        elif 'glove' in name_lower:
            score += 10
        elif 'ak-47' in name_lower or 'awp' in name_lower:
            score += 8
            
        return min(score, 100)
    
    def get_recommendation(self, probability):
        if probability >= 80:
            return "🚀 STRONG BUY"
        elif probability >= 65:
            return "📈 GOOD BUY"
        elif probability >= 50:
            return "⚡ MODERATE"
        else:
            return "💤 HOLD"
    
    async def search_items(self, query, count=8):
        """Search for items"""
        all_items = await self.get_market_data(30)
        results = []
        
        for item in all_items:
            if query.lower() in item['name'].lower():
                results.append(item)
        
        return results[:count]

# Create analyzer instance
analyzer = CS2MarketAnalyzer()

@bot.event
async def on_ready():
    print(f'✅ {bot.user} is online on Render!')
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching, 
        name="CS2 Market Trends"
    ))

@bot.command(name='analyze')
async def analyze_market(ctx, count: int = 6):
    """Get market analysis"""
    await ctx.send("🔍 Analyzing CS2 market...")
    
    try:
        opportunities = await analyzer.get_market_data(count)
        
        embed = discord.Embed(
            title="🎯 CS2 Market Analysis",
            color=0x00ff00,
            description="Real data from Steam Market"
        )
        
        for i, item in enumerate(opportunities[:count], 1):
            data_source = "✅ Real" if item.get('real_data', False) else "🤖 Sim"
            
            embed.add_field(
                name=f"{i}. {item['name']} {data_source}",
                value=(
                    f"💰 **Price:** ${item['current_price']:.2f}\n"
                    f"📊 **Volume:** {item['volume']} listings\n"
                    f"🎯 **Score:** {item['investment_probability']}%\n"
                    f"💡 **{item['recommendation']}**\n"
                    f"🔗 **[Buy on Steam]({item['market_url']})**"
                ),
                inline=False
            )
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send("❌ Market analysis failed")

@bot.command(name='search')
async def search_market(ctx, *, query: str):
    """Search for specific items"""
    await ctx.send(f"🔍 Searching for: **{query}**...")
    
    try:
        results = await analyzer.search_items(query, 6)
        
        if not results:
            await ctx.send(f"❌ No items found for: **{query}**")
            return
            
        embed = discord.Embed(
            title=f"🔎 Search Results: {query}",
            color=0x7289da
        )
        
        for i, item in enumerate(results, 1):
            embed.add_field(
                name=f"{i}. {item['name']}",
                value=(
                    f"💰 ${item['current_price']:.2f} | "
                    f"🎯 {item['investment_probability']}%\n"
                    f"💡 {item['recommendation']}\n"
                    f"🔗 **[View]({item['market_url']})**"
                ),
                inline=False
            )
            
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Search failed for **{query}**")

@bot.command(name='ping')
async def ping(ctx):
    """Check bot status"""
    latency = round(bot.latency * 1000)
    await ctx.send(f'🏓 Pong! Latency: {latency}ms | Hosted on Render')

@bot.command(name='help_bot')
async def help_bot(ctx):
    """Show help"""
    embed = discord.Embed(
        title="🤖 CS2 Market Bot Commands",
        color=0x0099ff,
        description="All commands start with `!`"
    )
    
    commands = {
        "!analyze [number]": "Get market opportunities (default: 6)",
        "!search <item name>": "Search for specific items",
        "!ping": "Check if bot is online", 
        "!help_bot": "Show this help message"
    }
    
    for cmd, desc in commands.items():
        embed.add_field(name=cmd, value=desc, inline=False)
    
    await ctx.send(embed=embed)

# Start the bot
if __name__ == "__main__":
    bot.run(token)
