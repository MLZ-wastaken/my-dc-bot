import discord
from discord import app_commands
import requests
import json
import asyncio
from datetime import datetime
import aiohttp
import schedule
import time
from threading import Thread

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# CS2 Market Analyzer
class CS2MarketAnalyzer:
    def __init__(self):
        self.app_id = 730  # CS2 App ID
        self.session = None
        
    async def get_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def get_market_data(self, count=100):
        """Get real CS2 market data from Steam"""
        try:
            session = await self.get_session()
            url = f"https://steamcommunity.com/market/search/render/"
            params = {
                'search_descriptions': 0,
                'sort_column': 'price',
                'sort_dir': 'desc',
                'appid': self.app_id,
                'norender': 1,
                'count': count
            }
            
            async with session.get(url, params=params) as response:
                data = await response.json()
                return data.get('results', [])
                
        except Exception as e:
            print(f"Error fetching market data: {e}")
            return []
    
    async def get_price_history(self, market_hash_name):
        """Get price history for specific item"""
        try:
            # Note: This requires proper Steam API key for full access
            # Using alternative approach with Steam web
            session = await self.get_session()
            url = f"https://steamcommunity.com/market/pricehistory/"
            params = {
                'appid': self.app_id,
                'market_hash_name': market_hash_name
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.text()
                    return self.parse_price_history(data)
                return []
                
        except Exception as e:
            print(f"Error fetching price history: {e}")
            return []
    
    def parse_price_history(self, data):
        """Parse price history from Steam response"""
        # This is simplified - Steam requires proper authentication
        # For now, return mock trend data
        return []
    
    def calculate_investment_confidence(self, item, price_history):
        """Calculate investment confidence 0-100%"""
        confidence = 50  # Base confidence
        
        # Factor 1: Listings (supply)
        listings = item.get('sell_listings', 100)
        if isinstance(listings, str):
            listings = int(listings) if listings.isdigit() else 100
            
        if listings < 20:
            confidence += 25  # Low supply = good
        elif listings > 200:
            confidence -= 15  # High supply = bad
        
        # Factor 2: Item name analysis
        name = item.get('name', '').lower()
        
        # High-value items
        if any(word in name for word in ['knife', 'glove', 'doppler', 'gamma', 'emerald', 'sapphire', 'ruby']):
            confidence += 15
        
        # StatTrak items
        if 'stattrak' in name:
            confidence += 10
            
        # Popular weapons
        popular_weapons = ['ak-47', 'awp', 'm4a4', 'm4a1', 'desert eagle', 'usp-s']
        if any(weapon in name for weapon in popular_weapons):
            confidence += 8
            
        # Factor 3: Price analysis
        price_text = item.get('sell_price_text', '$0').replace('$', '').replace(',', '')
        try:
            price = float(price_text)
            if 10 <= price <= 500:  # Good investment range
                confidence += 10
            elif price > 1000:  # Very expensive = higher risk
                confidence -= 5
        except:
            pass
            
        return max(5, min(95, confidence))
    
    def get_trend_emoji(self, confidence):
        """Get trend emoji based on confidence"""
        if confidence >= 80:
            return "🚀"
        elif confidence >= 65:
            return "📈"
        elif confidence >= 50:
            return "➡️"
        else:
            return "📉"
    
    async def analyze_market(self, specific_item=None):
        """Main analysis function"""
        market_data = await self.get_market_data(50)  # Get 50 items
        
        opportunities = []
        
        for item in market_data:
            if specific_item and specific_item.lower() not in item.get('name', '').lower():
                continue
                
            price_history = await self.get_price_history(item.get('hash_name', ''))
            confidence = self.calculate_investment_confidence(item, price_history)
            
            if confidence >= 60:  # Only show good opportunities
                opportunities.append({
                    'name': item.get('name', 'Unknown'),
                    'confidence': confidence,
                    'price': item.get('sell_price_text', 'N/A'),
                    'volume': item.get('sell_listings', 'N/A'),
                    'trend_emoji': self.get_trend_emoji(confidence),
                    'asset_description': item.get('asset_description', {})
                })
        
        # Sort by confidence (highest first)
        opportunities.sort(key=lambda x: x['confidence'], reverse=True)
        return opportunities[:5]  # Top 5 only

# Initialize analyzer
analyzer = CS2MarketAnalyzer()

@client.event
async def on_ready():
    print(f'✅ {client.user} has connected to Discord!')
    
    try:
        synced = await tree.sync()
        print(f"✅ Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"❌ Error syncing commands: {e}")

# Slash command: /cs2invest
@tree.command(name="cs2invest", description="Get CS2 market investment opportunities")
async def cs2invest(interaction: discord.Interaction, item: str = None):
    await interaction.response.defer()
    
    try:
        opportunities = await analyzer.analyze_market(item)
        
        if not opportunities:
            embed = discord.Embed(
                title="🔍 CS2 Market Analysis",
                description="No high-confidence investment opportunities found at the moment.",
                color=0xFF0000
            )
            await interaction.followup.send(embed=embed)
            return
        
        embed = discord.Embed(
            title="🔍 CS2 Market Analysis - Real Data",
            description="Top investment opportunities based on live market data:",
            color=0x00FF00,
            timestamp=datetime.now()
        )
        
        for opp in opportunities:
            embed.add_field(
                name=f"{opp['trend_emoji']} {opp['name']} - {opp['confidence']}% Confidence",
                value=f"💰 **Price:** {opp['price']} | 📊 **Listings:** {opp['volume']}",
                inline=False
            )
        
        embed.set_footer(text="CS2 Investment Bot • Real-time Steam Market Data")
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        print(f"Command error: {e}")
        await interaction.followup.send("❌ Error analyzing market data. Please try again later.")

# Auto-update function (runs every 6 hours)
async def auto_market_update():
    """Send automatic market updates to specified channel"""
    try:
        channel_id = int(os.getenv('UPDATE_CHANNEL_ID', 0))
        if not channel_id:
            return
            
        channel = client.get_channel(channel_id)
        if not channel:
            return
            
        opportunities = await analyzer.analyze_market()
        
        if opportunities:
            embed = discord.Embed(
                title="🔄 CS2 Market Auto-Update",
                description="6-hour market analysis update:",
                color=0x0099FF
            )
            
            for opp in opportunities[:3]:  # Top 3 only for updates
                embed.add_field(
                    name=f"{opp['trend_emoji']} {opp['name']} - {opp['confidence']}%",
                    value=f"Price: {opp['price']}",
                    inline=True
                )
            
            embed.set_footer(text="Auto-update • Next in 6 hours")
            await channel.send(embed=embed)
            
    except Exception as e:
        print(f"Auto-update error: {e}")

def schedule_updates():
    """Schedule background tasks"""
    while True:
        schedule.run_pending()
        time.sleep(1)

# Start the bot
if __name__ == "__main__":
    # Schedule auto-updates every 6 hours
    schedule.every(6).hours.do(lambda: asyncio.create_task(auto_market_update()))
    
    # Start scheduler in background thread
    scheduler_thread = Thread(target=schedule_updates, daemon=True)
    scheduler_thread.start()
    
    # Start the bot
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("❌ ERROR: DISCORD_TOKEN environment variable not set!")
        exit(1)
        
    client.run(token)
