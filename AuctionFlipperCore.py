import json
import logging

import requests
import schedule
import time

from pymongo import MongoClient

import AuctionHandler

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

def updatecachedprices():
    # Load the prices JSON from the URL
    response = requests.get('https://raw.githubusercontent.com/SkyHelperBot/Prices/main/prices.json')
    prices = response.json()

    # Write the prices JSON to the local file
    with open('cached/prices.json', 'w') as f:
        # delete everything in old one and substitute with new json
        json.dump({}, f)
        json.dump(prices, f)

# Keep the script running
while True:
    updatecachedprices()
    # Call CheckAuctions and wait for it to finish
    AuctionHandler.CheckAuctions()
    AuctionHandler.delete_ended_auctions()
    time.sleep(1)