#!/usr/bin/env python3
"""
Enhanced Result Collector for AuctionFlipper

Provides flexible JSON output and filtering options for external applications.
Supports various output formats, sorting options, and filtering criteria.
"""

import json
import argparse
import sys
from datetime import datetime, timedelta
from pymongo import MongoClient
from typing import Dict, List, Optional, Any

class ResultCollector:
    def __init__(self, mongo_uri: str = 'mongodb://localhost:27017/'):
        """Initialize the ResultCollector with MongoDB connection."""
        self.client = MongoClient(mongo_uri)
        self.db = self.client['skyblock']
        self.flips = self.db['Flips']
        self.auctions = self.db['Auctions']

    def get_flips(self, 
                  limit: Optional[int] = None,
                  min_profit: Optional[float] = None,
                  min_percentage: Optional[float] = None,
                  max_price: Optional[float] = None,
                  item_tier: Optional[str] = None,
                  item_name: Optional[str] = None,
                  sort_by: str = 'profit',
                  sort_order: str = 'desc',
                  time_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve flips with various filtering and sorting options.
        
        Args:
            limit: Maximum number of results
            min_profit: Minimum profit amount
            min_percentage: Minimum profit percentage
            max_price: Maximum starting bid price
            item_tier: Filter by item tier (COMMON, UNCOMMON, RARE, EPIC, LEGENDARY, MYTHIC)
            item_name: Filter by item name (partial match)
            sort_by: Field to sort by (profit, percentage, targeted_price, etc.)
            sort_order: Sort order ('asc' or 'desc')
            time_filter: Time filter ('1h', '6h', '24h', '7d')
        
        Returns:
            List of flip documents
        """
        # Build query filters
        query = {}
        
        if min_profit is not None:
            query['profit'] = {'$gte': min_profit}
            
        if min_percentage is not None:
            query['percentage'] = {'$gte': min_percentage}
            
        if max_price is not None:
            query['itemstats.starting_bid'] = {'$lte': max_price}
            
        if item_tier:
            query['itemstats.tier'] = item_tier.upper()
            
        if item_name:
            query['itemstats.item_name'] = {'$regex': item_name, '$options': 'i'}
            
        # Time filtering (if timestamp field exists)
        if time_filter:
            time_map = {
                '1h': timedelta(hours=1),
                '6h': timedelta(hours=6),
                '24h': timedelta(days=1),
                '7d': timedelta(days=7)
            }
            if time_filter in time_map:
                cutoff_time = datetime.now() - time_map[time_filter]
                query['timestamp'] = {'$gte': cutoff_time.timestamp() * 1000}
        
        # Sorting
        sort_direction = -1 if sort_order.lower() == 'desc' else 1
        
        # Execute query
        cursor = self.flips.find(query).sort(sort_by, sort_direction)
        
        if limit:
            cursor = cursor.limit(limit)
            
        return list(cursor)

    def get_auction_stats(self) -> Dict[str, Any]:
        """Get statistics about the auction database."""
        total_auctions = self.auctions.count_documents({})
        total_flips = self.flips.count_documents({})
        
        # Get profit statistics
        pipeline = [
            {
                '$group': {
                    '_id': None,
                    'total_profit': {'$sum': '$profit'},
                    'avg_profit': {'$avg': '$profit'},
                    'max_profit': {'$max': '$profit'},
                    'min_profit': {'$min': '$profit'},
                    'avg_percentage': {'$avg': '$percentage'},
                    'max_percentage': {'$max': '$percentage'}
                }
            }
        ]
        
        profit_stats = list(self.flips.aggregate(pipeline))
        stats = profit_stats[0] if profit_stats else {}
        
        # Get tier distribution
        tier_pipeline = [
            {
                '$group': {
                    '_id': '$itemstats.tier',
                    'count': {'$sum': 1},
                    'total_profit': {'$sum': '$profit'}
                }
            },
            {'$sort': {'total_profit': -1}}
        ]
        
        tier_stats = list(self.flips.aggregate(tier_pipeline))
        
        return {
            'total_auctions': total_auctions,
            'total_flips': total_flips,
            'flip_rate': (total_flips / total_auctions * 100) if total_auctions > 0 else 0,
            'profit_statistics': {
                'total_profit': stats.get('total_profit', 0),
                'average_profit': stats.get('avg_profit', 0),
                'maximum_profit': stats.get('max_profit', 0),
                'minimum_profit': stats.get('min_profit', 0),
                'average_percentage': stats.get('avg_percentage', 0),
                'maximum_percentage': stats.get('max_percentage', 0)
            },
            'tier_distribution': tier_stats
        }

    def get_top_items(self, limit: int = 10) -> Dict[str, Any]:
        """Get top performing items by various metrics."""
        # Most profitable items
        profit_pipeline = [
            {
                '$group': {
                    '_id': '$itemstats.item_name',
                    'total_profit': {'$sum': '$profit'},
                    'count': {'$sum': 1},
                    'avg_profit': {'$avg': '$profit'},
                    'max_profit': {'$max': '$profit'}
                }
            },
            {'$sort': {'total_profit': -1}},
            {'$limit': limit}
        ]
        
        # Most frequent items
        frequency_pipeline = [
            {
                '$group': {
                    '_id': '$itemstats.item_name',
                    'count': {'$sum': 1},
                    'total_profit': {'$sum': '$profit'},
                    'avg_profit': {'$avg': '$profit'}
                }
            },
            {'$sort': {'count': -1}},
            {'$limit': limit}
        ]
        
        # Highest percentage items
        percentage_pipeline = [
            {
                '$group': {
                    '_id': '$itemstats.item_name',
                    'avg_percentage': {'$avg': '$percentage'},
                    'max_percentage': {'$max': '$percentage'},
                    'count': {'$sum': 1},
                    'total_profit': {'$sum': '$profit'}
                }
            },
            {'$sort': {'avg_percentage': -1}},
            {'$limit': limit}
        ]
        
        return {
            'most_profitable': list(self.flips.aggregate(profit_pipeline)),
            'most_frequent': list(self.flips.aggregate(frequency_pipeline)),
            'highest_percentage': list(self.flips.aggregate(percentage_pipeline))
        }

    def export_detailed_results(self, **kwargs) -> Dict[str, Any]:
        """Export comprehensive results with metadata."""
        flips = self.get_flips(**kwargs)
        stats = self.get_auction_stats()
        top_items = self.get_top_items()
        
        # Convert ObjectId to string for JSON serialization
        for flip in flips:
            if '_id' in flip:
                flip['_id'] = str(flip['_id'])
        
        return {
            'metadata': {
                'export_timestamp': datetime.now().isoformat(),
                'total_results': len(flips),
                'filters_applied': {k: v for k, v in kwargs.items() if v is not None},
                'database_stats': stats
            },
            'flips': flips,
            'analytics': {
                'top_items': top_items,
                'summary': {
                    'total_profit_in_results': sum(flip.get('profit', 0) for flip in flips),
                    'average_profit_in_results': sum(flip.get('profit', 0) for flip in flips) / len(flips) if flips else 0,
                    'average_percentage_in_results': sum(flip.get('percentage', 0) for flip in flips) / len(flips) if flips else 0
                }
            }
        }

    def export_simple_format(self, **kwargs) -> List[Dict[str, Any]]:
        """Export simple format for basic consumption."""
        flips = self.get_flips(**kwargs)
        
        simple_flips = []
        for flip in flips:
            itemstats = flip.get('itemstats', {})
            simple_flips.append({
                'auction_id': itemstats.get('uuid', ''),
                'item_name': itemstats.get('item_name', ''),
                'tier': itemstats.get('tier', ''),
                'starting_bid': itemstats.get('starting_bid', 0),
                'estimated_value': flip.get('targeted_price', 0),
                'profit': flip.get('profit', 0),
                'profit_percentage': flip.get('percentage', 0),
                'lowest_bin': flip.get('lowest_bin'),
                'daily_sales': flip.get('daily_sales'),
                'auction_end': itemstats.get('end', 0),
                'seller': itemstats.get('seller', '')
            })
        
        return simple_flips

def main():
    parser = argparse.ArgumentParser(description='AuctionFlipper Result Collector')
    
    # Output options
    parser.add_argument('--format', choices=['simple', 'detailed', 'legacy'], 
                       default='detailed', help='Output format')
    parser.add_argument('--output', '-o', help='Output file (default: stdout)')
    parser.add_argument('--pretty', action='store_true', 
                       help='Pretty print JSON output')
    
    # Filtering options
    parser.add_argument('--limit', '-l', type=int, 
                       help='Maximum number of results')
    parser.add_argument('--min-profit', type=float, 
                       help='Minimum profit amount')
    parser.add_argument('--min-percentage', type=float, 
                       help='Minimum profit percentage')
    parser.add_argument('--max-price', type=float, 
                       help='Maximum starting bid price')
    parser.add_argument('--tier', choices=['COMMON', 'UNCOMMON', 'RARE', 'EPIC', 'LEGENDARY', 'MYTHIC'],
                       help='Filter by item tier')
    parser.add_argument('--item-name', help='Filter by item name (partial match)')
    parser.add_argument('--time-filter', choices=['1h', '6h', '24h', '7d'],
                       help='Filter by time period')
    
    # Sorting options
    parser.add_argument('--sort-by', default='profit',
                       choices=['profit', 'percentage', 'targeted_price', 'itemstats.starting_bid'],
                       help='Field to sort by')
    parser.add_argument('--sort-order', choices=['asc', 'desc'], default='desc',
                       help='Sort order')
    
    # Database options
    parser.add_argument('--mongo-uri', default='mongodb://localhost:27017/',
                       help='MongoDB connection URI')
    
    args = parser.parse_args()
    
    try:
        collector = ResultCollector(args.mongo_uri)
        
        # Prepare filter arguments
        filter_args = {
            'limit': args.limit,
            'min_profit': args.min_profit,
            'min_percentage': args.min_percentage,
            'max_price': args.max_price,
            'item_tier': args.tier,
            'item_name': args.item_name,
            'sort_by': args.sort_by,
            'sort_order': args.sort_order,
            'time_filter': args.time_filter
        }
        
        # Remove None values
        filter_args = {k: v for k, v in filter_args.items() if v is not None}
        
        # Generate output based on format
        if args.format == 'legacy':
            # Legacy format (original behavior)
            flips = collector.get_flips(**filter_args)
            for flip in flips:
                itemstats = flip.get('itemstats', {})
                print(f"{itemstats.get('uuid', 'N/A')} {flip.get('profit', 0)}")
            return
        elif args.format == 'simple':
            output = collector.export_simple_format(**filter_args)
        else:  # detailed
            output = collector.export_detailed_results(**filter_args)
        
        # Format JSON output
        json_output = json.dumps(output, indent=2 if args.pretty else None, default=str)
        
        # Write to file or stdout
        if args.output:
            with open(args.output, 'w') as f:
                f.write(json_output)
            print(f"Results exported to {args.output}", file=sys.stderr)
        else:
            print(json_output)
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()