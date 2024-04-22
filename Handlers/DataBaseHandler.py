import logging
from pymongo import MongoClient

# # Set up logging
# logging.basicConfig(level=logging.DEBUG)
# logger = logging.getLogger(__name__)

# Create a MongoDB client
print('Connecting to MongoDB...')
client = MongoClient('mongodb://localhost:27017/')
print('Connected to MongoDB.')

# Connect to the 'Skyblock' database
db = client['skyblock']

# Connect to the 'Auctions' collection
auctions = db['Auctions']

flips = db['Flips']

AuctionInsertion = []


def bulk_insert_auctions():
    global AuctionInsertion
    if len(AuctionInsertion) == 0:
        return
    # Use Motor's insert_many method for bulk insertion
    result = auctions.insert_many(AuctionInsertion)
    print(f'Inserted {len(result.inserted_ids)} documents')
    AuctionInsertion = []


def InsertAuction(auction):
    global AuctionInsertion
    AuctionInsertion.append(auction)

