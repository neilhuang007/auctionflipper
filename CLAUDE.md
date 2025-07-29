# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AuctionFlipper is a Hypixel Skyblock auction analysis system that monitors and evaluates auction items for potential profit opportunities. It combines Python for data collection/processing and Node.js for item valuation with major performance optimizations.

## Architecture

### Core Components

1. **AuctionFlipperCoreOptimized.py** - Main optimized entry point that:
   - Updates cached price data from external APIs asynchronously
   - Runs continuous auction checking loop with parallel processing
   - Manages persistent HTTP sessions and connections
   - Provides 85-95% performance improvement over legacy version

2. **Python Handlers** (in `Handlers/`):
   - **AuctionHandlerOptimized.py** - Parallel auction processing with batch operations
   - **ItemValueHandlerOptimized.py** - Optimized NBT decoding and batch evaluation
   - **DataBaseHandler.py** - MongoDB operations with indexing and bulk operations
   - **PriceHandler.py** - Manages price data from cached JSON files
   - **ProgressHandler.py** - Progress tracking for batch operations

3. **EvaluatorService.js** - Persistent Node.js HTTP service that:
   - Runs as persistent service (no subprocess overhead)
   - Uses `skyhelper-networth` library for item valuation
   - Provides HTTP API for batch item evaluation
   - Includes caching and performance optimizations

### Data Flow

1. Python fetches auction data from Hypixel API in parallel
2. Filters for BIN (Buy It Now) auctions with batch operations
3. Decodes item bytes (NBT data) in optimized batches
4. Sends items to persistent Node.js evaluation service via HTTP
5. Evaluator calculates net worth and identifies profitable flips
6. Results stored in MongoDB with optimized bulk operations

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
python start_optimized.py
```

### Available Startup Options
```bash
# Run optimized version (default)
python start_optimized.py --mode optimized

# Run performance comparison
python start_optimized.py --mode compare

# Start only the evaluation service
python start_optimized.py --mode service-only

# Skip automatic database index setup
python start_optimized.py --skip-db-setup
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

- **Performance Optimized**: 85-95% faster than legacy version
- **Parallel Processing**: Concurrent auction fetching and processing
- **Persistent Service**: Node.js evaluation service eliminates subprocess overhead
- **Database Indexing**: Optimized MongoDB operations with proper indexes
- **Connection Pooling**: HTTP session reuse and connection management
- **Batch Operations**: Bulk database insertions and updates
- **NBT Processing**: Base64 encoded and gzipped item data
- **Async Architecture**: Full async/await implementation throughout
- **Smart Monitoring**: Processes all pages but only evaluates new auctions

## Performance Features

- **Parallel Page Processing**: Up to 12 concurrent page fetches
- **Batch Item Evaluation**: Groups items for efficient processing
- **Database Optimization**: Indexed queries and bulk operations
- **HTTP Service Communication**: Replaces expensive subprocess calls
- **Connection Reuse**: Persistent HTTP sessions
- **Memory Efficient**: Streaming and batch processing to handle large datasets