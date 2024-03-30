# Load the prices JSON from the local file
import json

with open('cached/prices.json', 'r') as f:
    prices = json.load(f)

print(prices)

