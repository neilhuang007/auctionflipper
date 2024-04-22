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
    if auction.get('bin', False) and auction.get('claimed') == False:
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
        DataBaseHandler.InsertAuction(item)

        # # Do the evaluation of item and pass it as a json to the nodejs script
        ItemValueHandler.get_item_networth(auction)
        ProgressHandler.updatepbar(1)
        return True
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

        # Get all auction UUIDs from the database and store them in a set
        existing_auctions_uuids = set(auction['uuid'] for auction in DataBaseHandler.auctions.find({}))

        # Count the number of auctions that already exist in the database
        existing_auctions_count = sum(1 for auction in data['auctions'] if auction['uuid'] in existing_auctions_uuids)

        # Filter out auctions that already exist in the database
        data['auctions'] = [auction for auction in data['auctions'] if auction['uuid'] not in existing_auctions_uuids]

        # print(f'Processing page {page} with {len(data["auctions"])} auctions')
        # print(f'{existing_auctions_count} auctions already exist in the database')

        ProgressHandler.updatepbar(existing_auctions_count)

        with concurrent.futures.ThreadPoolExecutor(max_workers=14) as executor:
            executor.map(process_auction, data['auctions'])

        # Update the progress bar by the number of auctions removed
        ProgressHandler.updatepbar(existing_auctions_count)

        DataBaseHandler.bulk_insert_auctions()

async def CheckAuctions(total_pages):
    print('Making request to API...')
    async with aiohttp.ClientSession() as session:
        response = await fetch(session, 'https://api.hypixel.net/skyblock/auctions')
        data = orjson.loads(response)
        totalAuctions = data['totalAuctions']
        print(f'Received response from API. Total pages: {total_pages}')
        ProgressHandler.createpbar(totalAuctions)

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            futures = {executor.submit(asyncio.run, process_page(page)) for page in range(total_pages)}
            for future in concurrent.futures.as_completed(futures):
                future.result()

    print('Finished processing all pages.')
    ProgressHandler.deletepbar()
    return True

def delete_ended_auctions():
    # Make a GET request to the API to get the ended auctions
    print('Making request to API to get ended auctions...')
    response = requests.get('https://api.hypixel.net/v2/skyblock/auctions_ended')
    data = orjson.loads(response.content)
    deleted = 0
    # Iterate over the auctions
    for auction in data['auctions']:
        # Check if the auction ended in the last 60 seconds
        db_auction = DataBaseHandler.auctions.find_one({'uuid': auction['auction_id']})
        if db_auction and auction['auction_id'] == db_auction['uuid']:
            # Delete the auction from the MongoDB collection
            DataBaseHandler.auctions.delete_one({'uuid': auction['auction_id']})
            deleted += 1
    print(f'Deleted {deleted} auctions from the database.')


    print('Finished deleting ended auctions.')
    return True