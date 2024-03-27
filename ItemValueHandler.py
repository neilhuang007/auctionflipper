import base64
import nbtlib
import logging
import subprocess
import json
from io import BytesIO
import sys

import requests

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def decode_data(string):
    try:
        # Decode the base64 string
        data = base64.b64decode(string)
        # Parse the NBT data
        nbt_file = nbtlib.File.load(BytesIO(data), gzipped=True)
        # Convert the NBT file to a dictionary
        json_data = dict(nbt_file)
        return json_data
    except Exception as error:
        logging.error(f"Error decoding data: {error}")
        if "PartialReadError" in str(error):
            logging.error("The NBT data may be corrupted or incorrectly formatted.")
        return None


def get_item_networth(itemstats):
    logger.info('item stats received: ' + itemstats)
    inp = decode_data(itemstats.get('item_bytes'))
    # Extract the first item from the 'i' property of the input
    item = inp['i'][0]

    # Load the prices JSON from the local file
    with open('cached/prices.json', 'r') as f:
        prices = json.load(f)

    # Combine the item, prices, and price into a single dictionary
    data = {'item': item, 'prices': prices, 'itemstats': itemstats}

    # Convert the dictionary to a JSON string
    data_json = json.dumps(data)

    # Convert the JSON string to bytes
    data_bytes = data_json.encode()

    print('subproccess triggered with input: ' + data_json)

    # Call the Node.js script and pass the JSON string via stdin
    subprocess.run(['node', 'Evaluator.js'], input=data_bytes)

    return True