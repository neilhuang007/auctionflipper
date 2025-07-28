"""
Optimized Item Value Handler with Persistent Service Integration

This replaces the subprocess-based evaluation with HTTP service calls
Expected performance improvement: 85-90% reduction in evaluation time
"""

import base64
import nbtlib
import logging
import json
import aiohttp
import asyncio
from io import BytesIO
from typing import Dict, Any, Optional, List
import time

from Handlers import PriceHandler, DataBaseHandler
from ConfigHandler import get_evaluation_service_config, get_performance_config

# Global aiohttp session for connection reuse
_http_session: Optional[aiohttp.ClientSession] = None

# Performance tracking
evaluation_stats = {
    'total_evaluations': 0,
    'total_time': 0,
    'cache_hits': 0,
    'profitable_found': 0
}

# Simple cache for recently evaluated items (avoid re-evaluating same item)
_evaluation_cache = {}

def get_service_url():
    """Get evaluation service URL from configuration."""
    service_config = get_evaluation_service_config()
    return service_config.get("url", "http://localhost:3000")

def get_cache_ttl():
    """Get cache TTL from configuration."""
    perf_config = get_performance_config()
    return perf_config.get("cache_ttl_seconds", 300)

async def get_http_session():
    """Get or create the global HTTP session."""
    global _http_session
    if _http_session is None or _http_session.closed:
        connector = aiohttp.TCPConnector(
            limit=100,  # Total connection pool size
            limit_per_host=20,  # Connections per host
            keepalive_timeout=60,
            enable_cleanup_closed=True
        )
        timeout = aiohttp.ClientTimeout(total=10, connect=2)
        _http_session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'Content-Type': 'application/json'}
        )
    return _http_session

async def close_http_session():
    """Close the global HTTP session."""
    global _http_session
    if _http_session and not _http_session.closed:
        await _http_session.close()
        _http_session = None

def decode_data_optimized(string: str) -> Optional[Dict]:
    """
    Optimized NBT data decoding with error handling and JSON serialization support.
    """
    try:
        # Decode the base64 string
        data = base64.b64decode(string)
        # Parse the NBT data
        nbt_file = nbtlib.File.load(BytesIO(data), gzipped=True)
        # Convert the NBT file to a dictionary and handle non-serializable types
        return convert_nbt_to_serializable(dict(nbt_file))
    except Exception as error:
        logging.error(f"Error decoding NBT data: {error}")
        return None

def convert_nbt_to_serializable(obj):
    """
    Convert NBT objects to JSON-serializable types.
    """
    if hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes)):
        if isinstance(obj, dict):
            return {k: convert_nbt_to_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_nbt_to_serializable(item) for item in obj]
        else:
            # Handle other iterables
            return [convert_nbt_to_serializable(item) for item in obj]
    elif hasattr(obj, '__dict__'):
        # Handle objects with attributes
        return {k: convert_nbt_to_serializable(v) for k, v in obj.__dict__.items()}
    elif isinstance(obj, (bytes, bytearray)):
        # Convert bytes to list of integers or base64 string
        return list(obj) if len(obj) < 100 else base64.b64encode(obj).decode('utf-8')
    else:
        # Return primitive types as-is
        return obj

def get_cache_key(item_bytes: str) -> str:
    """Generate cache key for item evaluation."""
    import hashlib
    return hashlib.md5(item_bytes.encode()).hexdigest()

