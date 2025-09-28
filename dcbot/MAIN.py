import discord
from discord.ext import tasks, commands
import os
from market_analyzer import CS2MarketAnalyzer
from flask import Flask
from threading import Thread
import time

# Simple Flask app
app = Flask('')

@app.route('/')
def home():
    return "CS2 Market Bot"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# Start the server
keep_alive()

# Get token
token = os.environ['DISCORD_TOKEN']

# Create bot
class CS2MarketBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        self.analyzer = CS2MarketAnalyzer()
        
    async def setup_hook(self):
        print('Bot is starting...')
        self.market_update.start()

    @tasks.loop(minutes=15)
    async def market_update(self):
        print("Updating market data...")

    @market_update.before_loop
    async def before_market_update(self):
        await self.wait_until_ready()

bot = CS2MarketBot()

@bot.event
async def on_ready():
    print(f'{bot.user} is online!')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="CS2 Market"))

@bot.command()
async def analyze(ctx, count: int = 5):
    await ctx.send("Analyzing market...")
    
    try:
        opportunities = await bot.analyzer.get_top_opportunities(count)
        
        embed = discord.Embed(title="Market Analysis", color=0x00ff00)
        
        for i, item in enumerate(opportunities, 1):
            embed.add_field(
                name=f"{i}. {item['name']}",
                value=f"Price: ${item['current_price']:.2f}\nScore: {item['investment_probability']}%",
                inline=False
            )
            
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send("Analysis failed")

@bot.command()
async def search(ctx, *, query: str):
    await ctx.send(f"Searching for {query}...")
    
    try:
        results = await bot.analyzer.search_real_items(query, 5)
        
        embed = discord.Embed(title=f"Results: {query}", color=0x7289da)
        
        for i, item in enumerate(results, 1):
            embed.add_field(
                name=f"{i}. {item['name']}",
                value=f"${item['current_price']:.2f} | {item['investment_probability']}%",
                inline=False
            )
            
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send("Search failed")

@bot.command()
async def ping(ctx):
    await ctx.send("Pong! Bot is online")

@bot.command()
async def help_bot(ctx):
    embed = discord.Embed(title="Bot Commands", color=0x0099ff)
    embed.add_field(name="!analyze", value="Get opportunities", inline=False)
    embed.add_field(name="!search", value="Search items", inline=False)
    embed.add_field(name="!ping", value="Check bot", inline=False)
    embed.add_field(name="!help_bot", value="This menu", inline=False)
    await ctx.send(embed=embed)

# Run bot
bot.run(token)