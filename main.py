import requests
import os
from requests.exceptions import HTTPError
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename


def check_for_redirect(response):
    if response.history:
        raise HTTPError(f"Редирект на URL: {response.url}")


def get_book_info(book_id):
    url = f'https://tululu.org/b{book_id}'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'lxml')
    title_tag = soup.find('h1').text
    if title_tag:
        title_author = title_tag.split('::')
        book_title = title_author[0].strip()
        book_author = title_author[1].strip()
    else:
        print('Заголовок H1 не найден')

    try:
        book_url_img = soup.find(class_="bookimage").find('img')['src']
    except AttributeError:
        print(f"Изображение книги {book_id =} не найдено")

    return book_title, book_author, book_url_img


def download_txt(response, title, book_id, folder='books/'):
    filename = f'{book_id}.{sanitize_filename(title)}.txt'
    with open(os.path.join(folder, filename), 'wb') as file:
        file.write(response.content)


def main():
    url = f'https://tululu.org/txt.php'
    os.makedirs('books', exist_ok=True)

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


if __name__ == "__main__":
    main()
