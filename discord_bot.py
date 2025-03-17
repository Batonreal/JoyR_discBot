import discord
from discord.ext import commands
import os

TOKEN = ''
PREFIX = '/'
intents = discord.Intents.all()

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

@bot.command()
async def hello(ctx):
    await ctx.send('Hello!')

@bot.command()
async def image(ctx):
    image_path = os.path.join('images', 'image1.jpg')
    if os.path.exists(image_path):
        await ctx.send(file=discord.File(image_path))
    else:
        await ctx.send('Image not found.')

bot.run(TOKEN)