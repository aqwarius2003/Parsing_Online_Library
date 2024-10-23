import requests
import os
from requests.exceptions import HTTPError
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlsplit, unquote
import time
from tululu import get_soup, check_for_redirect, CustomHTTPError
import logging

logger = logging.getLogger(__name__)

URL = 'https://tululu.org'

def parse_page_by_category(soup):
    book_links = soup.find_all('table', class_='d_book')
    links = []
    for link in book_links:
        book_link = link.find('a')['href']
        full_url = urljoin(URL, book_link)
        links.append(full_url)
    return links

def main():
    logging.basicConfig(level=logging.ERROR)
    logger.setLevel(logging.DEBUG)

    category = f'l55/'
    os.makedirs('images', exist_ok=True)

    # количество страниц для парсинга
    quantity_pages = 10
    # пустой список для хранения весех найденых ссылок на книги
    all_links = []

    for i in range(1, quantity_pages + 1):
        try:
            url_parse_page = urljoin(URL,category, str(i))
            soup = get_soup(url_parse_page)
            check_for_redirect(soup)

            links = parse_page_by_category(soup)
            all_links.extend(links)
        except HTTPError:
            logger.error('HTTPError: %s', url_parse_page)
            break
        except ConnectionError:
            logger.error('ConnectionError: %s', url_parse_page)
            break

    for link in all_links:
        print(link)
    print(f'Выше {len(all_links)} ссылок от книг по теме научная фантастика с {quantity_pages} страниц')



if __name__ == '__main__':
    main()