async def evaluate_item_async(item_data: Dict, prices: Dict, itemstats: Dict) -> Optional[Dict]:
    """
    Asynchronously evaluate a single item using the persistent service.
    """
    session = await get_http_session()
    
    try:
        evaluation_stats['total_evaluations'] += 1
        start_time = time.perf_counter()
        
        # Check cache first
        cache_key = get_cache_key(itemstats.get('item_bytes', ''))
        current_time = time.time()
        
        if cache_key in _evaluation_cache:
            cached_result, cache_time = _evaluation_cache[cache_key]
            cache_ttl = get_cache_ttl()
            if current_time - cache_time < cache_ttl:
                evaluation_stats['cache_hits'] += 1
                return cached_result
        
        payload = {
            'item': item_data,
            'prices': prices,
            'itemstats': itemstats
        }
        
        service_url = get_service_url()
        async with session.post(f"{service_url}/evaluate", json=payload) as response:
            if response.status == 200:
                result = await response.json()
                
                # Cache the result
                _evaluation_cache[cache_key] = (result, current_time)
                
                # Clean old cache entries periodically
                if len(_evaluation_cache) > 1000:
                    cleanup_cache()
                
                elapsed_time = time.perf_counter() - start_time
                evaluation_stats['total_time'] += elapsed_time
                
                if result.get('isProfitable', False):
                    evaluation_stats['profitable_found'] += 1
                
                return result
            else:
                error_text = await response.text()
                logging.error(f"Evaluation service error {response.status}: {error_text}")
                return None
                
    except asyncio.TimeoutError:
        logging.error("Evaluation service timeout")
        return None
    except Exception as e:
        logging.error(f"Error calling evaluation service: {e}")
        return None

async def evaluate_items_batch(items_data: List[Dict]) -> List[Dict]:
    """
    Evaluate multiple items in a single batch request for maximum performance.
    """
    session = await get_http_session()
    
    try:
        start_time = time.perf_counter()
        
        # Ensure all items_data is JSON serializable
        serializable_items = []
        for item in items_data:
            try:
                # Test serialization
                json.dumps(item)
                serializable_items.append(item)
            except (TypeError, ValueError) as e:
                logging.warning(f"Skipping non-serializable item: {e}")
                continue
        
        if not serializable_items:
            logging.warning("No serializable items in batch")
            return []
        
        payload = {
            'items': serializable_items,
            'prices': PriceHandler.getprices()
        }
        
        service_url = get_service_url()
        async with session.post(f"{service_url}/evaluate-batch", json=payload) as response:
            if response.status == 200:
                result = await response.json()
                
                elapsed_time = time.perf_counter() - start_time
                evaluation_stats['total_evaluations'] += len(serializable_items)
                evaluation_stats['total_time'] += elapsed_time
                evaluation_stats['profitable_found'] += len(result.get('profitable', []))
                
                return result.get('results', [])
            else:
                error_text = await response.text()
                logging.error(f"Batch evaluation service error {response.status}: {error_text}")
                return []
                
    except Exception as e:
        logging.error(f"Error calling batch evaluation service: {e}")
        return []

def cleanup_cache():
    """Clean up old cache entries."""
    global _evaluation_cache
    current_time = time.time()
    cache_ttl = get_cache_ttl()
    _evaluation_cache = {
        k: v for k, v in _evaluation_cache.items() 
        if current_time - v[1] < cache_ttl
    }

async def get_item_networth_async(itemstats: Dict) -> bool:
    """
    Asynchronously evaluate item net worth and store profitable flips.
    This is the main replacement for the synchronous subprocess version.
    """
    try:
        # Decode NBT data
        item_data = decode_data_optimized(itemstats.get('item_bytes'))
        if not item_data or 'i' not in item_data or not item_data['i']:
            return False
        
        # Extract the first item from the 'i' property
        item = item_data['i'][0]
        
        # Get cached price data
        prices = PriceHandler.getprices()
        
        # Evaluate the item
        evaluation_result = await evaluate_item_async(item, prices, itemstats)
        
        if not evaluation_result or not evaluation_result.get('success', False):
            return False
        
        if evaluation_result.get('isProfitable', False):
            # Get additional market data
            item_id = evaluation_result['itemId']
            lowestbin = PriceHandler.lowestbin.get(item_id)
            dailysales = PriceHandler.dailysales.get(item_id)
            
            # Store the profitable flip
            flip_data = {
                'itemstats': itemstats,
                'profit': evaluation_result['profit'],
                'daily_sales': dailysales,
                'lowest_bin': lowestbin,
                'percentage': evaluation_result['percentage'],
                'targeted_price': evaluation_result['estimatedValue'],
                'timestamp': int(time.time() * 1000)
            }
            
            try:
                DataBaseHandler.flips.insert_one(flip_data)
                return True
            except Exception as e:
                logging.error(f"Error inserting flip to database: {e}")
                return False
        
        return True
        
    except Exception as e:
        logging.error(f"Error in async item evaluation: {e}")
        return False

