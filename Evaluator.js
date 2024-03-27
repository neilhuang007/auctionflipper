const axios = require('axios');
const { getItemNetworth } = require('skyhelper-networth');
const fs = require('fs');
const mongodb = require('mongodb');
const MongoClient = mongodb.MongoClient;

// Connection URL
// Enable command monitoring for debugging
const client = new MongoClient('mongodb://localhost:27017', { monitorCommands: true });

// Database Name
const dbName = 'skyblock';

let db;
let collection;

// Connect to the MongoDB server
client.connect()
    .then(() => {
        console.log("Connected successfully to server");

        db = client.db(dbName);
        collection = db.collection('Flips');
        console.log('Database collection connected')
    })
    .catch(err => {
        console.error('Error connecting to MongoDB:', err);
        process.exit(1)
        throw err;
    });

// Read the JSON data from stdin
let data = '';
process.stdin.on('data', chunk => {
  data += chunk;
});
process.stdin.on('end', () => {
    console.log('data received')
    // Parse the data into a JSON object
  const inputData = JSON.parse(data);

  // Extract the item, prices, and price properties from the inputData object
  const { item, prices, itemstats } = inputData;
    console.log(itemstats)

    // Call the getItemNetworth function with your own prices
    getItemNetworth(item, {prices: prices, returnItemData: true})
        .then(networth => {
            console.log('Networth retreived:', networth.price);
            console.log('Price:', itemstats['starting_bid']);
            // If the price in the returned JSON is higher than the selling price
            if (networth.price > itemstats['starting_bid']) {
                  console.log('This item is worth flipping!');
                  // Add the item to the database
                  console.log('uuid:', itemstats['uuid'], 'price:', itemstats['starting_bid'], 'worth:', networth.price, 'profit:', networth.price - itemstats['starting_bid'], 'margin:', ((networth.price - itemstats['starting_bid']) / itemstats['starting_bid'])) * 100;
                  collection.insertOne({ auctionuuid: itemstats['uuid'], price: itemstats['starting_bid'], worth: networth.price, profit: networth.price - itemstats['starting_bid'], margin: ((networth.price - itemstats['starting_bid']) / itemstats['starting_bid']) * 100 })
                      .then(result => {
                          console.log('Item added to database:', result);
                          process.exit(0);
                      })
                      .catch(error => {
                          console.error('Error adding item to database:', error);
                          throw error;
                      });
            }
    })
    .catch(error => {
      // Print the error message
      console.error('Error in getItemNetworth:', error);
      process.exit(1)
      throw error; // Rethrow the error after logging
    });
});