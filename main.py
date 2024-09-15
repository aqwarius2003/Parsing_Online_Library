import requests
import os
from requests.exceptions import HTTPError


def check_for_redirect(response):
    if response.history:
        raise HTTPError(f"Редирект на URL: {response.url}")


def save_book(response, path):
    with open(path, 'wb') as file:
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
        save_book(response=response, path=f'books/id_{book_id}.txt')


if __name__ == "__main__":
    main()
