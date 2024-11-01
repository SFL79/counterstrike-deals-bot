import datetime
import json
import threading
import time
import pygsheets
import requests
import schedule

import buff.buff163 as buff163
from logs.logger_setup import get_logger

with open("../../config.json", "r") as file:
    config = json.load(file)

# Accessing values from the JSON data
cookies_path = config["session"]["cookies"]

google_sheets_path = config["googleSheets"]["configPath"]
google_sheet_name = config["googleSheets"]["sheetName"]
sheet_row_index = config["googleSheets"]["sheet_row_index"]

skins_db_path = config["database"]["skinsDbPath"]

priority_pages = config["csfloat"]["priorityPages"]
max_pages = config["csfloat"]["maxPages"]
num_of_threads = config["csfloat"]["numOfThreads"]

buff_price_percentage = config["pricing"]["buffPricePercentage"]
minimum_price = config["pricing"]["minimumPrice"]
target_payment_rate = config["pricing"]["targetPaymentRate"]

COOKIES = {
    'session': cookies_path
}

'''google sheets related variables'''
json_file = pygsheets.authorize(service_file=google_sheets_path)

with open("../../buff_ids.json", "r", encoding='utf-8') as file:
    buff_ids_config = json.load(file)

logger = get_logger()


def get_item_details(listing):
    item_info = listing["item"]
    item_name = item_info["market_hash_name"]
    if item_name[:-1] == " ":
        item_name = item_name[:-1]

    item_id = buff_ids_config["items"].get(item_name, {}).get("buff163_goods_id")
    if item_id is None:
        logger.warning("item id {} not found for item: {}".format(item_id, item_name))
        return item_name, None, None, None
    # if item is a skin, it will have a float. Other items such as stickers dont have such property
    item_float = item_info.get("float_value")
    if item_float is None:
        item_float = -1
    price = listing["price"] / 100
    buff_price = buff163.get_item_buff_price(item_id)
    if buff_price is None:
        logger.warning("received None buff request for item: " + item_name)
    return item_name, item_float, price, buff_price


def write_to_google_sheets(listing):
    global sheet_row_index
    try:
        item_name, item_float, price, buff_price = get_item_details(listing)
        if buff_price is None:
            logger.warning("item name for non buff price is " + item_name)
            return
        if buff_price * buff_price_percentage >= price:
            # open the google spreadsheet
            sh = json_file.open(google_sheet_name)
            # select the first sheet
            wks = sh[0]
            # update the first sheet with df, starting at cell B2.
            current_time = datetime.datetime.now()
            current_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
            # calculate desired target payment. str to avoid automatic conversion to Date data type by sheets
            target_payment = str(buff_price * target_payment_rate)

            wks.update_row(sheet_row_index, [item_name, item_float, price, price / buff_price, current_time, target_payment])
            sheet_row_index += 1
            logger.info("wrote item: {} to google sheets".format(item_name))
    except Exception as e:
        logger.error(e)
    finally:
        time.sleep(2)


items_checked = 0


def look_for_discounts(page):
    global max_pages
    global items_checked
    while True:
        try:
            output = requests.get(
                'https://csfloat.com/api/v1/listings?sort_by=most_recent&min_price=10000&page=%d' % page,
                cookies=COOKIES)
            logger.info('https://csfloat.com/api/v1/listings?sort_by=most_recent&min_price=10000&page=%d' % page)
            my_json = output.json()
            ratelimit_remaining = output.headers["x-ratelimit-remaining"]
            logger.info(output.status_code)
            if int(ratelimit_remaining) < priority_pages:
                logger.info(int(output.headers["x-ratelimit-reset"]) - int(time.time()))
                time.sleep(int(output.headers["x-ratelimit-reset"]) - int(time.time()))

            for listing in my_json["data"]:
                if "code" in listing:
                    if listing["code"] == 20:  # too many requests
                        time.sleep(100)
                        break
                    elif listing["code"] == 4:  # request page number is too high
                        max_pages = page
                        logger.info("max pages is: ", max_pages)

                price = listing["price"]
                listing_type = listing["type"]
                if price / 100 > minimum_price and listing_type == "buy_now":
                    write_to_google_sheets(listing)
                    items_checked += 1
                    time.sleep(0.3)
        except Exception as e:
            logger.error(e)
        finally:
            page = get_next_page(page)
            time.sleep(3)


def get_next_page(page_num):
    if page_num != 1:
        page_num += num_of_threads - 1
    if page_num > max_pages:
        page_num %= num_of_threads - 1
    if page_num == 0:
        page_num = num_of_threads - 1
    return page_num


def log_items_checked():
    logger.info(f"Checked {items_checked} items so far")


def main():
    schedule.every(30).seconds.do(log_items_checked)

    for i in range(1, num_of_threads + 1):
        t1 = threading.Thread(target=look_for_discounts, args=(i,))
        t1.start()
        time.sleep(i)

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()
