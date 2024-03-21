const axios = require('axios');
const { getItemNetworth } = require('skyhelper-networth');
const fs = require('fs');

// Read the JSON data from stdin
let data = '';
process.stdin.on('data', chunk => {
  data += chunk;
});
process.stdin.on('end', () => {
  // Parse the JSON data
  const { item, prices } = JSON.parse(data);

  console.log("itme: " + item)

  // Configure axios to use a proxy
  axios.defaults.proxy = {
    host: '127.0.0.1',
    port: 33210,
    protocol: 'http'
  };

  console.log("input done")

  // Call the getItemNetworth function with your own prices
  getItemNetworth(item, {prices: prices, returnItemData: true})
      .then(networth => {
          console.log(networth)
      })
      .catch(error => {
          // Print the error message
          console.error('Error in getItemNetworth:', error);
          throw error; // Rethrow the error after logging
      });
});