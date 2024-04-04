import asyncio
import json
import logging
import os

import requests
import schedule
import time

from pymongo import MongoClient

from Handlers import PriceHandler, AuctionHandler

# Set up logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

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




# Keep the script running
while True:
    UpdateCachedPrices()
    UpdateDailySales()
    UpdateLowestBin()
    PriceHandler.readprices()

    # Create a new event loop
    loop = asyncio.new_event_loop()
    # Set the event loop for the current OS thread
    asyncio.set_event_loop(loop)
    try:
        # Call CheckAuctions and wait for it to finish
        loop.run_until_complete(AuctionHandler.CheckAuctions())
    finally:
        # Close the event loop
        loop.close()

    print('auctions updated')
    AuctionHandler.delete_ended_auctions()
    print('auctions deleted')
    time.sleep(1)
