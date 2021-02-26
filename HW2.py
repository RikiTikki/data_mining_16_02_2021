"""
Необходимо собрать структуры товаров по акции и сохранить их в MongoDB
пример структуры и типы обязательно хранить поля даты как объекты datetime

{
    "url": str,
    "promo_name": str,
    "product_name": str,
    "old_price": float,
    "new_price": float,
    "image_url": str,
    "date_from": "DATETIME",
    "date_to": "DATETIME",
}
"""
import pymongo
import bs4
import requests
import time
from urllib.parse import urljoin
import datetime as dt


class MagnitParser:
    headers_user_agent_and_accept = {
        "Accept": "application/json",  # формат данных, которые вернёт сервер
        "User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:85.0) Gecko/20100101 Firefox/85.0'
    }

    def __init__(self, start_url, db_client):
        self.start_url = start_url
        self.db = db_client["gb_data_mining_16_02_2021"]

    col_requests = 5

    months = {1: 'января',
              2: 'февраля',
              3: 'марта',
              4: 'апреля',
              5: 'мая',
              6: 'июня',
              7: 'июля',
              8: 'августа',
              9: 'сентября',
              10: 'октября',
              11: 'ноября',
              12: 'декабря'}

    def template(self):
        data_template = {
            'url': lambda a: urljoin(self.start_url, a.attrs.get('href')),
            'promo_name': lambda a: a.find("div", attrs={"class": "card-sale__header"}).text,
            'product_name': lambda a: a.find("div", attrs={"class": "card-sale__title"}).text,
            'old_price': self.search_old_price,
            'new_price': self.search_new_price,
            'image_url': lambda a: urljoin(self.start_url, a.find("img").attrs.get('data-src')),
            'date_from': self.search_date_from,
            'date_to': self.search_date_to
        }
        return data_template

    def get_response(self, url):
        num_request = 0
        while num_request != self.col_requests:
            num_request += 1
            response = requests.get(url, headers=self.headers_user_agent_and_accept)
            if response.status_code == 200:
                return response
            time.sleep(0.5)

    def get_soup(self, url):
        response = self.get_response(url)
        if response:
            soup = bs4.BeautifulSoup(response.text, "lxml")
            return soup

    def parse(self, product_tag_a):
        product_data = {}
        for key, func in self.template().items():
            try:
                product_data[key] = func(product_tag_a)
            except AttributeError:
                pass
        return product_data

    def search_price(self, product_tag_a, type_price):
        price = product_tag_a.find("div", attrs={"class": f"label__price_{type_price}"})
        price_int = price.find("span", attrs={"class": "label__price-integer"}).text
        price_dec = price.find("span", attrs={"class": "label__price-decimal"}).text
        final_price_num = float(price_int + '.' + price_dec)
        return final_price_num

    def search_new_price(self, product_tag_a):
        return self.search_price(product_tag_a, 'new')

    def search_old_price(self, product_tag_a):
        return self.search_price(product_tag_a, 'old')

    def search_date_from(self, product_tag_a):
        return self.search_date(product_tag_a, "from")

    def search_date_to(self, product_tag_a):
        return self.search_date(product_tag_a, "to")

    def search_date(self, product_tag_a, type_date):
        date_list = product_tag_a.find("div", attrs={"class": "card-sale__date"}).text.split()
        if not date_list:
            return None
        pos_day_in_list = None
        pos_month_in_list = None
        if type_date == "from":
            pos_day_in_list = 1
            pos_month_in_list = 2
        if type_date == "to":
            pos_day_in_list = 4
            pos_month_in_list = 5
        if len(date_list) == 3:
            pos_day_in_list = 1
            pos_month_in_list = 2
        month = self.get_number_month(date_list[pos_month_in_list])
        day = int(date_list[pos_day_in_list])

        if type_date == "from":
            if month > dt.datetime.now().month:
                year = dt.datetime.now().year - 1
            else:
                year = dt.datetime.now().year
        if type_date == "to":
            if month >= dt.datetime.now().month:
                year = dt.datetime.now().year
            else:
                year = dt.datetime.now().year + 1
        date = dt.datetime(year, month, day)
        return date

    def get_number_month(self, name):
        for key, value in self.months.items():
            if value == name:
                return key

    def run(self):
        soup = self.get_soup(self.start_url)
        if soup:
            catalog = soup.find("div", attrs={"class": "сatalogue__main"})
            for product_tag_a in catalog.find_all("a", recursive=False):
                product_data = self.parse(product_tag_a)
                self.save(product_data)
        print("Done")

    def save(self, data: dict):
        collection = self.db["my_magnit"]
        collection.insert_one(data)


if __name__ == '__main__':
    start_url = 'https://magnit.ru/promo/?geo=moskva'
    db_client = pymongo.MongoClient()
    parser = MagnitParser(start_url, db_client)
    parser.run()
