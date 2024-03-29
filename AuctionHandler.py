import logging
from pymongo import MongoClient
import requests
import concurrent.futures
import orjson
from tqdm import tqdm
import time

import DataBaseHandler
import ItemValueHandler

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def process_auction(auction):
    # Check if 'bin' is true and the auction is not already in the database
    if auction.get('bin', False) and auction.get('claimed') == False and DataBaseHandler.auctions.find_one({'uuid': auction['uuid']}) is None:
        # Create a dictionary for each auction with the required fields
        item = {
            'name': auction['item_name'],
            'tier': auction['tier'],
            'price': auction['starting_bid'],
            'bin': auction['bin'],
            'item_bytes': auction['item_bytes'],
            'uuid': auction['uuid'],
            'start': auction['start'],
            'end': auction['end']
        }

        # Check if 'coop' is present
        if 'coop' in auction:
            for uuid in auction['coop']:
                item['seller'] = uuid
            # Set 'seller' to the names of the coop members

        else:
            item['seller'] = auction['auctioneer']

        # # Insert the item into the database
        DataBaseHandler.auctions.insert_one(item)
        # Do the evaluation of item and pass it as a json to the nodejs script
        ItemValueHandler.get_item_networth(item)
        return item
    else:
        return None

def process_page(page):
    # Make a GET request to the API for the given page
    response = requests.get(f'https://api.hypixel.net/skyblock/auctions?page={page}')
    data = orjson.loads(response.content)
    with concurrent.futures.ThreadPoolExecutor(max_workers=14) as executor:
        # Wrap the iterable with tqdm() to show a progress bar
        executor.map(process_auction, tqdm(data['auctions']))

def delete_ended_auctions():
    # Make a GET request to the API to get the ended auctions
    logger.debug('Making request to API to get ended auctions...')
    response = requests.get('https://api.hypixel.net/v2/skyblock/auctions_ended')
    data = orjson.loads(response.content)

    # Iterate over the auctions
    for auction in data['auctions']:
        # Check if the auction ended in the last 60 seconds
        if auction['uuid'] in DataBaseHandler.auctions.find_one({'uuid': auction['uuid']}):
            # Delete the auction from the MongoDB collection
            DataBaseHandler.auctions.delete_one({'uuid': auction['auction_id']})
            logger.debug(f'Deleted auction {auction["auction_id"]} from the database.')

def CheckAuctions():
    # Make a GET request to the API to get the total number of pages
    logger.debug('Making request to API...')
    response = requests.get('https://api.hypixel.net/skyblock/auctions')
    data = orjson.loads(response.content)
    total_pages = data['totalPages']
    logger.debug(f'Received response from API. Total pages: {total_pages}')

    with concurrent.futures.ThreadPoolExecutor(max_workers=14) as executor:
        # Wrap the iterable with tqdm() to show a progress bar
        futures = {executor.submit(process_page, page) for page in tqdm(range(total_pages), desc="Processing auctions")}
        for future in concurrent.futures.as_completed(futures):
            future.result()