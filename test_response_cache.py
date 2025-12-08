"""
Test Response Cache

Test complete response caching for fast repeated queries
"""

from src.response_cache import get_response_cache
from loguru import logger
import time

if __name__ == "__main__":
    logger.info("🧪 Testing Response Cache...")
    
    cache = get_response_cache()
    
    # Test 1: Cache miss
    logger.info("\n" + "="*60)
    logger.info("Test 1: Cache miss (first query)")
    logger.info("="*60)
    
    query = "EN 54-11 standardı nedir?"
    result = cache.get(query)
    
    if result is None:
        logger.success("✅ Cache miss as expected")
    else:
        logger.error("❌ Unexpected cache hit!")
    
    # Test 2: Set cache
    logger.info("\n" + "="*60)
    logger.info("Test 2: Set cache entry")
    logger.info("="*60)
    
    mock_response = {
        "response": "EN 54-11, yangın algılama sistemleri için manuel çağrı noktaları standardıdır.",
        "sources": [
            {"document": "IS3218 2024", "page": "35"}
        ],
        "metadata": {
            "question": query,
            "model": "deepseek-chat"
        }
    }
    
    cache.set(query, mock_response)
    logger.success("✅ Response cached")
    
    # Test 3: Cache hit
    logger.info("\n" + "="*60)
    logger.info("Test 3: Cache hit (same query)")
    logger.info("="*60)
    
    result = cache.get(query)
    
    if result:
        logger.success(f"✅ Cache hit!")
        logger.info(f"   Response: {result['response'][:50]}...")
        logger.info(f"   Sources: {len(result['sources'])}")
        logger.info(f"   Cache hits: {result['metadata']['cache_hits']}")
        logger.info(f"   Cache age: {result['metadata']['cache_age_seconds']:.2f}s")
    else:
        logger.error("❌ Cache miss unexpected!")
    
    # Test 4: Multiple hits
    logger.info("\n" + "="*60)
    logger.info("Test 4: Multiple cache hits")
    logger.info("="*60)
    
    for i in range(3):
        result = cache.get(query)
        if result:
            logger.info(f"   Hit #{i+2}: cache_hits={result['metadata']['cache_hits']}")
    
    # Test 5: Different query variations (should be same key)
    logger.info("\n" + "="*60)
    logger.info("Test 5: Query normalization")
    logger.info("="*60)
    
    variations = [
        "EN 54-11 STANDARDI NEDİR?",  # Uppercase
        "  en 54-11 standardı nedir?  ",  # Extra spaces
        "EN 54-11 standardı nedir?",  # Original
    ]
    
    for var in variations:
        result = cache.get(var)
        if result:
            logger.success(f"✅ '{var}' → Cache hit!")
        else:
            logger.error(f"❌ '{var}' → Cache miss!")
    
    # Test 6: Cache with filters
    logger.info("\n" + "="*60)
    logger.info("Test 6: Cache with filters")
    logger.info("="*60)
    
    query_filtered = "Yangın algılama nedir?"
    filters = {"document": "IS3218 2024"}
    
    # Set with filters
    mock_response_filtered = {
        "response": "Yangın algılama, duman veya sıcaklık tespitidir.",
        "sources": [],
        "metadata": {"question": query_filtered}
    }
    cache.set(query_filtered, mock_response_filtered, filters)
    
    # Get with same filters - should hit
    result = cache.get(query_filtered, filters)
    if result:
        logger.success("✅ Cache hit with matching filters")
    else:
        logger.error("❌ Cache miss with matching filters")
    
    # Get without filters - should miss
    result = cache.get(query_filtered, None)
    if result is None:
        logger.success("✅ Cache miss with different filters")
    else:
        logger.error("❌ Unexpected cache hit with different filters")
    
    # Test 7: Statistics
    logger.info("\n" + "="*60)
    logger.info("Test 7: Cache statistics")
    logger.info("="*60)
    
    stats = cache.get_statistics()
    logger.info(f"Total entries: {stats['total_entries']}")
    logger.info(f"Valid entries: {stats['valid_entries']}")
    logger.info(f"Expired entries: {stats['expired_entries']}")
    logger.info(f"Total hits: {stats['total_hits']}")
    logger.info(f"Hit rate: {stats['hit_rate']}%")
    
    if stats['top_queries']:
        logger.info("\nTop queries:")
        for i, q in enumerate(stats['top_queries'], 1):
            logger.info(f"  {i}. {q['query'][:50]}... (hits: {q['hits']}, age: {q['age']:.1f}m)")
    
    # Test 8: Expiration (fast test with 1 second TTL)
    logger.info("\n" + "="*60)
    logger.info("Test 8: Cache expiration (1 second TTL)")
    logger.info("="*60)
    
    from src.response_cache import ResponseCache
    short_cache = ResponseCache(db_path="cache_db/test_short_ttl.db", ttl_minutes=0.016)  # ~1 second
    
    short_cache.set("test query", {"response": "test", "sources": [], "metadata": {}})
    
    # Should hit immediately
    result = short_cache.get("test query")
    if result:
        logger.success("✅ Cache hit before expiration")
    
    # Wait 2 seconds
    logger.info("   Waiting 2 seconds...")
    time.sleep(2)
    
    # Should miss after expiration
    result = short_cache.get("test query")
    if result is None:
        logger.success("✅ Cache miss after expiration")
    else:
        logger.error("❌ Cache hit after expiration (should be expired!)")
    
    logger.success("\n✅ All response cache tests completed!")
