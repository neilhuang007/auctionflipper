import logging
from pymongo import MongoClient
from pymongo.errors import OperationFailure
import time

# # Set up logging
# logging.basicConfig(level=logging.DEBUG)
# logger = logging.getLogger(__name__)

# Create a MongoDB client
print('Connecting to MongoDB...')
client = MongoClient('mongodb://localhost:27017/')
print('Connected to MongoDB.')

# Connect to the 'Skyblock' database
db = client['skyblock']

# Connect to the 'Auctions' collection
auctions = db['Auctions']

flips = db['Flips']

AuctionInsertion = []

def setup_database_indexes():
    """
    Set up all necessary database indexes for optimal performance.
    Only creates indexes if they don't already exist.
    """
    print('Setting up database indexes...')
    start_time = time.time()
    
    try:
        # Auctions collection indexes
        print('Creating auctions collection indexes...')
        
        # Primary UUID index for fast duplicate checking (most critical)
        auctions.create_index([("uuid", 1)], unique=True, background=True, name="uuid_unique")
        print('✓ UUID unique index created')
        
        # End timestamp index for efficient cleanup operations
        auctions.create_index([("end", 1)], background=True, name="end_timestamp")
        print('✓ End timestamp index created')
        
        # Tier index for filtering by rarity
        auctions.create_index([("tier", 1)], background=True, name="tier_index")
        print('✓ Tier index created')
        
        # Price index for filtering by starting bid
        auctions.create_index([("price", 1)], background=True, name="price_index")
        print('✓ Price index created')
        
        # BIN status index (since we only care about BIN auctions)
        auctions.create_index([("bin", 1)], background=True, name="bin_status")
        print('✓ BIN status index created')
        
        # Composite index for common query patterns
        auctions.create_index([("bin", 1), ("tier", 1), ("price", 1)], background=True, name="bin_tier_price_composite")
        print('✓ Composite BIN-tier-price index created')
        
        # Flips collection indexes
        print('Creating flips collection indexes...')
        
        # Profit index for sorting results (most used query)
        flips.create_index([("profit", -1)], background=True, name="profit_desc")
        print('✓ Profit descending index created')
        
        # Percentage index for profit margin filtering
        flips.create_index([("percentage", -1)], background=True, name="percentage_desc")
        print('✓ Percentage descending index created')
        
        # Auction UUID index for flip lookups
        flips.create_index([("itemstats.uuid", 1)], background=True, name="auction_uuid")
        print('✓ Auction UUID index created')
        
        # Item name index for item-specific searches
        flips.create_index([("itemstats.item_name", 1)], background=True, name="item_name")
        print('✓ Item name index created')
        
        # Tier index for flips filtering
        flips.create_index([("itemstats.tier", 1)], background=True, name="flip_tier")
        print('✓ Flip tier index created')
        
        # Targeted price index for value-based queries
        flips.create_index([("targeted_price", -1)], background=True, name="targeted_price_desc")
        print('✓ Targeted price index created')
        
        # Composite index for common flip queries
        flips.create_index([
            ("profit", -1), 
            ("itemstats.tier", 1), 
            ("percentage", -1)
        ], background=True, name="profit_tier_percentage_composite")
        print('✓ Composite profit-tier-percentage index created')
        
        # Optional: Add timestamp index if we decide to add timestamps to flips
        # flips.create_index([("timestamp", -1)], background=True, name="timestamp_desc")
        
        elapsed_time = time.time() - start_time
        print(f'✅ Database indexes setup completed in {elapsed_time:.2f} seconds')
        
        # Show index information
        print('\n📊 Index Summary:')
        print('Auctions collection indexes:')
        for index_info in auctions.list_indexes():
            print(f'  - {index_info["name"]}: {index_info.get("key", {})}')
        
        print('\nFlips collection indexes:')
        for index_info in flips.list_indexes():
            print(f'  - {index_info["name"]}: {index_info.get("key", {})}')
            
    except OperationFailure as e:
        if "already exists" in str(e):
            print('ℹ️  Some indexes already exist, skipping...')
        else:
            print(f'❌ Error creating indexes: {e}')
    except Exception as e:
        print(f'❌ Unexpected error setting up indexes: {e}')

def check_auction_exists_optimized(uuid):
    """
    Optimized function to check if auction exists using UUID index.
    Much faster than loading all auctions into memory.
    """
    return auctions.find_one({"uuid": uuid}, {"_id": 1}) is not None

def bulk_check_existing_auctions(uuids):
    """
    Efficiently check which auctions already exist using batch query.
    Returns set of existing UUIDs.
    """
    if not uuids:
        return set()
    
    existing_docs = auctions.find(
        {"uuid": {"$in": uuids}}, 
        {"uuid": 1, "_id": 0}
    )
    return {doc['uuid'] for doc in existing_docs}

def bulk_delete_auctions(uuids):
    """
    Efficiently delete multiple auctions using bulk operation.
    """
    if not uuids:
        return 0
    
    result = auctions.delete_many({"uuid": {"$in": uuids}})
    return result.deleted_count

def get_auction_stats():
    """
    Get database statistics for monitoring.
    """
    auction_count = auctions.estimated_document_count()
    flip_count = flips.estimated_document_count()
    
    # Get index usage stats (requires MongoDB 3.2+)
    try:
        auction_stats = db.command("collStats", "Auctions")
        flip_stats = db.command("collStats", "Flips")
        
        return {
            'auction_count': auction_count,
            'flip_count': flip_count,
            'auction_size_mb': auction_stats.get('size', 0) / (1024 * 1024),
            'flip_size_mb': flip_stats.get('size', 0) / (1024 * 1024),
            'auction_indexes': len(list(auctions.list_indexes())),
            'flip_indexes': len(list(flips.list_indexes()))
        }
    except Exception as e:
        return {
            'auction_count': auction_count,
            'flip_count': flip_count,
            'error': str(e)
        }

# Initialize indexes on module import
setup_database_indexes()


def bulk_insert_auctions():
    global AuctionInsertion
    if len(AuctionInsertion) == 0:
        return
    # Use Motor's insert_many method for bulk insertion
    result = auctions.insert_many(AuctionInsertion)
    print(f'Inserted {len(result.inserted_ids)} documents')
    AuctionInsertion = []


def InsertAuction(auction):
    global AuctionInsertion
    AuctionInsertion.append(auction)

