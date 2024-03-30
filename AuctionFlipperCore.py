import json
import logging
import os

import requests
import schedule
import time

from pymongo import MongoClient

import AuctionHandler
import PriceHandler

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

def UpdateCachedPrices():
    # Load the prices JSON from the URL
    response = requests.get('https://raw.githubusercontent.com/SkyHelperBot/Prices/main/prices.json')
    prices = response.json()

    # Check if the file exists
    if not os.path.exists('cached/prices.json'):
        # If the file doesn't exist, create an empty JSON file
        with open('cached/prices.json', 'w') as f:
            json.dump({}, f)

    # Write the prices JSON to the local file
    with open('cached/prices.json', 'w') as f:
        # delete everything in old one and substitute with new json
        json.dump(prices, f)


def UpdateLowestBin():
    # Load the prices JSON from the URL
    response = requests.get('https://moulberry.codes/lowestbin.json')
    prices = response.json()

    # Check if the file exists
    if not os.path.exists('cached/lowestbin.json'):
        # If the file doesn't exist, create an empty JSON file
        with open('cached/lowestbin.json', 'w') as f:
            json.dump({}, f)

    # Write the prices JSON to the local file
    with open('cached/lowestbin.json', 'w') as f:
        # delete everything in old one and substitute with new json
        json.dump(prices, f)

def UpdateDailySales():
    # Load the prices JSON from the URL
    response = requests.get('https://moulberry.codes/auction_averages/3day.json')
    prices = response.json()

    # Check if the file exists
    if not os.path.exists('cached/DailySales.json'):
        # If the file doesn't exist, create an empty JSON file
        with open('cached/DailySales.json', 'w') as f:
            json.dump({}, f)

    # Write the prices JSON to the local file
    with open('cached/DailySales.json', 'w') as f:
        # delete everything in old one and substitute with new json
        json.dump(prices, f)



# # Keep the script running
while True:
    UpdateCachedPrices()
    UpdateDailySales()
    UpdateLowestBin()
    # Call CheckAuctions and wait for it to finish
    AuctionHandler.CheckAuctions()
    print('auctions updated')
    AuctionHandler.delete_ended_auctions()
    print('auctions deleted')
    time.sleep(1)
