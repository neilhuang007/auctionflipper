const { getItemNetworth } = require('skyhelper-networth');
const fs = require('fs');

// Get the NBT data from the command line arguments
const item = JSON.parse(process.argv[2]);

// Call the getItemNetworth function
getItemNetworth(item)
    .then(networth => {
        // Write the networth to the output file
        fs.writeFile('output.json', JSON.stringify(networth), err => {
            if (err) {
                console.error('Error writing file:', err);
            }
        });
    })
    .catch(error => {
        // Print the error message
        console.error(error.message);
    });