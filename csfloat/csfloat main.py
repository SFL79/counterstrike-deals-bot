import datetime
import gc
import json
import threading
import time
import traceback
import pygsheets
import requests

import buff.buff163 as buff163

with open("../config.json", "r") as file:
    config = json.load(file)

# Accessing values from the JSON data
cookies_path = config["session"]["cookies"]

google_sheets_path = config["googleSheets"]["configPath"]
google_sheet_name = config["googleSheets"]["sheetName"]
sheet_row_index = config["googleSheets"]["sheet_row_index"]

skins_db_path = config["database"]["skinsDbPath"]

priority_pages = config["csfloat"]["priorityPages"]
max_pages = config["csfloat"]["maxPages"]

buff_price_percentage = config["pricing"]["buffPricePercentage"]
minimum_price = config["pricing"]["minimumPrice"]

COOKIES = {
    'session': cookies_path
}


'''google sheets related variables'''
json_file = pygsheets.authorize(
    service_file=google_sheets_path)


with open("../buff_ids.json", "r", encoding='utf-8') as file:
    buff_ids_config = json.load(file)

def get_item_details(listing):
    item_info = listing["item"]
    item_name = item_info["market_hash_name"]
    if item_name[:-1] == " ":
        item_name = item_name[:-1]
    item_name = item_name.replace("'", "''")

    item_id = buff_ids_config["items"].get(item_name, {}).get("buff163_goods_id")
    if item_id is None:
        print("item id {} not found for item: {}".format(item_id, item_name))
        return item_name, None, None, None
    # if item is a skin, it will have a float. Other items such as stickers dont have such property
    try:
        item_float = item_info["float_value"]
    except:
        item_float = None
    price = listing["price"] / 100
    buff_price = buff163.get_item_buff_price(item_id)
    if buff_price is None:
        print("received None buff request for item: " + item_name)
    else:
        # print("csgofloat price is: " + str(price), " buff price is: " + str(buff_price))
        pass
    del item_info
    gc.collect()
    return item_name, item_float, price, buff_price


def write_to_google_sheets(listing):
    global sheet_row_index
    try:
        item_name, item_float, price, buff_price = get_item_details(listing)
        if buff_price is None:
            print("item name for non buff price is " + item_name)
            return
        if buff_price * buff_price_percentage >= price:
            # open the google spreadsheet (where 'PY to Gsheet Test' is the name of my sheet)
            sh = json_file.open('csgofloat alerter')
            # select the first sheet
            wks = sh[0]
            # update the first sheet with df, starting at cell B2.
            current_time = datetime.datetime.now()
            current_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
            wks.update_row(sheet_row_index, [item_name, item_float, price, price / buff_price, current_time])
            sheet_row_index += 1
            print("wrote item: {} to google sheets".format(item_name))
            del sh, wks, current_time
    except:
        traceback.print_exc()
    finally:
        time.sleep(2)


def look_for_discounts(page):
    global max_pages
    while (True):
        try:
            output = requests.get(
                'https://csfloat.com/api/v1/listings?sort_by=most_recent&min_price=10000&page=%d' % page,
                cookies=COOKIES)
            print('https://csfloat.com/api/v1/listings?sort_by=most_recent&min_price=10000&page=%d' % page)
            my_json = output.json()
            ratelimit_remaining = output.headers["x-ratelimit-remaining"]
            print(output.status_code)
            if int(ratelimit_remaining) < priority_pages:
                print(int(output.headers["x-ratelimit-reset"]) - int(time.time()))
                time.sleep(int(output.headers["x-ratelimit-reset"]) - int(time.time()))

            # candidate_list = []
            for listing in my_json:
                if "code" in listing:
                    if listing["code"] == 20:  # too many requests
                        time.sleep(100)
                        break
                    elif listing["code"] == 4:  # request page number is too high
                        max_pages = page
                        print("max pages is: ", max_pages)

                price = listing["price"]
                item = listing["item"]
                if price / 100 > minimum_price:
                    write_to_google_sheets(listing)
                    time.sleep(0.5)
        except:
            traceback.print_exc()
        finally:
            del output, my_json, ratelimit_remaining, listing
            gc.collect()
            page = get_next_page(page)
            time.sleep(5)


def get_next_page(page_num):
    if page_num != 1:
        page_num += 5
    if page_num > max_pages:
        page_num %= 5
    if page_num == 0:
        page_num = 5
    return page_num


def main():
    for i in range(1, 4):
        t1 = threading.Thread(target=look_for_discounts, args=(i,))
        t1.start()
        time.sleep(i)


if __name__ == "__main__":
    main()
