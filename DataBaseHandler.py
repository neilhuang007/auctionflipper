import logging
from pymongo import MongoClient

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