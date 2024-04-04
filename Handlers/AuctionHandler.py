import asyncio
import logging

import aiohttp
from pymongo import MongoClient
import requests
import concurrent.futures
import orjson

import time

from Handlers import ItemValueHandler, DataBaseHandler, ProgressHandler


# Set up logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

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

        # # Do the evaluation of item and pass it as a json to the nodejs script
        ItemValueHandler.get_item_networth(auction)
        ProgressHandler.updatepbar(1)
        return item
    else:
        ProgressHandler.updatepbar(1)
        return None

async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()

async def process_page(page):
    async with aiohttp.ClientSession() as session:
        response = await fetch(session, f'https://api.hypixel.net/skyblock/auctions?page={page}')
        data = orjson.loads(response)
        with concurrent.futures.ThreadPoolExecutor(max_workers=14) as executor:
            executor.map(process_auction, data['auctions'])

async def CheckAuctions():
    print('Making request to API...')
    async with aiohttp.ClientSession() as session:
        response = await fetch(session, 'https://api.hypixel.net/skyblock/auctions')
        data = orjson.loads(response)
        total_pages = data['totalPages']
        totalAuctions = data['totalAuctions']
        print(f'Received response from API. Total pages: {total_pages}')
        ProgressHandler.createpbar(totalAuctions)

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            futures = {executor.submit(asyncio.run, process_page(page)) for page in range(total_pages)}
            for future in concurrent.futures.as_completed(futures):
                future.result()

    print('Finished processing all pages.')
    return True

def delete_ended_auctions():
    # Make a GET request to the API to get the ended auctions
    print('Making request to API to get ended auctions...')
    response = requests.get('https://api.hypixel.net/v2/skyblock/auctions_ended')
    data = orjson.loads(response.content)

    # Iterate over the auctions
    for auction in data['auctions']:
        # Check if the auction ended in the last 60 seconds
        db_auction = DataBaseHandler.auctions.find_one({'uuid': auction['uuid']})
        if db_auction and auction['uuid'] == db_auction['uuid']:
            # Delete the auction from the MongoDB collection
            DataBaseHandler.auctions.delete_one({'uuid': auction['auction_id']})
            print(f'Deleted auction {auction["auction_id"]} from the database.')
    print('Finished deleting ended auctions.')
    return True