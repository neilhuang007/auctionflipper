import base64
import nbtlib
import logging
import subprocess
import json
from io import BytesIO

import requests


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


def get_item_networth(input):
    # Extract the first item from the 'i' property of the input
    item = input['i'][0]

    # Convert the Python dictionary to a JSON string
    item_json = json.dumps(item)

    # Load the prices JSON from the URL
    response = requests.get('https://raw.githubusercontent.com/SkyHelperBot/Prices/main/prices.json')
    prices = response.json()

    # Combine the item and prices into a single dictionary
    data = {'item': item, 'prices': prices}

    # Convert the dictionary to a JSON string
    data_json = json.dumps(data)

    # Convert the JSON string to bytes
    data_bytes = data_json.encode()

    # Call the Node.js script and pass the JSON string via stdin
    subprocess.run(['node', 'Evaluator.js'], input=data_bytes)

item_bytes = 'H4sIAAAAAAAAAF1TzW7TQBCeNCk0gVIEAg5I1SBRAYrSOm0ap721Tfoj9Qc1UAkhVK3tib2qvRt5N5S+AacKBCcE57xH3oQeeAzEOEl/xMHjndnvm/l2NFMCKEJOlgAgNwETMshVcjC5oXvK5kqQtyLMwZ23yktJnAgvplweitsyoM1YhIZJf0twO5CmG4uzIhR2dUpTHH0KDwd9t21TUqGNVnHQ98tLDjzh4EYqLTZFIkIaxRedOXjAF9sk4hFWlKsMzmJN6pAyNArWHHjMsR1lKY5lSMofXyzDLP8b7/m7+PGd7Yf/XFY0M+h7TZ1IJZiGO0dQ4VRbQqqhhvoc/9xgqApPI1IoLHZ6cYzRUNU83GP+nlACX2sd4xHMZfRUKGuY6ZWrjnPx8xxvamPAPBeeZQFvJKUU4LpWPbOKQxk9gy+dhdoraDBuU6dIHyk9w4RiIjyRXDkci6tm0owV/gnqDp/rYz6U+Pz715dhnTxbcNm0hB/dACEDrvnhpWAqO/PVi2+fsX0qVQh3OXIoVEjXuRbZrNlhfecqgUERG81uYE5ll7I4axTIaQOdwELWQ5mSb6VWGElrOfn4YaQoOUNG24iwK2zEj4FpJmT+MNu4cJ3NrjaEVRyJFh1LaSaklil3uQdK22F3suxihMo6nd1mzY6kQWkpQV8o9AhT6ug0pOAZPOLGDPrxbmurtd9cO3yH6wcHb9p5mPR1rFP404YpKOyLhOA+I3lSE8MPWdfacrdhpvXJpmLN2lR6PUumBCVx5fBaBJfjxVoK7Cc8LsddHhf2JzkzLxdMbxzu7LUP9o/HlYueNubY8nxkJK7e6zHqed1Z9Nx6o1FZocZSpba8RJUVt+pU/E7N9QJqeG7HKUDRyoT4+UmXl/f8xdegBTABt0bLxfngH8By43zdAwAA'
decoded_item = decode_data(item_bytes)
get_item_networth(decoded_item)
print(get_item_networth(decoded_item))