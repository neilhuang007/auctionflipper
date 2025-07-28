#!/usr/bin/env python3
"""
Database Setup and Management Utility for AuctionFlipper

This script allows you to manage database indexes and perform maintenance tasks.
"""

import argparse
import sys
import time
from Handlers import DataBaseHandler

def show_database_stats():
    """Display current database statistics."""
    print("📊 Database Statistics")
    print("=" * 50)
    
    stats = DataBaseHandler.get_auction_stats()
    
    print(f"Auction count: {stats.get('auction_count', 'N/A'):,}")
    print(f"Flip count: {stats.get('flip_count', 'N/A'):,}")
    print(f"Auction collection size: {stats.get('auction_size_mb', 0):.2f} MB")
    print(f"Flip collection size: {stats.get('flip_size_mb', 0):.2f} MB")
    print(f"Auction indexes: {stats.get('auction_indexes', 'N/A')}")
    print(f"Flip indexes: {stats.get('flip_indexes', 'N/A')}")
    
    if 'error' in stats:
        print(f"⚠️  Error getting stats: {stats['error']}")

def list_indexes():
    """List all current database indexes."""
    print("📋 Current Database Indexes")
    print("=" * 50)
    
    print("\n🏛️  Auctions Collection:")
    for index_info in DataBaseHandler.auctions.list_indexes():
        index_name = index_info.get("name", "unknown")
        index_keys = index_info.get("key", {})
        unique = index_info.get("unique", False)
        background = index_info.get("background", False)
        
        print(f"  • {index_name}")
        print(f"    Keys: {dict(index_keys)}")
        if unique:
            print("    Type: UNIQUE")
        if background:
            print("    Built in background: Yes")
        print()
    
    print("💰 Flips Collection:")
    for index_info in DataBaseHandler.flips.list_indexes():
        index_name = index_info.get("name", "unknown")
        index_keys = index_info.get("key", {})
        unique = index_info.get("unique", False)
        background = index_info.get("background", False)
        
        print(f"  • {index_name}")
        print(f"    Keys: {dict(index_keys)}")
        if unique:
            print("    Type: UNIQUE")
        if background:
            print("    Built in background: Yes")
        print()

def rebuild_indexes():
    """Force rebuild all indexes."""
    print("🔄 Rebuilding Database Indexes")
    print("=" * 50)
    print("⚠️  This will recreate all indexes and may take some time...")
    
    response = input("Are you sure you want to continue? (y/N): ")
    if response.lower() != 'y':
        print("❌ Operation cancelled.")
        return
    
    try:
        # Drop existing indexes (except _id)
        print("Dropping existing indexes...")
        
        auction_indexes = list(DataBaseHandler.auctions.list_indexes())
        for index in auction_indexes:
            if index['name'] != '_id_':
                print(f"  Dropping auction index: {index['name']}")
                DataBaseHandler.auctions.drop_index(index['name'])
        
        flip_indexes = list(DataBaseHandler.flips.list_indexes())
        for index in flip_indexes:
            if index['name'] != '_id_':
                print(f"  Dropping flip index: {index['name']}")
                DataBaseHandler.flips.drop_index(index['name'])
        
        print("✅ Old indexes dropped.")
        
        # Recreate indexes
        print("Creating new indexes...")
        DataBaseHandler.setup_database_indexes()
        
    except Exception as e:
        print(f"❌ Error rebuilding indexes: {e}")

def test_performance():
    """Test database query performance."""
    print("⚡ Database Performance Test")
    print("=" * 50)
    
    # Test UUID lookup performance
    print("Testing UUID lookup performance...")
    
    # Get a sample UUID
    sample_doc = DataBaseHandler.auctions.find_one({}, {"uuid": 1})
    if not sample_doc:
        print("❌ No auctions found in database for testing.")
        return
    
    test_uuid = sample_doc['uuid']
    
    # Test optimized function
    start_time = time.perf_counter()
    exists = DataBaseHandler.check_auction_exists_optimized(test_uuid)
    optimized_time = time.perf_counter() - start_time
    
    print(f"✅ Optimized UUID lookup: {optimized_time*1000:.2f}ms (result: {exists})")
    
    # Test batch lookup
    test_uuids = [test_uuid] * 100  # Test with 100 UUIDs
    start_time = time.perf_counter()
    existing_uuids = DataBaseHandler.bulk_check_existing_auctions(test_uuids)
    batch_time = time.perf_counter() - start_time
    
    print(f"✅ Batch UUID lookup (100 UUIDs): {batch_time*1000:.2f}ms (found: {len(existing_uuids)})")
    
    # Test flip query performance
    print("\nTesting flip query performance...")
    start_time = time.perf_counter()
    top_flips = list(DataBaseHandler.flips.find().sort("profit", -1).limit(10))
    flip_query_time = time.perf_counter() - start_time
    
    print(f"✅ Top 10 flips query: {flip_query_time*1000:.2f}ms (found: {len(top_flips)})")

def cleanup_database():
    """Clean up old or invalid database entries."""
    print("🧹 Database Cleanup")
    print("=" * 50)
    
    response = input("This will remove ended auctions. Continue? (y/N): ")
    if response.lower() != 'y':
        print("❌ Cleanup cancelled.")
        return
    
    try:
        # Find auctions that have ended (end timestamp < current time)
        current_time = int(time.time() * 1000)
        ended_auctions = list(DataBaseHandler.auctions.find(
            {"end": {"$lt": current_time}}, 
            {"uuid": 1}
        ))
        
        if ended_auctions:
            ended_uuids = [auction['uuid'] for auction in ended_auctions]
            deleted_count = DataBaseHandler.bulk_delete_auctions(ended_uuids)
            print(f"✅ Cleaned up {deleted_count} ended auctions.")
        else:
            print("✅ No ended auctions found to clean up.")
            
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")

def main():
    parser = argparse.ArgumentParser(description='AuctionFlipper Database Management')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Stats command
    subparsers.add_parser('stats', help='Show database statistics')
    
    # List indexes command
    subparsers.add_parser('indexes', help='List all database indexes')
    
    # Setup indexes command
    subparsers.add_parser('setup', help='Setup database indexes (safe, creates only if missing)')
    
    # Rebuild indexes command
    subparsers.add_parser('rebuild', help='Force rebuild all indexes')
    
    # Performance test command
    subparsers.add_parser('test', help='Test database performance')
    
    # Cleanup command
    subparsers.add_parser('cleanup', help='Clean up old database entries')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'stats':
            show_database_stats()
        elif args.command == 'indexes':
            list_indexes()
        elif args.command == 'setup':
            print("Setting up database indexes...")
            DataBaseHandler.setup_database_indexes()
        elif args.command == 'rebuild':
            rebuild_indexes()
        elif args.command == 'test':
            test_performance()
        elif args.command == 'cleanup':
            cleanup_database()
            
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()