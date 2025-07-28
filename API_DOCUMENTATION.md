# AuctionFlipper API Documentation

This document provides comprehensive documentation for all APIs, interfaces, and data structures used in the AuctionFlipper project.

## Table of Contents

1. [External APIs](#external-apis)
2. [Internal Python APIs](#internal-python-apis)
3. [Node.js Interfaces](#nodejs-interfaces)
4. [Database Schemas](#database-schemas)
5. [Data Flow Interfaces](#data-flow-interfaces)

---

## External APIs

### Hypixel Skyblock API

#### Get Auction Data
**Endpoint**: `https://api.hypixel.net/skyblock/auctions`

**Method**: GET

**Parameters**:
- `page` (optional): Page number for pagination (default: 0)

**Response Structure**:
```json
{
  "success": true,
  "page": 0,
  "totalPages": 150,
  "totalAuctions": 75000,
  "lastUpdated": 1647891234567,
  "auctions": [
    {
      "uuid": "string",
      "auctioneer": "string", 
      "profile_id": "string",
      "coop": ["string"],
      "start": 1647891234567,
      "end": 1647891234567,
      "item_name": "string",
      "item_lore": "string",
      "extra": "string",
      "category": "string",
      "tier": "COMMON|UNCOMMON|RARE|EPIC|LEGENDARY|MYTHIC",
      "starting_bid": 1000,
      "item_bytes": "base64_encoded_nbt_data",
      "claimed": false,
      "claimed_bidders": [],
      "highest_bid_amount": 0,
      "last_updated": 1647891234567,
      "bin": true,
      "bids": [],
      "item_uuid": "string"
    }
  ]
}
```

#### Get Ended Auctions
**Endpoint**: `https://api.hypixel.net/v2/skyblock/auctions_ended`

**Method**: GET

**Response Structure**:
```json
{
  "success": true,
  "lastUpdated": 1647891234567,
  "auctions": [
    {
      "auction_id": "string",
      "seller": "string",
      "seller_profile": "string",
      "buyer": "string", 
      "timestamp": 1647891234567,
      "price": 1000,
      "bin": true,
      "item_bytes": "base64_encoded_nbt_data"
    }
  ]
}
```

### External Price Data APIs

#### SkyHelper Prices
**Endpoint**: `https://raw.githubusercontent.com/SkyHelperBot/Prices/main/prices.json`

**Method**: GET

**Response**: JSON object with item prices
```json
{
  "ITEM_ID": {
    "price": 1000,
    "sellPrice": 800
  }
}
```

#### Moulberry Lowest BIN
**Endpoint**: `https://moulberry.codes/lowestbin.json`

**Method**: GET

**Response**: JSON object with lowest BIN prices
```json
{
  "ITEM_ID": 1000
}
```

#### Daily Sales Averages
**Endpoint**: `https://moulberry.codes/auction_averages/3day.json`

**Method**: GET

**Response**: JSON object with 3-day sales averages
```json
{
  "ITEM_ID": {
    "price": 1000,
    "sales": 50,
    "clean_price": 950
  }
}
```

---

## Internal Python APIs

### AuctionHandler Module

#### `process_auction(auction: dict) -> bool | None`

Processes a single auction item for potential flips.

**Parameters**:
- `auction`: Auction data object from Hypixel API

**Returns**:
- `True`: If auction was processed and stored
- `None`: If auction was skipped (not BIN or already claimed)

**Behavior**:
- Filters for BIN auctions that are unclaimed
- Extracts relevant auction data
- Calls ItemValueHandler for valuation
- Updates progress tracking

#### `async fetch(session: aiohttp.ClientSession, url: str) -> str`

Asynchronous HTTP fetch wrapper.

**Parameters**:
- `session`: aiohttp client session
- `url`: Target URL to fetch

**Returns**: Response text as string

#### `async process_page(page: int) -> None`

Processes a single page of auction data.

**Parameters**:
- `page`: Page number to process

**Behavior**:
- Fetches auction data for specified page
- Filters out existing auctions from database
- Processes auctions in parallel using ThreadPoolExecutor
- Bulk inserts results to database

#### `async CheckAuctions(total_pages: int) -> bool`

Main function to check all auction pages.

**Parameters**:
- `total_pages`: Number of pages to process

**Returns**: `True` when complete

**Behavior**:
- Creates progress bar for total auctions
- Processes pages in parallel
- Handles cleanup and progress updates

#### `delete_ended_auctions() -> bool`

Removes ended auctions from database.

**Returns**: `True` when complete

**Behavior**:
- Fetches ended auctions from Hypixel API
- Removes matching auctions from local database
- Reports deletion count

### ItemValueHandler Module

#### `decode_data(string: str) -> dict | None`

Decodes base64 NBT data to Python dictionary.

**Parameters**:
- `string`: Base64 encoded NBT data

**Returns**:
- `dict`: Decoded NBT data
- `None`: If decoding fails

**Error Handling**: Logs errors and handles PartialReadError

#### `get_item_networth(itemstats: dict) -> bool`

Evaluates item net worth and determines if it's a profitable flip.

**Parameters**:
- `itemstats`: Complete auction data object

**Returns**: `True` when processing complete

**Behavior**:
1. Decodes item NBT data
2. Combines item data with price information
3. Calls Node.js evaluator via subprocess
4. Parses net worth result
5. Calculates profit margins
6. Stores profitable flips in database

**Data Passed to Node.js**:
```json
{
  "item": "nbt_decoded_item_data",
  "prices": "cached_price_data",
  "itemstats": "original_auction_data"
}
```

### DataBaseHandler Module

#### `InsertAuction(auction: dict) -> None`

Adds auction to batch insertion queue.

**Parameters**:
- `auction`: Processed auction data

**Behavior**: Appends to global `AuctionInsertion` list

#### `bulk_insert_auctions() -> None`

Performs bulk insertion of queued auctions.

**Behavior**:
- Inserts all queued auctions to MongoDB
- Clears the insertion queue
- Reports insertion count

**Database**: Inserts to `skyblock.Auctions` collection

### PriceHandler Module

#### `readprices() -> None`

Loads all cached price data from JSON files.

**Files Read**:
- `cached/prices.json`
- `cached/lowestbin.json`
- `cached/DailySales.json`

**Global Variables Updated**:
- `prices`
- `lowestbin` 
- `dailysales`

#### `getprices() -> dict`

Returns cached price data.

**Returns**: Global `prices` dictionary

### ProgressHandler Module

#### `createpbar(totalauction: int) -> None`

Creates a progress bar for auction processing.

**Parameters**:
- `totalauction`: Total number of auctions to process

#### `updatepbar(amount: int) -> None`

Updates progress bar by specified amount.

**Parameters**:
- `amount`: Number of items processed

#### `deletepbar() -> None`

Closes and cleans up the progress bar.

---

## Node.js Interfaces

### Evaluator.js

#### Input Interface (via stdin)

**Format**: JSON string with the following structure:
```json
{
  "item": {
    "id": "string",
    "Count": 1,
    "tag": {
      "ExtraAttributes": {
        "id": "ITEM_ID",
        "enchantments": {},
        "modifier": "reforge_name",
        "uuid": "string"
      },
      "display": {
        "Name": "item_name",
        "Lore": ["lore_lines"]
      }
    }
  },
  "prices": {
    "ITEM_ID": {
      "price": 1000,
      "sellPrice": 800
    }
  },
  "itemstats": {
    "uuid": "auction_uuid",
    "starting_bid": 1000,
    "item_name": "string"
  }
}
```

#### Output Interface (via stdout)

**Format**: Pipe-separated string: `networth|item_id`

**Example**: `1500000|HYPERION`

#### Error Handling

Errors are output to stderr with descriptive messages:
- MongoDB connection failures
- Item evaluation errors
- JSON parsing errors

---

## Database Schemas

### MongoDB Connection
- **Host**: `localhost:27017`
- **Database**: `skyblock`

### Collections

#### `skyblock.Auctions`

Stores processed auction data for tracking and duplicate prevention.

```javascript
{
  _id: ObjectId,
  name: String,           // Item display name
  tier: String,          // COMMON, UNCOMMON, RARE, EPIC, LEGENDARY, MYTHIC
  price: Number,         // Starting bid amount
  bin: Boolean,          // Always true (only BIN auctions stored)
  item_bytes: String,    // Base64 encoded NBT data
  uuid: String,          // Unique auction identifier
  start: Number,         // Auction start timestamp (ms)
  end: Number,          // Auction end timestamp (ms)
  seller: String        // Seller UUID (auctioneer or coop member)
}
```

**Indexes Recommended**:
- `{uuid: 1}` - Unique index for duplicate prevention
- `{end: 1}` - For efficient cleanup of ended auctions

#### `skyblock.Flips`

Stores profitable flip opportunities identified by the system.

```javascript
{
  _id: ObjectId,
  itemstats: {          // Original auction data
    uuid: String,
    starting_bid: Number,
    item_name: String,
    // ... other auction fields
  },
  profit: Number,         // Calculated profit (networth - starting_bid)
  daily_sales: {          // Daily sales data (if available)
    price: Number,
    sales: Number,
    clean_price: Number
  },
  lowest_bin: Number,     // Current lowest BIN price
  percentage: Number,     // Profit margin percentage
  targeted_price: Number  // Calculated item net worth
}
```

**Indexes Recommended**:
- `{profit: -1}` - For sorting by profitability
- `{"itemstats.uuid": 1}` - For auction lookup
- `{percentage: -1}` - For sorting by profit margin

---

## Data Flow Interfaces

### Core Processing Pipeline

#### 1. Auction Fetching
```
Hypixel API → AuctionHandler.process_page() → AuctionHandler.process_auction()
```

#### 2. Item Processing
```
process_auction() → DataBaseHandler.InsertAuction() → ItemValueHandler.get_item_networth()
```

#### 3. Valuation Pipeline
```
ItemValueHandler.decode_data() → Node.js Evaluator → MongoDB Flips Collection
```

#### 4. Price Data Flow
```
External APIs → AuctionFlipperCore.Update*() → cached/*.json → PriceHandler.readprices()
```

### Inter-Process Communication

#### Python → Node.js
- **Method**: subprocess with stdin/stdout
- **Format**: JSON via stdin
- **Response**: Pipe-separated values via stdout

#### Python → MongoDB
- **Driver**: pymongo
- **Connection**: Direct MongoDB connection
- **Operations**: Insert, find, delete

#### Node.js → MongoDB  
- **Driver**: mongodb (official)
- **Connection**: Direct MongoDB connection
- **Operations**: Insert only (for flips)

### Error Handling Patterns

#### Network Errors
- Automatic retries for API failures
- Graceful degradation when external APIs unavailable
- Logging of network issues

#### Data Processing Errors
- NBT decoding error handling with logging
- Malformed auction data filtering
- Database connection error recovery

#### System Resource Management
- Progress tracking for long-running operations
- Memory management for large auction datasets
- Proper cleanup of resources and connections

---

## Usage Examples

### Adding New Price Data Source

1. **Add fetching function to AuctionFlipperCore.py**:
```python
def UpdateNewPriceSource():
    response = requests.get('https://api.example.com/prices')
    data = response.json()
    with open('cached/newprices.json', 'w') as f:
        json.dump(data, f)
```

2. **Update PriceHandler.py**:
```python
newprices = {}

def readprices():
    global newprices
    # existing code...
    with open('cached/newprices.json', 'r') as f:
        newprices = json.load(f)
```

3. **Integrate in evaluation logic**:
```python
# In ItemValueHandler.py
data = {
    'item': item, 
    'prices': prices,
    'newprices': PriceHandler.newprices,
    'itemstats': itemstats
}
```

### Extending Database Schema

To add new fields to the flips collection:

```python
# In ItemValueHandler.py get_item_networth()
DataBaseHandler.flips.insert_one({
    'itemstats': itemstats,
    'profit': profit,
    'daily_sales': dailysales,
    'lowest_bin': lowestbin,
    'percentage': percentage,
    'targeted_price': networth,
    'new_field': new_value,  # Add new fields here
    'timestamp': time.time()  # Example: add timestamp
})
```

This documentation provides a complete reference for understanding and extending the AuctionFlipper system's APIs and interfaces.