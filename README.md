# AuctionFlipper

A comprehensive Hypixel Skyblock auction monitoring and profit analysis system that identifies profitable item flipping opportunities in real-time.

## 🎯 Overview

AuctionFlipper continuously monitors the Hypixel Skyblock auction house to identify underpriced items that can be purchased and resold for profit. The system combines Python for data collection and processing with Node.js for advanced item valuation using the `skyhelper-networth` library.

## ✨ Features

- **Real-time Auction Monitoring**: Continuously fetches and processes auction data from Hypixel API
- **Smart Item Valuation**: Uses skyhelper-networth for accurate item pricing including enchantments, reforges, and special attributes
- **BIN Auction Focus**: Specifically targets Buy-It-Now auctions for immediate purchase opportunities
- **Profit Analysis**: Calculates potential profit margins and identifies the most lucrative flips
- **MongoDB Storage**: Persistent storage of auction data and profitable flip opportunities
- **Progress Tracking**: Real-time progress bars for batch operations
- **Duplicate Prevention**: Prevents processing the same auction multiple times
- **Automatic Cleanup**: Removes ended auctions from the database

## 🏗️ Architecture

### Python Components

- **AuctionFlipperCore.py**: Main orchestrator that manages the continuous monitoring loop
- **AuctionHandler.py**: Fetches and processes auction data from Hypixel API
- **ItemValueHandler.py**: Decodes NBT item data and prepares it for valuation
- **DataBaseHandler.py**: Manages MongoDB operations for auctions and flips
- **PriceHandler.py**: Handles cached price data from external sources
- **ProgressHandler.py**: Provides progress tracking for batch operations

### Node.js Components

- **Evaluator.js**: Receives item data from Python and calculates net worth using skyhelper-networth

### Data Flow

1. Fetch auction data from Hypixel API
2. Filter for unclaimed BIN auctions
3. Extract and decode item NBT data
4. Pass item data to Node.js evaluator
5. Calculate item net worth and potential profit
6. Store profitable opportunities in MongoDB
7. Clean up ended auctions

## 🚀 Getting Started

### Prerequisites

- **Python 3.7+** with the following packages:
  - `aiohttp` - Async HTTP requests
  - `orjson` - Fast JSON parsing
  - `pymongo` - MongoDB client
  - `nbtlib` - NBT data parsing
  - `requests` - HTTP requests
  - `schedule` - Task scheduling
  - `tqdm` - Progress bars

- **Node.js 14+** with dependencies:
  - `express` - HTTP server framework
  - `mongodb` - MongoDB client
  - `skyhelper-networth` - Item valuation
  - `prismarine-nbt` - NBT parsing

- **MongoDB** - Local instance running on port 27017

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd auctionflipper
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Node.js dependencies**
   ```bash
   npm install
   ```

4. **Install and Setup MongoDB**
   
   Follow the official MongoDB installation guide for your operating system:
   - **Windows**: https://docs.mongodb.com/manual/tutorial/install-mongodb-on-windows/
   - **macOS**: https://docs.mongodb.com/manual/tutorial/install-mongodb-on-os-x/
   - **Linux**: https://docs.mongodb.com/manual/administration/install-on-linux/
   
   After installation, start MongoDB:
   ```bash
   # On Windows
   net start MongoDB
   
   # On macOS/Linux
   sudo systemctl start mongod
   
   # Or using MongoDB Compass (GUI)
   # Download from: https://www.mongodb.com/products/compass
   ```
   
   **Quick Setup Verification**:
   ```bash
   # Test MongoDB connection
   mongosh
   # Should connect to MongoDB shell successfully
   ```

5. **Configure API Access (Optional)**

   For improved rate limits and reliability, configure your Hypixel API key:
   
   **Option A: Environment Variable (Recommended)**
   ```bash
   # Windows
   set HYPIXEL_API_KEY=your-api-key-here
   
   # macOS/Linux
   export HYPIXEL_API_KEY=your-api-key-here
   ```
   
   **Option B: Configuration File**
   Edit `config.json` and replace `"your-hypixel-api-key-here"` with your actual API key:
   ```json
   {
     "hypixel_api_key": "your-actual-api-key"
   }
   ```
   
   > **Get a Hypixel API Key**: Visit https://developer.hypixel.net/ to obtain your free API key

