import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()  # Загружаем переменные из .env

TOKEN = os.getenv('DISCORD_TOKEN')  # Получаем токен из переменной окружения
PREFIX = '/' # Префикс для команд
intents = discord.Intents.all() # Включаем все интенты

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