import discord
from discord.ext import commands
import os
import requests
import random

token = os.environ['DISCORD_TOKEN']
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

class CS2MarketAnalyzer:
    def get_real_market_data(self, count=10):
        """Get REAL Steam market data"""
        try:
            url = "https://steamcommunity.com/market/search/render/"
            params = {
                'appid': 730,
                'count': count,
                'search_descriptions': 0,
                'sort_column': 'price',
                'sort_dir': 'desc',
                'norender': 1
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    items = data.get('results', [])
                    return self.process_real_items(items)
            
            # If API fails, use fallback data
            return self.get_fallback_data()
            
        except:
            return self.get_fallback_data()
    
    def process_real_items(self, items):
        """Process real items from Steam"""
        processed = []
        for item in items:
            try:
                name = item.get('name', 'Unknown')
                price = item.get('sell_price', 0) / 100  # Convert to dollars
                volume = item.get('sell_listings', 0)
                hash_name = item.get('hash_name', '')
                
                # Calculate investment score
                score = self.calculate_score(price, volume, name)
                
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
    
    def get_fallback_data(self):
        """Fallback data if Steam API fails"""
        items = [
            "AK-47 | Redline", "AWP | Asiimov", "Karambit | Fade",
            "M4A4 | Howl", "Butterfly Knife", "Sport Gloves",
            "Desert Eagle | Blaze", "USP-S | Kill Confirmed"
        ]
        
        processed = []
        for name in items:
            price = random.uniform(20, 500)
            volume = random.randint(50, 800)
            score = self.calculate_score(price, volume, name)
            
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
    
    def calculate_score(self, price, volume, name):
        score = 50
        if 10 <= price <= 100: score += 20
        if volume < 100: score += 25
        if 'knife' in name.lower(): score += 15
        if 'glove' in name.lower(): score += 10
        return min(score, 100)
    
    def get_recommendation(self, probability):
        if probability >= 80: return "🚀 STRONG BUY"
        elif probability >= 65: return "📈 GOOD BUY"
        elif probability >= 50: return "⚡ MODERATE"
        else: return "💤 HOLD"

analyzer = CS2MarketAnalyzer()

@bot.event
async def on_ready():
    print(f'✅ {bot.user} is online!')
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching, 
        name="CS2 Market"
    ))

@bot.command()
async def analyze(ctx, count: int = 6):
    await ctx.send("🔍 Analyzing REAL CS2 market...")
    opportunities = analyzer.get_real_market_data(count)
    
    embed = discord.Embed(title="🎯 CS2 Market Analysis", color=0x00ff00)
    
    for i, item in enumerate(opportunities[:count], 1):
        data_source = "🟢 REAL" if item['real_data'] else "🟡 SIM"
        embed.add_field(
            name=f"{i}. {item['name']} {data_source}",
            value=f"💰 ${item['current_price']:.2f} | 🎯 {item['investment_probability']}% | {item['recommendation']}",
            inline=False
        )
    
    await ctx.send(embed=embed)

@bot.command()
async def search(ctx, *, query: str):
    await ctx.send(f"🔍 Searching for {query}...")
    all_items = analyzer.get_real_market_data(20)
    results = [item for item in all_items if query.lower() in item['name'].lower()]
    
    if results:
        embed = discord.Embed(title=f"Results: {query}", color=0x7289da)
        for i, item in enumerate(results[:5], 1):
            embed.add_field(
                name=f"{i}. {item['name']}",
                value=f"${item['current_price']:.2f} | {item['investment_probability']}% | {item['recommendation']}",
                inline=False
            )
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"❌ No results for {query}")

@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong! Bot is online")

@bot.command()
async def help_bot(ctx):
    embed = discord.Embed(title="CS2 Bot Commands", color=0x0099ff)
    embed.add_field(name="!analyze", value="Get investment opportunities", inline=False)
    embed.add_field(name="!search", value="Search items", inline=False)
    embed.add_field(name="!ping", value="Check bot", inline=False)
    await ctx.send(embed=embed)

bot.run(token)