6. **Run the Application**
   
   **Quick Start (Recommended - Optimized Version)**:
   ```bash
   python start_optimized.py
   ```
   
   **Alternative Methods**:
   ```bash
   # Original version
   python start_optimized.py --mode original
   
   # Service only (for development)
   python start_optimized.py --mode service-only
   
   # Performance comparison
   python start_optimized.py --mode compare
   
   # Skip database setup (if already configured)
   python start_optimized.py --skip-db-setup
   ```

## ⚙️ Configuration

### Configuration File (config.json)
The application uses `config.json` for configuration. Key settings include:

```json
{
  "hypixel_api_key": "your-hypixel-api-key-here",
  "mongodb_url": "mongodb://localhost:27017",
  "database_name": "skyblock",
  "evaluation_service": {
    "url": "http://localhost:3000",
    "timeout": 10
  },
  "performance": {
    "max_concurrent_pages": 12,
    "cache_ttl_seconds": 300,
    "connection_pool_size": 200
  }
}
```

### Environment Variables
Override any configuration using environment variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `HYPIXEL_API_KEY` | Your Hypixel API key | `abc123...` |
| `MONGODB_URL` | MongoDB connection string | `mongodb://localhost:27017` |
| `DATABASE_NAME` | Database name | `skyblock` |
| `EVALUATION_SERVICE_URL` | Evaluation service URL | `http://localhost:3000` |
| `MAX_CONCURRENT_PAGES` | Max parallel page processing | `12` |
| `CACHE_TTL_SECONDS` | Cache time-to-live | `300` |

### Performance Tuning
- **`max_concurrent_pages`**: Higher values = faster processing but more memory/CPU usage
- **`cache_ttl_seconds`**: How long to cache item evaluations (reduces API calls)
- **`connection_pool_size`**: HTTP connection pool size for API requests

## 🚀 Performance Features

### Optimized Version Benefits
- **85-95% faster** than original implementation
- **Automatic database indexing** for optimal query performance
- **Persistent evaluation service** eliminates subprocess overhead
- **Parallel page processing** with configurable concurrency
- **Intelligent caching** reduces redundant evaluations
- **Connection pooling** minimizes HTTP overhead
- **Complete re-evaluation on startup** - All existing auctions are re-evaluated with latest prices

### Database Optimization
The optimized version automatically creates these indexes:
- `uuid` (unique) - Fast auction lookups
- `end` - Efficient cleanup of expired auctions  
- `bin` - Quick filtering of Buy-It-Now auctions
- `tier, price` - Optimized auction queries
- `timestamp` - Efficient flip tracking

## 📋 Application Workflow

### Initial Launch Process
1. **Update price data** - Fetch latest prices, lowest BIN, and daily sales data
2. **Fetch new auctions** - Get all current auctions from Hypixel API
3. **Filter and store** - Save new BIN auctions to database
4. **Evaluate new auctions** - Calculate profitability for new items
5. **🔄 Re-evaluate ALL existing auctions** - Check all stored auctions with updated prices
6. **Store profitable flips** - Save all profitable opportunities to database

### Monitoring Mode Process
1. **Update prices** (every 5 cycles) - Keep price data current
2. **Scan all auction pages** - Check all pages for new auction listings
3. **Filter new auctions** - Only process auctions not already in database
4. **Evaluate new items** - Calculate profitability for newly discovered auctions
5. **Cleanup expired** - Remove ended auctions from database

> **Why scan all pages?** Hypixel auction pages are not sorted chronologically - new auctions can appear on any page, so we must check all pages to avoid missing profitable opportunities.

> **Performance note:** Even though we fetch all pages, we only **evaluate** new auctions (not in database). Most auctions are already processed, so evaluation time remains low while ensuring complete coverage.

> **Why re-evaluate everything on startup?** Price data changes frequently, so auctions that weren't profitable yesterday might be profitable today with updated market prices.

## 🔧 Troubleshooting

### Common Issues

#### Evaluation Service Won't Start
```bash
# Check if Node.js dependencies are installed
npm install

# Manually test the service
node EvaluatorService.js

# Check if port 3000 is available
netstat -ano | findstr :3000
```

#### Character Encoding Issues
If you see `'gbk' codec can't decode byte` errors:
- The startup script automatically handles encoding issues
- If problems persist, run with `--skip-db-setup` flag
- Check Windows system locale settings

