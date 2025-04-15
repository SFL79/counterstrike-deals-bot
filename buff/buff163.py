import json
import re
import time
import urllib.request as request
from urllib.error import HTTPError

import bs4 as bs

from logger.logger_setup import get_logger

logger = get_logger()
with open("../buff_ids.json", "r", encoding='utf-8') as file:
    buff_ids_config = json.load(file)

def get_item_buff_price(item_id: int) -> float:
    try:
        request_url = 'https://buff.163.com/goods/{}?from=market#tab=selling'.format(item_id)
        source = send_request(request_url)
        if source is not None:
            soup = bs.BeautifulSoup(source, 'lxml')
            exchange_rate = get_exchange_rate(soup)
            l_layout_bs = soup.find('div', attrs={'class': 'market-list'}).find('div', attrs={'class': 'l_Layout'})
            price = float(l_layout_bs.find(
                'div', attrs={'class': 'detail-summ'}).prettify().split('data-goods-sell-min-price="')[1].split('"')[
                              0]) / 100
            return price / exchange_rate
    except Exception as e:
        logger.warning('failed in: https://buff.163.com/goods/{}?from=market#tab=selling'.format(item_id))
        logger.error(e)

def get_item_buff_price_from_name(item_name: str) -> float:
    item_id = buff_ids_config["items"].get(item_name, {}).get("buff163_goods_id")
    return get_item_buff_price(item_id)


def send_request(request_url: str):
    header = {"Accept-Language": "en-US,en;q=0.9"}
    max_retries = 3  # Maximum number of retries
    retries = 0
    while retries < max_retries:
        try:
            # Prepare the request
            req = request.Request(request_url, headers=header)
            # Send the request
            source = request.urlopen(req).read()
            return source  # Return the fetched data if successful

        except HTTPError as e:
            # Check for specific status code 429
            if e.code == 429:
                logger.warning(f"Error 429: Too Many Requests for {request_url}. Retrying...")
                time.sleep(2)  # Wait before retrying
                retries += 1
            else:
                logger.error(f"HTTP error occurred: {e.code} for {request_url}.")
                break  # Exit the loop for other HTTP errors

    return None  # Return None or handle it as needed

def get_exchange_rate(soup: bs.BeautifulSoup) -> float:
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
