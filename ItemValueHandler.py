import base64
import nbtlib
import logging
import subprocess
import json
from io import BytesIO
import sys

import requests

import DataBaseHandler
import PriceHandler

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

prices = {}

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
    # logger.info('item stats received: ' + itemstats)
    inp = decode_data(itemstats.get('item_bytes'))
    # Extract the first item from the 'i' property of the input
    item = inp['i'][0]

    # Load the prices JSON from the local file
    prices = PriceHandler.getprices()

    # Combine the item, prices, and price into a single dictionary
    data = {'item': item, 'prices': prices, 'itemstats': itemstats}

    # Convert the dictionary to a JSON string
    data_json = json.dumps(data)

    # Convert the JSON string to bytes
    data_bytes = data_json.encode()

    # print('subproccess triggered with input: ' + data_json)

    # Call the Node.js script and pass the JSON string via stdin
    result = subprocess.run(['node', 'Evaluator.js'], input=data_bytes,capture_output=True)  # Capture output and error messages

    print("evaluated value: " + (result.stdout.decode().strip().split('|')[0]))

    if(float(result.stdout.decode().strip().split('|')[0]) > itemstats['starting_bid']):

        # Get the networth from the result
        networth = float(result.stdout.decode().strip().split('|')[0])
        itemid = result.stdout.decode().strip().split('|')[1].upper()

        lowestbin = PriceHandler.lowestbin.get(itemid)

        dailysales = PriceHandler.dailysales.get(itemid)

        # Calculate the profit
        profit = networth - itemstats['starting_bid']

        # Calculate the price margin
        price_margin = profit / itemstats['starting_bid']

        # Calculate the percentage
        percentage = price_margin * 100

        print('found profitable flip, auction id: ' + str(itemstats['uuid']) + ' profit: ' + str(profit) + ' price margin: ' + str(price_margin) + ' percentage: ' + str(percentage) + '%')

        # Insert the itemstats, profit, price margin, and percentage into the flips collection
        try:
            DataBaseHandler.flips.insert_one({
                'itemstats': itemstats,
                'profit': profit,
                'daily_sales': dailysales,
                'lowest_bin': lowestbin,
                'percentage': percentage
            })
        except Exception as e:
            print("Error inserting into MongoDB:", e)

        print('Insertion successfull')
    return True

