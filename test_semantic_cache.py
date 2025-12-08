"""
Test semantic cache functionality
"""

from src.semantic_cache import SemanticCache
from src.utils import setup_logger
from loguru import logger

def test_cache():
    """Test semantic cache with similar queries"""
    setup_logger("INFO")
    
    logger.info("=" * 60)
    logger.info("SEMANTIC CACHE TEST")
    logger.info("=" * 60)
    
    # Initialize cache
    cache = SemanticCache(
        cache_db_path="./cache_db/test_cache.db",
        similarity_threshold=0.92,
        ttl_seconds=3600  # 1 hour for testing
    )
    
    # Test 1: Cache a query
    logger.info("\n📝 TEST 1: Caching a query")
    query1 = "What is the current carrying capacity for 2.5mm² copper cable?"
    answer1 = "According to IS10101 Table 4.3.1, the current carrying capacity for 2.5mm² copper cable is 24A at reference conditions."
    
    cache.set(query1, answer1, sources=[{"document": "IS10101", "page": 45}])
    logger.info(f"✅ Cached: {query1}")
    
    # Test 2: Retrieve exact same query
    logger.info("\n🔍 TEST 2: Exact match")
    result = cache.get(query1)
    if result:
        logger.success(f"✅ Cache HIT! Similarity: {result['similarity']:.3f}")
        logger.info(f"   Answer: {result['answer'][:80]}...")
    else:
        logger.error("❌ Cache MISS (unexpected!)")
    
    # Test 3: Similar query (fuzzy match)
    logger.info("\n🔍 TEST 3: Similar query (fuzzy match)")
    query2 = "2.5mm² cable amperage capacity?"
    result = cache.get(query2)
    if result:
        logger.success(f"✅ Cache HIT! Similarity: {result['similarity']:.3f}")
        logger.info(f"   Matched with: {result['query']}")
        logger.info(f"   Answer: {result['answer'][:80]}...")
    else:
        logger.warning(f"❌ Cache MISS - Similarity below threshold")
    
    # Test 4: Very different query
    logger.info("\n🔍 TEST 4: Different query")
    query3 = "What is the grounding resistance requirement?"
    result = cache.get(query3)
    if result:
        logger.warning(f"⚠️ Unexpected cache HIT! Similarity: {result['similarity']:.3f}")
    else:
        logger.success("✅ Cache MISS (as expected)")
    
    # Test 5: Cache multiple queries
    logger.info("\n📝 TEST 5: Caching multiple queries")
    queries = [
        ("What is the voltage drop for 50m cable run?", "Voltage drop is 2.5% per IS10101 Section 6.2"),
        ("Temperature correction factor for 40°C?", "The correction factor is 0.94 according to Table 5.2.1"),
        ("Fire alarm cable requirements?", "Fire alarm cables must be fire-resistant per BS7671"),
    ]
    
    for q, a in queries:
        cache.set(q, a)
        logger.info(f"✅ Cached: {q[:50]}...")
    
    # Test 6: Statistics
    logger.info("\n📊 TEST 6: Cache statistics")
    stats = cache.get_stats()
    logger.info(f"Total entries: {stats['total_entries']}")
    logger.info(f"Total queries: {stats['total_queries']}")
    logger.info(f"Cache hits: {stats['cache_hits']}")
    logger.info(f"Cache misses: {stats['cache_misses']}")
    logger.info(f"Hit rate: {stats['hit_rate_percent']:.1f}%")
    
    # Test 7: Test similar query variations
    logger.info("\n🔍 TEST 7: Query variations")
    test_variations = [
        "current capacity 2.5mm² copper",
        "2.5mm cable current rating",
        "how much current can 2.5mm² cable carry",
    ]
    
    for variation in test_variations:
        result = cache.get(variation)
        if result:
            logger.success(f"✅ HIT ({result['similarity']:.3f}): {variation}")
        else:
            logger.info(f"❌ MISS: {variation}")
    
    logger.info("\n" + "=" * 60)
    logger.info("TEST COMPLETE")
    logger.info("=" * 60)


if __name__ == "__main__":
    test_cache()
