from pymongo import MongoClient

# Create a MongoDB client
client = MongoClient('mongodb://localhost:27017/')

# Connect to the 'Skyblock' database
db = client['skyblock']

# Connect to the 'Flips' collection
flips = db['Flips']

# Retrieve all documents from the 'flips' collection and sort them by 'profit' in descending order
results = flips.find().sort('profit', -1)

# Print the results
for result in results:
    print(result['itemstats']['uuid'], result['profit'])