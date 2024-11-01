"""Checks the pricing of your csfloat stall
 to determine if your currently listed price fulfills your requirement or not"""
import json

import requests
from csfloat.deals_finder import deals_finder_main

with open("../../config.json", "r") as file:
    config = json.load(file)

user_id = config["csfloat"]["steam_user_id"]
URL = f"https://csfloat.com/api/v1/users/{user_id}/stall?limit=40"


if __name__ == '__main__':
    output = requests.get(URL)
    my_json = output.json()
    for listing in my_json["data"]:
        listing_data = deals_finder_main.get_item_details(listing)
        csfloat_minus_buff_price = listing_data[2] - listing_data[3]
        over_under_buff_percentage = round(csfloat_minus_buff_price / listing_data[3] * 100, 2)
        if over_under_buff_percentage < 0:
            print(f"{listing_data[0:2]}. {over_under_buff_percentage}% under buff. buff price is {listing_data[3]}")

