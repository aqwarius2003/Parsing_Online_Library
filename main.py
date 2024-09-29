import requests
import os
import logging
from requests.exceptions import HTTPError
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from urllib.parse import urljoin, urlsplit, unquote

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


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
        logger.info('Заголовок H1 не найден')

    try:
        book_src_img = soup.find(class_="bookimage").find('img')['src']
        book_url_img = urljoin(url, book_src_img)
    except AttributeError:
        logger.info(f"Изображение книги {book_title}-{book_author}- не найдено")

    return book_title, book_author, book_url_img


def download_txt(url, filename, folder='books/'):
    """Функция для скачивания текстовых файлов.
        Args:
            url (str): Cсылка на текст, который хочется скачать.
            filename (str): Имя файла, с которым сохранять.
            folder (str): Папка, куда сохранять.
        Returns:
            str: Путь до файла, куда сохранён текст.
        """
    os.makedirs(folder, exist_ok=True)

    response = requests.get(url)
    response.raise_for_status()

    filename = sanitize_filename(filename)

    split_url = urlsplit(url)
    path = unquote(split_url.path)
    extension = path.split('.')[0].lstrip('/') if '.' in path else 'txt'

    filename = f'{filename}.{extension}'
    file_path = (os.path.join(folder, filename))

    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(response.text)
    return file_path


def download_image(book_url_img, book_id, folder='images/'):

    response = requests.get(book_url_img)
    response.raise_for_status()

    split_url = urlsplit(book_url_img)
    path = unquote(split_url.path)

    extension = path.split('.')[-1] if '.' in path else None
    image_name = f'{book_id}.{extension}' if 'nopic.gif' not in path else 'nopic.gif'

    save_path = os.path.join(folder, image_name)

    with open(save_path, 'wb') as file:
        file.write(response.content)

    logger.info(f"Скачана обложка книги {book_id}")



def main():
    url = 'http://tululu.org/txt.php?id=1'

    filepath = download_txt(url, 'Алиби')
    print(filepath)  # Выведется books/Алиби.txt

    filepath = download_txt(url, 'Али/би', folder='books/')
    print(filepath)  # Выведется books/Алиби.txt

    filepath = download_txt(url, 'Али\\би', folder='txt/')
    print(filepath)  # Выведется txt/Алиби.txt


    # url = f'https://tululu.org/txt.php'
    # os.makedirs('books', exist_ok=True)
    # os.makedirs('images', exist_ok=True)

    # for book_id in range(11):
    #     params = {
    #         'id': book_id
    #     }
    #
    #     try:
    #         response = requests.get(url, params=params, allow_redirects=True)
    #         response.raise_for_status()
    #         if response.history:
    #             continue
    #         book_title, book_author, book_url_img = get_book_info(book_id)
    #         logger.info(f'Заголовок:{book_title}\n{book_url_img}')
    #         filename = f'{book_id}.{sanitize_filename(book_title)}.txt'
    #         download_txt(response, url, filename)
    #         download_image(book_url_img, book_id)
    #     except HTTPError as e:
    #         logger.info(f"Ошибка при запросе книги: {e}")
    #         continue


if __name__ == "__main__":
    main()
