import requests
import json

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:84.0) Gecko/20100101 Firefox/84.0'}

global_dict = dict()


def get_response(url, **kwargs):
    response = requests.get(url, **kwargs)
    return response


def run(url):
    for products in parse(url):
        for product in products:
            parse_product(product["id"], url)
    save_file()


def parse_product(id_product, url):
    product_url = url+str(id_product)
    response = get_response(product_url, headers=headers)
    data = json.loads(response.text)
    check_value = global_dict.get(data["product"]["group"]["parent_group_name"], None)
    if check_value is None:
        global_dict[data["product"]["group"]["parent_group_name"]] = list()
    global_dict[data["product"]["group"]["parent_group_name"]].append(data)


def parse(url):
    while url:
        response = get_response(url, headers=headers)
        data = json.loads(response.text)
        url = data['next']
        yield data.get('results', [])


def save_file():
    for key, item in global_dict.items():
        file_element = dict()
        file_element['parent_group_name'] = key
        file_element['products'] = item
        with open(f'{key}.json', 'a+', encoding='UTF-8') as file:
            json.dump(file_element, file, ensure_ascii=False)


url_5ka = 'https://5ka.ru/api/v2/special_offers/'
run(url_5ka)