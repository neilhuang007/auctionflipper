import logging
from pymongo import MongoClient
import requests
import concurrent.futures
import orjson
from tqdm import tqdm
import time

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create a MongoDB client
logger.debug('Connecting to MongoDB...')
client = MongoClient('mongodb://localhost:27017/')
logger.debug('Connected to MongoDB.')

# Connect to the 'Skyblock' database
db = client['skyblock']

# Connect to the 'Auctions' collection
auctions = db['Auctions']

# Define the headers for the authentication
headers = {
    'Authorization': '36191ebd-3e72-4757-998a-2b98f415b488'
}

# Make a GET request to the API to get the total number of pages
logger.debug('Making request to API...')
response = requests.get('https://api.hypixel.net/skyblock/auctions', headers=headers)
data = orjson.loads(response.content)
total_pages = data['totalPages']
logger.debug(f'Received response from API. Total pages: {total_pages}')

def process_auction(auction):
    # Check if 'bin' is true and the auction is not already in the database
    if auction.get('bin', False) and auction.get('claimed') == False and auctions.find_one({'uuid': auction['uuid']}) is None:
        # Create a dictionary for each auction with the required fields
        item = {
            'name': auction['item_name'],
            'tier': auction['tier'],
            'price': auction['starting_bid'],
            'bin': auction['bin'],
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
        # auctions.insert_one(item)
        logger.debug(f'Inserted item {item["uuid"]} into the database.')
        return item
    else:
        return None

def process_page(page):
    # Make a GET request to the API for the given page
    response = requests.get(f'https://api.hypixel.net/skyblock/auctions?page={page}', headers=headers)
    data = orjson.loads(response.content)

    with concurrent.futures.ThreadPoolExecutor(max_workers=14) as executor:
        executor.map(process_auction, data['auctions'])

def delete_ended_auctions():
    # Make a GET request to the API to get the ended auctions
    logger.debug('Making request to API to get ended auctions...')
    response = requests.get('https://api.hypixel.net/v2/skyblock/auctions_ended', headers=headers)
    data = orjson.loads(response.content)

    # Iterate over the auctions
    for auction in data['auctions']:
        # Check if the auction ended in the last 60 seconds
        if auction['uuid'] in auctions.find_one({'uuid': auction['uuid']}):
            # Delete the auction from the MongoDB collection
            auctions.delete_one({'uuid': auction['auction_id']})
            logger.debug(f'Deleted auction {auction["auction_id"]} from the database.')

while True:
    # Use a ThreadPoolExecutor to process the pages in separate threads
    with concurrent.futures.ThreadPoolExecutor(max_workers=14) as executor:
        futures = {executor.submit(process_page, page) for page in tqdm(range(total_pages))}
        for future in concurrent.futures.as_completed(futures):
            future.result()
    # Update the auctions every 5 seconds
    delete_ended_auctions()
    time.sleep(5)