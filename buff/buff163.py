import gc
import json
import re
import sqlite3
import traceback
import urllib.request as request

import bs4 as bs

with open("../config.json", "r") as file:
    config = json.load(file)

skins_db_path = config["database"]["skinsDbPath"]

conn = sqlite3.connect(skins_db_path, check_same_thread=False)
cur = conn.cursor()
INSERT_COMMAND = "INSERT INTO BUFF163_SKINS (itemId, itemName, itemWear, game)" \
                 " VALUES ({}, '{}', '{}', '{}')"
header = {"Accept-Language": "en-US,en;q=0.9"}


def get_item_buff_price(item_id):
    try:
        header = {"Accept-Language": "en-US,en;q=0.9"}
        req = request.Request('https://buff.163.com/goods/{}?from=market#tab=selling'.format(item_id), headers=header)
        source = request.urlopen(req).read()
        soup = bs.BeautifulSoup(source, 'lxml')
        exchange_rate = get_exchange_rate(soup)
        l_layout_bs = soup.find('div', attrs={'class': 'market-list'}).find('div', attrs={'class': 'l_Layout'})
        price = float(l_layout_bs.find(
            'div', attrs={'class': 'detail-summ'}).prettify().split('data-goods-sell-min-price="')[1].split('"')[0]) / 100
        del header, req, source, soup, l_layout_bs
        return price / exchange_rate
    except:
        print('failed in: https://buff.163.com/goods/{}?from=market#tab=selling'.format(item_id))
        traceback.print_exc()
    finally:
        gc.collect()

def get_exchange_rate(soup : bs.BeautifulSoup) -> float:
    # return float(float(
    #         soup.find('script', attrs={'type': 'text/javascript'}).prettify().split('"rate_base_usd": ')[1].split(",")[0]))
    # Find the <script> tag that contains the 'rate_base_usd'
    script_tag = soup.find('script', text=re.compile('rate_base_usd'))

    # Extract the script content
    script_content = script_tag.string

    # Use regex to extract the JSON-like part of the script
    json_data = re.search(r'window\.g\s*=\s*({.*?});', script_content, re.DOTALL).group(1)

    # Parse the JSON data
    data = json.loads(json_data)

    # Extract the value of rate_base_usd
    return float(data['currency']['rate_base_usd'])
