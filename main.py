import requests
import os
from requests.exceptions import HTTPError
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from urllib.parse import urljoin, urlsplit, unquote


def check_for_redirect(response):
    if response.history:
        raise HTTPError(f"Редирект на URL: {response.url}")


def get_book_info(book_id):
    url = 'https://tululu.org'
    response = requests.get(f'{url}/b{book_id}')
    soup = BeautifulSoup(response.text, 'lxml')
    title_tag = soup.find('h1').text
    if title_tag:
        title_author = title_tag.split('::')
        book_title = title_author[0].strip()
        book_author = title_author[1].strip()
    else:
        print('Заголовок H1 не найден')

    try:
        book_src_img = soup.find(class_="bookimage").find('img')['src']
        book_url_img = urljoin(url, book_src_img)
    except AttributeError:
        print(f"Изображение книги {book_id =} не найдено")

    return book_title, book_author, book_url_img


def download_txt(response, title, book_id, folder='books/'):
    filename = f'{book_id}.{sanitize_filename(title)}.txt'
    with open(os.path.join(folder, filename), 'wb') as file:
        file.write(response.content)


def download_image(book_url_img, book_id, folder='images/'):
    try:
        response = requests.get(book_url_img)
        response.raise_for_status()

        split_url = urlsplit(book_url_img)
        path = unquote(split_url.path)
        extension = path.split('.')[-1] if '.' in path else None
        image_name = f'{book_id}.{extension}' if 'nopic.gif' not in path else 'nopic.gif'

        save_path = os.path.join(folder, image_name)

        with open(save_path, 'wb') as file:
            file.write(response.content)

        print(f"Скачана обложка книги {book_id}")
    except requests.RequestException as e:
        print(f"Ошибка при скачивании обложки книги {book_id}: {e}")


def main():
    url = f'https://tululu.org/txt.php'
    os.makedirs('books', exist_ok=True)
    os.makedirs('images', exist_ok=True)

    for book_id in range(11):
        params = {
            'id': book_id
        }

        try:
            response = requests.get(url, params=params, allow_redirects=True)
            response.raise_for_status()
            check_for_redirect(response)
        except HTTPError as e:
            print(f"Ошибка при запросе книги {book_id}: {e}")
            continue
        book_title, book_author, book_url_img = get_book_info(book_id)
        download_txt(response, book_title, book_id)
        download_image(book_url_img, book_id)


if __name__ == "__main__":
    main()
