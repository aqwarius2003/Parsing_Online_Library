import argparse
import requests
import os
import logging
from requests.exceptions import HTTPError
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from urllib.parse import urljoin, urlsplit, unquote

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def check_for_redirect(response):
    """
    Проверяет, есть ли редирект в ответе HTTP запроса.
    Args:
        response (requests.Response): Ответ HTTP запроса.
    Raises:
        HTTPError: Если в ответе произошел редирект.
    """
    """Проверяет, есть ли редирект. Если есть - выдаст ошибку"""
    if response.history:
        raise HTTPError(f"Редирект на URL: {response.url}")


def get_soup(url):
    """
        Отправляет GET запрос по указанному URL и возвращает объект BeautifulSoup.
        Args:
            url (str): URL страницы, которую нужно парсить.
        Returns:
            BeautifulSoup: Объект BeautifulSoup, содержащий HTML контент страницы.
        Raises:
            HTTPError: Если произошла ошибка HTTP запроса.
        """
    response = requests.get(url, allow_redirects=True)
    response.raise_for_status()
    check_for_redirect(response)
    return BeautifulSoup(response.text, 'lxml')


def parse_book_page(soup):
    """
        Парсит страницу книги и извлекает необходимую информацию.
        Args:
            soup (BeautifulSoup): Объект BeautifulSoup, содержащий HTML контент страницы книги.
        Returns:
            tuple: Кортеж, содержащий заголовок книги, автора, URL изображения, комментарии и жанры.
                   Если заголовок H1 не найден, возвращает (None, None, None...).
        Notes:
            - book_title: Заголовок книги.
            - book_author: Автор книги
            - book_src_img: путь до изображения книги на сайте 'tululu.ru'
            - comments: Список комментариев к книге.
            - genres: Список жанров книги.
        """
    title_tag = soup.find('h1').text
    if title_tag:
        title_author = title_tag.split('::')
        book_title = title_author[0].strip()
        book_author = title_author[1].strip()
    else:
        logger.info('Заголовок H1 не найден')
        return None, None, None, None, None

    comments = []
    for comment in soup.find_all(class_='texts'):
        span = comment.find('span', class_='black')
        if span:
            comments.append(span.text)

    links = soup.find('span', class_='d_book').find_all('a')
    genres = [link.text.strip() for link in links]

    book_src_img = soup.find(class_="bookimage").find('img')['src']

    return book_title, book_author, book_src_img, comments, genres


def download_txt(url, filename, folder='books/'):
    """Функция для скачивания текстовых файлов.
        Args:
            url (str): Ссылка на текст, который хочется скачать.
            filename (str): Имя файла, с которым сохранять.
            folder (str): Папка, куда сохранять.
        Returns:
            str: Путь до файла, куда сохранён текст.
        Notes:
        - Создает папку, если она не существует.
        - Очищает имя файла от недопустимых символов.
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
    """
        Скачивает изображение по указанному URL и сохраняет его в указанной папке.
        Args:
            book_url_img (str): URL изображения.
            book_id (int): ID книги для формирования имени файла.
            folder (str, optional): Папка, куда сохранять изображение. Defaults to 'images/'.
        Returns:
            str: Путь до сохраненного файла.
        Notes:
            - Создает папку, если она не существует.
            - Определяет расширение файла из URL.
        """
    response = requests.get(book_url_img)
    response.raise_for_status()

    split_url = urlsplit(book_url_img)
    path = unquote(split_url.path)

    extension = path.split('.')[-1] if '.' in path else None
    image_name = f'{book_id}.{extension}' if 'nopic.gif' not in path else 'nopic.gif'

    save_path = os.path.join(folder, image_name)

    with open(save_path, 'wb') as file:
        file.write(response.content)

    return save_path


def main():
    parser = argparse.ArgumentParser(
        description='Скачивает с tululu.ru с указанным диапазоном'
    )
    parser.add_argument('start_id', help='start_id', type=int)
    parser.add_argument('end_id', help='end_id', type=int)

    args = parser.parse_args()

    start_id = args.start_id
    end_id = args.end_id

    url = f'https://tululu.org'
    os.makedirs('images', exist_ok=True)
    url_txt = f'https://tululu.org/txt.php'

    for book_id in range(start_id, end_id + 1):
        try:
            url_book = f'{url}/b{book_id}/'
            soup = get_soup(url_book)
            book_title, book_author, book_src_img, comments, genres = parse_book_page(soup)
            url_txt = f'{url_txt}?id{book_id}'
            filename = f'{book_id}.{book_title}'
            path_txt_file = download_txt(url_txt, filename)
            book_url_img = urljoin(url_book, book_src_img)
            path_image = download_image(book_url_img, book_id)
            logger.info(f'\nАвтор: {book_author}\nЗаголовок: {book_title}\nИзображение: {book_url_img}\n'
                        f'Пути к скачанным файлам:\n{path_txt_file}\n{path_image}\n{comments}\n{genres}\n\n')
        except HTTPError as e:
            logger.info(f"Ошибка при запросе книги: {e}")
            continue


if __name__ == "__main__":
    main()
