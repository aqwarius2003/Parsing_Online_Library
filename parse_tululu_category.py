import argparse
import os
import json
from requests.exceptions import HTTPError
from urllib.parse import urljoin, urlsplit
from tululu import get_soup, check_for_redirect, download_image, download_txt, parse_book_page, CustomHTTPError
import logging
import sys
import requests
import time

logger = logging.getLogger(__name__)

URL = 'https://tululu.org'


def parse_page_by_category(soup):
    """
    Parse page by category.

    This function takes a soup object as argument,
    finds all book links on the page,
    and returns a list of full urls of books.

    Parameters:
    soup (bs4.BeautifulSoup): soup object of the page.

    Returns:
    list: List of full urls of books.
    """
    book_links = soup.select('table.d_book')
    links = []
    for link in book_links:
        book_link = link.select_one('a')['href']
        full_url = urljoin(URL, book_link)
        links.append(full_url)
    return links


def main():
    logging.basicConfig(level=logging.ERROR)
    logger.setLevel(logging.DEBUG)

    parser = argparse.ArgumentParser(
        description='Скачивает с tululu.ru книги жанра научная фантастика с указанным диапазоном страниц'
    )
    parser.add_argument('--start_page', help='start_page', type=int)
    parser.add_argument('--end_page', nargs='?', help='end_page', type=int)

    parser.add_argument('--dest_folder', type=str, default='.',
                        help='путь к каталогу материалов для скачивания')
    parser.add_argument('--skip_img', action='store_true', default=False,
                        help='не скачивать изображения')
    parser.add_argument('--skip_txt', action='store_true', default=False,
                        help='не скачивать текст книг')

    args = parser.parse_args()

    start_page = args.start_page
    end_page = args.end_page

    category = f'l55/'

    images_folder = os.path.normpath(os.path.join(args.dest_folder, 'images/'))
    books_folder = os.path.normpath(os.path.join(args.dest_folder, 'books/'))

    os.makedirs(images_folder, exist_ok=True)
    os.makedirs(books_folder, exist_ok=True)

    # список для хранения всех найденных ссылок на книги
    all_links = []

    current_page = start_page
    while True:
        if end_page is not None and current_page > end_page:
            break
        try:
            url_parse_page = urljoin(URL, category + str(current_page))
            soup = get_soup(url_parse_page)
            check_for_redirect(soup)

            links = parse_page_by_category(soup)
            all_links.extend(links)
            current_page += 1

        except HTTPError:
            logger.info(f'На странице {current_page} книги закончились')
            break
        except ConnectionError:
            logger.error('ConnectionError: %s', url_parse_page)
            break

    books_data = []
    text_file_url = f'https://tululu.org/txt.php'

    for link in all_links:
        retries = 0
        max_retries = 2
        retry_delay = 2
        while True:
            try:
                soup = get_soup(link)
                book_title, book_author, book_src_img, comments, genres = parse_book_page(soup)
                file_number = urlsplit(link).path.rsplit('/')[1][1:]  # Возвращает типа 550 номер книги на сайте
                params = {
                    'id': file_number
                }
                filename = f'{file_number}.{book_title}'

                if not args.skip_txt:
                    downloaded_text_file_path = os.path.normpath(
                        download_txt(text_file_url, params, filename, books_folder))
                else:
                    downloaded_text_file_path = None
                book_image_url = urljoin(link, book_src_img)
                if not args.skip_img:
                    downloaded_image_path = os.path.normpath(
                        download_image(book_image_url, int(file_number), images_folder))
                else:
                    downloaded_image_path = None

                book_data = {
                    'title': book_title,
                    'author': book_author,
                    'img_src': downloaded_image_path,
                    'book_path': downloaded_text_file_path,
                    'comments': comments,
                    'genres': genres
                }
                books_data.append(book_data)
                break  # Выход из цикла while True, если скачивание успешно

            except CustomHTTPError as e:
                # Обработка ошибки редиректа
                print(f"Редирект для книги {file_number}: {e}", file=sys.stderr)
                break  # Выход из цикла while True, если редирект по этой ссылке

            except HTTPError as e:
                # Общие ошибки HTTP (кроме редиректов)
                print(f"HTTP ошибка при запросе книги {file_number}: {e}.", file=sys.stderr)
                break

            except (ConnectionError, requests.Timeout) as e:
                retries += 1
                print(
                    f'Проблема с книгой {file_number}. '
                    f'Попытка {retries} из {max_retries} из-за проблем с подключением: {e}',
                    file=sys.stderr)

                # Обработка нестабильного соединения или таймаута
                if retries == 1:
                    time.sleep(1)
                    continue
                elif retries == max_retries:
                    print(
                        f'Не удалось скачать книгу {file_number} '
                        f'после {max_retries} попыток из-за проблем с подключением: {e}',
                        file=sys.stderr)
                    break  # Прерывает цикл while True
                else:
                    time.sleep(retry_delay)
                    continue  # Продолжает цикл while True

    with open(os.path.join(args.dest_folder, 'books_data.json'), 'w', encoding='utf-8') as json_file:
        json.dump(books_data, json_file, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    main()
