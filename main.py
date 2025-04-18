import os
import requests
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote
from shutil import copyfileobj
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

JSON_FILE = 'processed_posts.json'
TOKEN = os.getenv('DISCORD_TOKEN')  # Discord bot token
PREFIX = '/'  # Command prefix
intents = discord.Intents.all()  # Enable all intents

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

URLS_FILE = 'urls.json'  # Файл для хранения списка URL

def load_urls():
    """Load the list of URLs from a JSON file."""
    if os.path.exists(URLS_FILE):
        with open(URLS_FILE, 'r') as file:
            return json.load(file)
    return []

def save_url(new_url):
    """Save a new URL to the JSON file."""
    urls = load_urls()
    if new_url not in urls:
        urls.append(new_url)
        with open(URLS_FILE, 'w') as file:
            json.dump(urls, file, indent=4)  # Сохраняем в читаемом формате
        return True
    return False

def load_processed_posts():
    """Load processed post IDs from a JSON file."""
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, 'r') as file:
            return json.load(file)
    return []

def save_processed_post(post_id):
    """Save a processed post ID to the JSON file."""
    processed_posts = load_processed_posts()
    if post_id not in processed_posts:
        processed_posts.append(post_id)
        with open(JSON_FILE, 'w') as file:
            json.dump(processed_posts, file, indent=4)  # Save in readable format

def clear_directory(directory):
    if os.path.exists(directory):
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')

def parse_reactor_geek(url):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        posts = soup.find_all('div', class_='postContainer')
        
        images_dir = 'images'
        
        # Clear the images directory
        clear_directory(images_dir)
        
        # Create directory for images if it doesn't exist
        if not os.path.exists(images_dir):
            os.makedirs(images_dir)
        
        image_counter = 1
        processed_posts = load_processed_posts()
        
        for post in posts:
            # Get the post ID
            post_id = post.get('id')
            if not post_id:
                continue
            
            # Skip if the post ID is already processed
            if post_id in processed_posts:
                print(f'Skipping already processed post: {post_id}')
                continue
            
            # Extract images from post_content
            post_content = post.find('div', class_='post_content')
            if post_content:
                images = post_content.find_all('div', class_='image')  # Find images in class "image"
                if images:
                    print(f'Post {post_id} contains images:')
                    for image_div in images:
                        # Skip if the image is part of a video
                        if image_div.find('video'):
                            print('Skipping image inside a video.')
                            continue
                        
                        img = image_div.find('img')  # Find the <img> tag inside the "image" div
                        if img:
                            img_url = img.get('src')
                            if img_url:
                                img_url = urljoin(url, img_url)
                                print(f'Image URL: {img_url}')
                                
                                # Download and save the image
                                img_response = requests.get(img_url, stream=True)
                                if img_response.status_code == 200:
                                    img_name = os.path.join(images_dir, f'image{image_counter}.jpg')
                                    with open(img_name, 'wb') as out_file:
                                        copyfileobj(img_response.raw, out_file)
                                    print(f'Saved image: {img_name}')
                                    image_counter += 1
                    
                    # Mark the post as processed
                    save_processed_post(post_id)
                    print(f'Post {post_id} processed and saved.')
                    print('-' * 40)
                else:
                    print(f'Post {post_id} does not contain images in class "image"')
            else:
                print(f'Post {post_id} does not contain post_content')
    else:
        print(f'Failed to retrieve the page. Status code: {response.status_code}')

@bot.command()
async def add_url(ctx, url: str):
    """Add a new URL to the list."""
    if save_url(url):
        await ctx.send(f"URL '{url}' has been added to the list.")
    else:
        await ctx.send(f"URL '{url}' is already in the list.")

@bot.command()
async def fetch_images(ctx):
    """Fetch images from Reactor and send them to the Discord channel."""
    await ctx.send("Fetching images from Reactor...")
    url_list = load_urls()  # Загружаем список URL из JSON
    if not url_list:
        await ctx.send("No URLs found in the list. Please add URLs using the /add_url command.")
        return

    for url in url_list:
        parse_reactor_geek(url)
        images_dir = 'images'
        if os.path.exists(images_dir):
            images_sent = 0
            for filename in os.listdir(images_dir):
                file_path = os.path.join(images_dir, filename)
                if os.path.isfile(file_path):
                    try:
                        await ctx.send(file=discord.File(file_path))
                        images_sent += 1
                    except Exception as e:
                        print("Failed to send image {file_path}. Reason: {e}")
            if images_sent == 0:
                print("No images were sent for URL: {url}. The folder might be empty.")
            else:
                print("Finished sending {images_sent} images for URL: {url}.")
        else:
            print("No images found for URL: {url}.")

@bot.command()
async def fetch_post_content(ctx):
    """Fetch text from post_content, save it to JSON, and send it to the Discord channel."""
    url = "https://polit.reactor.cc/"
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        posts = soup.find_all('div', class_='postContainer')

        if not posts:
            await ctx.send("No posts found on the page.")
            return

        processed_posts = load_processed_posts()  # Load already processed post IDs

        for post in posts:
            post_id = post.get('id')
            if not post_id:
                continue

            # Skip if the post ID is already processed
            if post_id in processed_posts:
                print(f"Skipping already processed post: {post_id}")
                continue

            post_content = post.find('div', class_='post_content')
            if post_content:
                # Extract text
                text_parts = post_content.find_all('p')
                text_content = "\n".join(p.get_text(strip=True) for p in text_parts if p.get_text(strip=True))
                if text_content:
                    # Split text into chunks of 1980 characters to account for formatting
                    prefix = f"**Post ID {post_id} Text (part):**\n"
                    max_length = 2000 - len(prefix)
                    for i in range(0, len(text_content), max_length):
                        await ctx.send(f"{prefix}{text_content[i:i+max_length]}")

                    # Save the post ID as processed
                    save_processed_post(post_id)
                    print(f"Post {post_id} processed and saved.")
                else:
                    await ctx.send(f"No text found in post ID {post_id}.")
            else:
                await ctx.send(f"No content found in post ID {post_id}.")
    else:
        await ctx.send(f"Failed to retrieve the page. Status code: {response.status_code}")

# @tasks.loop(minutes=1)
# async def send_test_message():
#     """Send a test message to the #offtop channel every minute."""
#     channel = discord.utils.get(bot.get_all_channels(), name="offtop")
#     if channel:
#         await channel.send("@everyone test")
#     else:
#         print("Channel #offtop not found.")

# @bot.event
# async def on_ready():
#     """Start the loop when the bot is ready."""
#     print(f"Logged in as {bot.user}")
#     send_test_message.start()

@bot.command()
async def hello(ctx):
    """Simple hello command."""
    await ctx.send("Hello!")

if __name__ == '__main__':
    bot.run(TOKEN)