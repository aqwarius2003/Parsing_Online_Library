import argparse
import requests
import os
import sys
import time
import logging
from requests.exceptions import HTTPError, ConnectionError
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from urllib.parse import urljoin, urlsplit, unquote
import textwrap

logger = logging.getLogger(__name__)


class CustomHTTPError(requests.HTTPError):
    """Кастомное исключение для обработки ошибок HTTP."""
    pass


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
        raise CustomHTTPError


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
    response = requests.get(url, allow_redirects=True, timeout=5)
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
    title_tag = soup.select_one('h1').text
    if title_tag:
        title_author = title_tag.split('::')
        book_title = title_author[0].strip()
        book_author = title_author[1].strip()
    else:
        logger.warning('Заголовок H1 не найден')
        return None, None, None, None, None

    comments = []
    for comment in soup.select('.texts'):
        span = comment.select_one('span.black')
        if span:
            comments.append(span.text)

    links = soup.select('span.d_book a')
    genres = [link.text.strip() for link in links]

    book_src_img = soup.select_one(".bookimage img")['src']

    return book_title, book_author, book_src_img, comments, genres


def download_txt(url, params, filename, folder='books/'):
    """Функция для скачивания текстовых файлов.
        Args:
            params:
            url (str): Ссылка на текст, который хочется скачать.
            filename (str): Имя файла, с которым сохранять.
            folder (str): Папка, куда сохранять.
        Returns:
            str: Путь до файла, куда сохранён текст.
        Notes:
        - Создает папку, если она не существует.
        - Очищает имя файла от недопустимых символов.
        """
    response = requests.get(url, params=params, timeout=5)
    response.raise_for_status()
    check_for_redirect(response)

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
    response = requests.get(book_url_img, timeout=5)
    response.raise_for_status()
    check_for_redirect(response)
    split_url = urlsplit(book_url_img)
    path = unquote(split_url.path)

    extension = path.split('.')[-1] if '.' in path else None
    image_name = f'{book_id}.{extension}' if 'nopic.gif' not in path else 'nopic.gif'

    save_path = os.path.join(folder, image_name)

    with open(save_path, 'wb') as file:
        file.write(response.content)

    return save_path


def main():
    logging.basicConfig(level=logging.ERROR)
    logger.setLevel(logging.DEBUG)
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
    text_file_url = f'https://tululu.org/txt.php'

    for book_id in range(start_id, end_id + 1):
        retries = 0
        max_retries = 5
        retry_delay = 5
        while True:
            try:
                book_page_url = f'{url}/b{book_id}/'
                soup = get_soup(book_page_url)
                book_title, book_author, book_src_img, comments, genres = parse_book_page(soup)
                params = {
                    'id': book_id
                }
                filename = f'{book_id}.{book_title}'
                downloaded_text_file_path = download_txt(text_file_url, params, filename)
                book_image_url = urljoin(book_page_url, book_src_img)
                downloaded_image_path = download_image(book_image_url, book_id)
                message = f'''
                            Автор: {book_author}
                            Заголовок: {book_title}
                            Изображение: {book_image_url}
                            Пути к скачанным файлам:
                            {downloaded_text_file_path}
                            {downloaded_image_path}
                            Коментарии:
                            {comments}
                            Жанр: {genres}
                            '''
                wrapped_message = '\n'.join(textwrap.shorten(line, width=120, placeholder='...')
                                            for line in message.splitlines())
                logger.info(wrapped_message)
                break

            except CustomHTTPError as e:
                # Обработка ошибки редиректа
                print(f"Редирект для книги {book_id}: {e}", file=sys.stderr)
                break

            except HTTPError as e:
                # Общие ошибки HTTP (кроме редиректов)
                print(f"HTTP ошибка при запросе книги {book_id}: {e}.", file=sys.stderr)
                break

            except (ConnectionError, requests.Timeout) as e:
                retries += 1
                print(
                    f'Проблема с книгой {book_id}.'
                    f'Попытка {retries} из {max_retries} из-за проблем с подключением: {e}',
                    file=sys.stderr)
                # Обработка нестабильного соединения или таймаута

                if retries == 1:
                    time.sleep(1)
                    continue
                elif retries == max_retries:
                    print(
                        f'Не удалось скачать книгу {book_id} '
                        f'после {max_retries} попыток из-за проблем с подключением: {e}',
                        file=sys.stderr)
                    break
                else:
                    time.sleep(retry_delay)
                    continue


if __name__ == "__main__":
    main()