#### JSON Parsing Issues
If you see `unexpected mimetype: text/plain` errors:
- The optimized version automatically handles mimetype issues
- This occurs when external APIs return JSON with incorrect Content-Type headers
- The system now falls back to manual JSON parsing when needed

#### MongoDB Connection Issues
```bash
# Verify MongoDB is running
mongosh

# Check connection in logs
python start_optimized.py --mode service-only
```

#### API Rate Limiting
- Configure your Hypixel API key for better rate limits
- Current endpoints used:
  - `https://api.hypixel.net/skyblock/auctions` (public, no key required)
  - `https://api.hypixel.net/v2/skyblock/auctions_ended` (public, no key required)
- With API key: Higher rate limits and priority access

### Performance Tips
- **Increase `max_concurrent_pages`** for faster processing (uses more CPU/memory)
- **Decrease `cache_ttl_seconds`** for more accurate but slower evaluation
- **Monitor memory usage** - reduce concurrency if system becomes unstable

## 📊 Database Schema

### MongoDB Collections

#### `skyblock.Auctions`
Stores all processed auction data:
```json
{
  "name": "String - Item name",
  "tier": "String - Item rarity tier",
  "price": "Number - Starting bid price",
  "bin": "Boolean - Buy It Now status",
  "item_bytes": "String - Base64 encoded NBT data",
  "uuid": "String - Unique auction identifier",
  "start": "Number - Auction start timestamp",
  "end": "Number - Auction end timestamp",
  "seller": "String - Seller UUID"
}
```

#### `skyblock.Flips`
Stores profitable flip opportunities:
```json
{
  "itemstats": "Object - Original auction data",
  "profit": "Number - Calculated profit amount",
  "networth": "Number - Item net worth",
  "item_id": "String - Skyblock item identifier"
}
```

## 🔧 Configuration

### External Data Sources

The system automatically caches price data from:

- **Prices**: `https://raw.githubusercontent.com/SkyHelperBot/Prices/main/prices.json`
- **Lowest BIN**: `https://moulberry.codes/lowestbin.json`
- **Daily Sales**: `https://moulberry.codes/auction_averages/3day.json`

### Performance Settings

- **Concurrent Workers**: 14 threads for auction processing
- **API Pages**: Initial scan processes all pages, then monitors first 2 pages
- **Update Interval**: 1-second delay between monitoring cycles
- **MongoDB Connection**: `mongodb://localhost:27017`

## 📈 Usage

### Starting the System

Run the main script to begin monitoring:
```bash
python AuctionFlipperCore.py
```

The system will:
1. Update all cached price data
2. Perform an initial full scan of all auctions
3. Enter continuous monitoring mode
4. Update prices and check auctions every cycle
5. Clean up ended auctions automatically

### Viewing Results

Use the `ResultCollector.py` to view profitable flips:
```bash
python ResultCollector.py
```

This displays all flips sorted by profit in descending order.

## 🔍 Monitoring and Debugging

### Progress Tracking

The system provides real-time progress bars showing:
- Total auctions being processed
- Processing speed
- Completion percentage

### Logging

Uncomment logging lines in handler files for detailed debug information:
```python
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

## ⚡ Performance Considerations

- **Memory Usage**: NBT data processing can be memory-intensive for large auction volumes
- **API Rate Limits**: Respects Hypixel API rate limits with appropriate delays
- **Database Size**: Regular cleanup prevents excessive storage growth
- **Network Bandwidth**: Continuous API requests require stable internet connection

## 🛠️ Development

### Adding New Features

1. **New Handlers**: Create in `Handlers/` directory following existing patterns
2. **Database Operations**: Extend `DataBaseHandler.py` for new collections
3. **Item Processing**: Modify `ItemValueHandler.py` for new item analysis features

### Testing

No automated tests currently exist. Manual testing involves:
1. Running with small page limits
2. Verifying database entries
3. Checking profit calculations

## 🚨 Important Notes

- **API Dependencies**: Relies on external APIs that may change or become unavailable
- **Market Volatility**: Profit calculations based on current market data
- **Resource Usage**: Continuous operation requires dedicated system resources
- **Legal Compliance**: Ensure usage complies with Hypixel Terms of Service

## 📄 License

This project is for educational and personal use. Ensure compliance with all relevant terms of service.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 Support

For issues and questions:
1. Check existing documentation
2. Review MongoDB and API connectivity
3. Verify all dependencies are installed
4. Check system resource availability