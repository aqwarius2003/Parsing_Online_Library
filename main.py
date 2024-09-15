import requests
import os

os.makedirs('books', exist_ok=True)
url = f'https://tululu.org/txt.php'


def download_book(url, path, params):
    response = requests.get(url, params=params)
    response.raise_for_status()
    with open(path, 'wb') as file:
        file.write(response.content)


for book_id in range(11):
    params = {
        'id': book_id
    }
    download_book(url=url,
                  path=f'books/id_{book_id}.txt',
                  params=params)
os.makedirs('books', exist_ok=True)
