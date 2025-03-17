import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote
from shutil import copyfileobj

def clear_directory(directory):
    if os.path.exists(directory):
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')

def parse_reactor_geek():
    url = 'https://reactor.cc/tag/geek'
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
        
        for post in posts:
            # Extract images from post_content
            post_content = post.find('div', class_='post_content')
            if post_content:
                images = post_content.find_all('img')
                if images:
                    print('Post contains images:')
                    for img in images:
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
                    print('-' * 40)
                else:
                    print('Post does not contain images')
            else:
                print('Post does not contain post_content')
    else:
        print(f'Failed to retrieve the page. Status code: {response.status_code}')

if __name__ == '__main__':
    parse_reactor_geek()