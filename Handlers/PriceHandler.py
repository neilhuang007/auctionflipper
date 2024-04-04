import json

prices = {}
lowestbin = {}
dailysales = {}

def readprices():
    global prices
    global lowestbin
    global dailysales
    with open('cached/prices.json', 'r') as f:
        prices = json.load(f)

    with open('cached/lowestbin.json', 'r') as f:
        lowestbin = json.load(f)

    with open('cached/DailySales.json', 'r') as f:
        dailysales = json.load(f)


def getprices():
    return prices