# Batch processing function for maximum efficiency
async def process_auctions_batch(auctions: List[Dict]) -> int:
    """
    Process multiple auctions in batch for maximum performance.
    Returns the number of profitable flips found.
    """
    if not auctions:
        return 0
    
    logging.info(f"Processing batch of {len(auctions)} auctions")
    
    # Prepare batch data
    items_data = []
    valid_auctions = []
    
    for auction in auctions:
        if auction.get('bin', False) and not auction.get('claimed', False):
            item_data = decode_data_optimized(auction.get('item_bytes'))
            if item_data and 'i' in item_data and item_data['i']:
                items_data.append({
                    'item': item_data['i'][0],
                    'itemstats': {
                        'uuid': auction['uuid'],
                        'item_name': auction['item_name'],
                        'tier': auction['tier'],
                        'starting_bid': auction['starting_bid'],
                        'item_bytes': auction['item_bytes'],
                        'start': auction['start'],
                        'end': auction['end'],
                        'seller': auction.get('auctioneer') or (auction.get('coop', [None])[0] if auction.get('coop') else None)
                    }
                })
                valid_auctions.append(auction)
    
    if not items_data:
        logging.info("No valid items found for evaluation")
        return 0
    
    logging.info(f"Evaluating {len(items_data)} items in batch")
    
    # Evaluate all items in batch
    evaluation_results = await evaluate_items_batch(items_data)
    
    # Process profitable flips
    profitable_count = 0
    flips_to_insert = []
    
    for i, result in enumerate(evaluation_results):
        if result.get('isProfitable', False) and i < len(valid_auctions):
            auction = valid_auctions[i]
            item_id = result['itemId']
            
            # Get market data
            lowestbin = PriceHandler.lowestbin.get(item_id)
            dailysales = PriceHandler.dailysales.get(item_id)
            
            flip_data = {
                'itemstats': items_data[i]['itemstats'],
                'profit': result['profit'],
                'daily_sales': dailysales,
                'lowest_bin': lowestbin,
                'percentage': result['percentage'],
                'targeted_price': result['estimatedValue'],
                'timestamp': int(time.time() * 1000)
            }
            
            flips_to_insert.append(flip_data)
            profitable_count += 1
    
    # Bulk insert profitable flips
    if flips_to_insert:
        try:
            DataBaseHandler.flips.insert_many(flips_to_insert)
            logging.info(f"Inserted {len(flips_to_insert)} profitable flips to database")
        except Exception as e:
            logging.error(f"Error bulk inserting flips: {e}")
    
    logging.info(f"Batch processing complete: {profitable_count} profitable flips found")
    return profitable_count

def get_evaluation_stats() -> Dict[str, Any]:
    """Get performance statistics for monitoring."""
    stats = evaluation_stats.copy()
    if stats['total_evaluations'] > 0:
        stats['avg_evaluation_time'] = stats['total_time'] / stats['total_evaluations']
        stats['cache_hit_rate'] = stats['cache_hits'] / stats['total_evaluations'] * 100
        stats['profitable_rate'] = stats['profitable_found'] / stats['total_evaluations'] * 100
    else:
        stats['avg_evaluation_time'] = 0
        stats['cache_hit_rate'] = 0
        stats['profitable_rate'] = 0
    
    stats['cache_size'] = len(_evaluation_cache)
    return stats

# Backward compatibility function (synchronous wrapper)
def get_item_networth(itemstats: Dict) -> bool:
    """
    Synchronous wrapper for backward compatibility.
    Note: This creates a new event loop - prefer async version when possible.
    """
    try:
        # Check if we're already in an event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # We're in an async context, can't use run()
            logging.warning("get_item_networth called from async context - use get_item_networth_async instead")
            return False
        else:
            return loop.run_until_complete(get_item_networth_async(itemstats))
    except RuntimeError:
        # No event loop, create one
        return asyncio.run(get_item_networth_async(itemstats))

# Cleanup function for graceful shutdown
async def cleanup():
    """Clean up resources on shutdown."""
    await close_http_session()
    global _evaluation_cache
    _evaluation_cache.clear()