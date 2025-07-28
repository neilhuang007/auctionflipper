# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AuctionFlipper is a Hypixel Skyblock auction analysis system that monitors and evaluates auction items for potential profit opportunities. It combines Python for data collection/processing and Node.js for item valuation.

## Architecture

### Core Components

1. **AuctionFlipperCore.py** - Main entry point that:
   - Updates cached price data from external APIs
   - Runs continuous auction checking loop
   - Manages event loops for async operations

2. **Python Handlers** (in `Handlers/`):
   - **AuctionHandler.py** - Fetches and processes auction data from Hypixel API
   - **ItemValueHandler.py** - Decodes item NBT data and prepares for valuation
   - **DataBaseHandler.py** - MongoDB operations for auction storage
   - **PriceHandler.py** - Manages price data from cached JSON files
   - **ProgressHandler.py** - Progress tracking for batch operations

3. **Evaluator.js** - Node.js component that:
   - Receives item data via stdin from Python
   - Uses `skyhelper-networth` library for item valuation
   - Stores profitable flips in MongoDB

### Data Flow

1. Python fetches auction data from Hypixel API
2. Filters for BIN (Buy It Now) auctions
3. Decodes item bytes (NBT data) to extract item properties
4. Passes item data to Node.js evaluator via subprocess
5. Evaluator calculates net worth and identifies profitable flips
6. Results stored in MongoDB for tracking

## Development Commands

### Python Dependencies
No requirements.txt file exists. Key dependencies used:
- aiohttp, orjson (async HTTP and JSON)
- pymongo (MongoDB client)
- nbtlib (NBT data parsing)
- requests, schedule

### Node.js Setup
```bash
npm install
```

### Running the Application
```bash
python AuctionFlipperCore.py
```

## MongoDB Configuration

- Connection: `mongodb://localhost:27017`
- Database: `skyblock`
- Collections:
  - `auctions` - All auction data
  - `Flips` - Profitable flip opportunities

## External Data Sources

The system caches data from these endpoints:
- Prices: `https://raw.githubusercontent.com/SkyHelperBot/Prices/main/prices.json`
- Lowest BIN: `https://moulberry.codes/lowestbin.json`
- Daily Sales: `https://moulberry.codes/auction_averages/3day.json`

## Key Implementation Notes

- Uses async/await for concurrent auction fetching
- NBT data is base64 encoded and gzipped
- Item evaluation subprocess communication uses JSON via stdin
- Continuous loop with 1-second delay between auction checks
- Initial launch checks all auction pages, then only checks first 2 pages