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

        db = client.db(dbName);
        collection = db.collection('Flips');
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
    // Parse the data into a JSON object
  const inputData = JSON.parse(data);

  // Extract the item, prices, and price properties from the inputData object
  const { item, prices} = inputData;

    // Call the getItemNetworth function with your own prices
    getItemNetworth(item, {prices: prices, returnItemData: true})
        .then(networth => {
            console.log(networth.price + "|" + networth.id)
            throw (networth.id)
    })
    .catch(error => {
      // Print the error message
      console.error('Error in getItemNetworth:', error);
      throw error; // Rethrow the error after logging
    });
});