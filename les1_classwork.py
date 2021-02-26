import json
from pathlib import Path
import requests
import time


class Parser5ka:
    headers_user_agent_and_accept = {
        "Accept": "application/json",  # формат данных, которые вернёт сервер
        "User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:85.0) Gecko/20100101 Firefox/85.0'
    }

    col_requests = 5  # число запросов, посылаемых серверу в случае неудачи

    def __init__(self, start_url: str, products_path: Path):
        self.start_url = start_url
        self.products_path = products_path # папка в которой будут все файлы продуктов

    def get_response(self, url):
        num_request = 0  # номер запроса
        while num_request != self.col_requests:  # стучимся к серверу
            num_request += 1
            response = requests.get(url, headers=self.headers_user_agent_and_accept)
            if response.status_code == 200:  # код успеха (мы успешно соединились и сервер вернул данные)
                return response
            time.sleep(0.5) # задержка чтобы не положить сервер

    def run(self):
        for data in self.parse_response(self.start_url):
            for product in data:
                product_path = self.products_path.joinpath(f"{product['id']}.json")  # задаём путь для файла продукта
                self.save(product, product_path)

    def parse_response(self, page_url):
        while page_url:  # если страницы нет, то в page_url будет None
            response = self.get_response(page_url)  # получаем документ текущей страницы
            data = response.json()
            # data = json.loads(response.text)  - эквивалентно строке response.json() выше
            page_url = data['next']  # переходим на следующую страницу
            yield data['results']  # возвращает один элемент, в случае повторного вызова parse_response()
                                   # продолжится работа начиная с конца этой строки

    @staticmethod   # статический потому что не используем в нём self
    def save(data: dict, file_path):  # сохранение продукта в отдельный в файл
        file_path.write_text(json.dumps(data, ensure_ascii=False), encoding='UTF-8')


if __name__ == '__main__':
    special_offers_url = 'https://5ka.ru/api/v2/special_offers/'
    save_path = Path(__file__).parent.joinpath('products')
    # если пути save_path нет, то он не создастся автоматически, поэтому нужна проверка
    if not save_path.exists():
        save_path.mkdir()
    parser = Parser5ka(special_offers_url, save_path)
    parser.run()
