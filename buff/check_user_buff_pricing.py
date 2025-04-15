import requests
import json
from buff.buff163 import get_item_buff_price_from_name
from logger.logger_setup import get_logger

logger = get_logger()

def check_inventory_buff_value(steam_id: str, app_id: int = 730, context_id: int = 2):
    total_value = 0.0
    inventory_url = f"https://steamcommunity.com/inventory/{steam_id}/{app_id}/{context_id}?l=english&count=5000"
    item_descriptions_map = {}

    logger.info(f"Fetching inventory for Steam ID: {steam_id} from {inventory_url}")

    try:
        response = requests.get(inventory_url, timeout=30)
        response.raise_for_status()
        inventory_data = response.json()

        if not inventory_data or not inventory_data.get('success'):
            error_message = inventory_data.get('Error', 'Unknown error') if inventory_data else 'Empty response'
            logger.error(f"Failed to fetch inventory or inventory is private/empty. Response: {error_message}")
            return

        descriptions = inventory_data.get('descriptions')
        assets = inventory_data.get('assets')

        if not descriptions or not assets:
            logger.warning(f"Inventory data for {steam_id} is missing 'descriptions' or 'assets'. Might be empty.")
            return

        for desc in descriptions:
            classid = desc.get('classid')
            instanceid = desc.get('instanceid', '0')
            market_hash_name = desc.get('market_hash_name')
            if classid and market_hash_name:
                item_descriptions_map[f"{classid}_{instanceid}"] = market_hash_name

        logger.info(f"Found {len(assets)} items in inventory. Fetching Buff prices...")

        for i, asset in enumerate(assets):
            classid = asset.get('classid')
            instanceid = asset.get('instanceid', '0')
            asset_key = f"{classid}_{instanceid}"

            market_hash_name = item_descriptions_map.get(asset_key)

            if market_hash_name:
                try:
                    buff_price = get_item_buff_price_from_name(market_hash_name)

                    if buff_price is not None and isinstance(buff_price, (float, int)):
                        logger.info(f"- {market_hash_name}: ${buff_price:.2f}")
                        total_value += buff_price
                    else:
                        logger.warning(f"Could not retrieve Buff price for: {market_hash_name} (Item ID might be missing or Buff error)")

                except Exception as e:
                    logger.error(f"Error getting Buff price for {market_hash_name}: {e}")
            else:
                logger.warning(f"Could not find market_hash_name for asset with classid {classid}, instanceid {instanceid}")

            if (i + 1) % 50 == 0:
                 logger.info(f"Processed {i + 1}/{len(assets)} items...")

        logger.info("------------------------------------")
        logger.info(f"Total Estimated Buff Value: ${total_value:.2f}")
        logger.info("------------------------------------")
        logger.info(f"Finished processing inventory for {steam_id}. Total estimated Buff value: ${total_value:.2f}")

    except requests.exceptions.Timeout:
        logger.error(f"Request timed out while fetching inventory for {steam_id}.")
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred: {http_err} while fetching inventory for {steam_id}.")
    except requests.exceptions.RequestException as req_err:
        logger.error(f"An error occurred during the request: {req_err} for {steam_id}.")
    except json.JSONDecodeError:
        logger.error(f"Failed to decode JSON response from Steam inventory for {steam_id}.")
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")

if __name__ == '__main__':
    test_steam_id = "76561198171832866/"
    if test_steam_id == "YOUR_STEAM_ID_64":
        logger.info("Please replace 'YOUR_STEAM_ID_64' with an actual SteamID64 in the code.")
    else:
        check_inventory_buff_value(test_steam_id)