# itemjson = {
#       "uuid": "a093eb2522204f89a07bb894fc1bade4",
#       "auctioneer": "d2a388479f244d2386bebfa4fac3e5ef",
#       "profile_id": "b652034c8ed14359bdf4e7947a248147",
#       "coop": [
#         "dc7d7c20a6d4411381f80fc477c172d5",
#         "d2a388479f244d2386bebfa4fac3e5ef"
#       ],
#       "start": 1711790344369,
#       "end": 1711833544369,
#       "item_name": "Storm's Leggings",
#       "item_lore": "§7Gear Score: §d590 §8(1325)\n§7Health: §a+230 §8(+529)\n§7Defense: §a+105 §8(+241.5)\n§7Intelligence: §a+250 §8(+575)\n §8[§8✎§8] §8[§8⚔§8]\n\n§7Reduces the damage you take from\n§7withers by §c10%§7.\n\n§6Full Set Bonus: Witherborn §7(0/4)\n§7Spawns a wither minion every §e30\n§e§7seconds up to a maximum §a1 §7wither.\n§7Your withers will travel to and\n§7explode on nearby enemies.\n\n§7§8This item can be reforged!\n§7§4❣ §cRequires §aThe Catacombs Floor VII\n§aCompletion§c.\n§6§lLEGENDARY DUNGEON LEGGINGS",
#       "extra": "Storm's Leggings Leather Leggings",
#       "category": "armor",
#       "tier": "LEGENDARY",
#       "starting_bid": 9,
#       "item_bytes": "H4sIAAAAAAAAAD1TS2/TQBCe9AFNOCAEEhx4DO9WJcF5pz1RmjQNqoKUtFQVQtXanqar2rthd93Hb0DqiROCE4fwKzhE/JL+EMQ4oT3Y653vsTPj2RxAFjIyBwCZGZiRYeZVBubXdaJcJgezTgwycGNH+YbEkfAjysxCdlOGtBGJgWXR3xxcD6UdRuIsC3Nb2tACR2/Do/Go3iZhsB9wbBXHo7C64vHSWCyWS9UluM+ETRKRO0xBsVwqT9HlamllaSJv0gEpS1O46FWncKlSLLD8CRM6ylEUyQGp4D+rVL00qTPnYfr9kZ+L7+f8/nS1/fY13XKeT9mlR2ESkEV3SBiKWAwIz3SCThwRHhgdwz0mnUiGjUX/jE2CovecYwU2eDEe1TaSKMI+OXyrVWJXcXfC9bVRzK0veq8rS5Dy+0NxoiwKnJphLJXUCumYTOpKZQ/yvDDTUqBVaDEZotMsiMWpjJM4LbGIV9kUJk3Y04nBy/ROJKfijDimaKJUITxgDp0OIx0S8mmK/wkXQYpiSTYtITXkdmwfSovSUYyBUOgTGjrQZkDhY/AmjMrFj59p8T36nEjDDeNstrln68KJQMe+xY1Ia4MfOh24xdi6jocROS6RRYX0mNp4FG212q1uc623h82dbrv1voscaXe67f4szAc60gbu/vqzAHNdERPcZlHfaRO/tLhFg4FUPHQ5uNk65SLXnDPSTxzZhXRw4c5up9/a3+1sb7Z6+5eu7JQkDD5r+D6JkPy8qJXr+Uq1EeaF16jmawGV6+XQC0VtZQ6yTsZknYiHfB/Ov7z5/Q5gBq41J3PBzYJ/gDfyMDADAAA=",
#       "claimed": "false",
#       "claimed_bidders": [],
#       "highest_bid_amount": 0,
#       "last_updated": 1711790344369,
#       "bin": "true",
#       "bids": [],
#       "item_uuid": "8bbeadeba637458da0856ce373d0da69"
#     }
# PriceHandler.readprices()
# # item_bytes = 'H4sIAAAAAAAAAF1TzW7TQBCeNCk0gVIEAg5I1SBRAYrSOm0ap721Tfoj9Qc1UAkhVK3tib2qvRt5N5S+AacKBCcE57xH3oQeeAzEOEl/xMHjndnvm/l2NFMCKEJOlgAgNwETMshVcjC5oXvK5kqQtyLMwZ23yktJnAgvplweitsyoM1YhIZJf0twO5CmG4uzIhR2dUpTHH0KDwd9t21TUqGNVnHQ98tLDjzh4EYqLTZFIkIaxRedOXjAF9sk4hFWlKsMzmJN6pAyNArWHHjMsR1lKY5lSMofXyzDLP8b7/m7+PGd7Yf/XFY0M+h7TZ1IJZiGO0dQ4VRbQqqhhvoc/9xgqApPI1IoLHZ6cYzRUNU83GP+nlACX2sd4xHMZfRUKGuY6ZWrjnPx8xxvamPAPBeeZQFvJKUU4LpWPbOKQxk9gy+dhdoraDBuU6dIHyk9w4RiIjyRXDkci6tm0owV/gnqDp/rYz6U+Pz715dhnTxbcNm0hB/dACEDrvnhpWAqO/PVi2+fsX0qVQh3OXIoVEjXuRbZrNlhfecqgUERG81uYE5ll7I4axTIaQOdwELWQ5mSb6VWGElrOfn4YaQoOUNG24iwK2zEj4FpJmT+MNu4cJ3NrjaEVRyJFh1LaSaklil3uQdK22F3suxihMo6nd1mzY6kQWkpQV8o9AhT6ug0pOAZPOLGDPrxbmurtd9cO3yH6wcHb9p5mPR1rFP404YpKOyLhOA+I3lSE8MPWdfacrdhpvXJpmLN2lR6PUumBCVx5fBaBJfjxVoK7Cc8LsddHhf2JzkzLxdMbxzu7LUP9o/HlYueNubY8nxkJK7e6zHqed1Z9Nx6o1FZocZSpba8RJUVt+pU/E7N9QJqeG7HKUDRyoT4+UmXl/f8xdegBTABt0bLxfngH8By43zdAwAA'
# print(get_item_networth(itemjson))
