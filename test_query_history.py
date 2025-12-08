"""
Test Query History functionality
"""

import sys
import time
from pathlib import Path
from loguru import logger

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.query_history import QueryHistory


def test_query_history():
    """Test query history manager"""
    logger.info("=" * 60)
    logger.info("Testing Query History")
    logger.info("=" * 60)
    
    # Initialize
    history = QueryHistory("history_db/test_query_history.db")
    
    # Clear existing data
    history.clear_all()
    logger.info("✅ History cleared")
    
    # Test 1: Add queries
    logger.info("\n📝 Test 1: Adding queries...")
    test_queries = [
        {
            'query': 'Bakır kablo akım taşıma kapasitesi nedir?',
            'response': '2.5mm² bakır kablo için 25A akım taşıma kapasitesidir.',
            'sources': [
                {'content': 'Tablo 4.1: Akım değerleri...', 'metadata': {'document_name': 'IS10101', 'page': 45}}
            ],
            'duration': 1.5
        },
        {
            'query': 'Topraklama direnci ne olmalıdır?',
            'response': 'Topraklama direnci 5 ohm\'un altında olmalıdır.',
            'sources': [
                {'content': 'Madde 7.2: Topraklama...', 'metadata': {'document_name': 'IS10101', 'page': 82}}
            ],
            'duration': 1.2
        },
        {
            'query': 'PVC kablo sıcaklık düzeltme faktörü nasıl hesaplanır?',
            'response': 'Ortam sıcaklığına göre Tablo 4.5\'ten düzeltme faktörü seçilir.',
            'sources': [
                {'content': 'Tablo 4.5: Sıcaklık faktörleri...', 'metadata': {'document_name': 'IS10101', 'page': 52}}
            ],
            'duration': 1.8
        }
    ]
    
    for test_query in test_queries:
        history.add_query(
            query=test_query['query'],
            response=test_query['response'],
            sources=test_query['sources'],
            duration=test_query['duration']
        )
        time.sleep(0.1)  # Small delay for timestamp differences
    
    logger.success(f"✅ Added {len(test_queries)} queries")
    
    # Test 2: Get recent queries
    logger.info("\n📋 Test 2: Getting recent queries...")
    recent = history.get_recent(limit=10)
    logger.info(f"Found {len(recent)} recent queries:")
    for item in recent[:3]:
        logger.info(f"  - [{item['id']}] {item['query'][:50]}... ({item['duration']:.2f}s)")
    
    # Test 3: Search history
    logger.info("\n🔍 Test 3: Searching history...")
    search_results = history.search('topraklama')
    logger.info(f"Found {len(search_results)} results for 'topraklama':")
    for item in search_results:
        logger.info(f"  - [{item['id']}] {item['query']}")
    
    # Test 4: Get statistics
    logger.info("\n📊 Test 4: Statistics...")
    stats = history.get_statistics()
    logger.info(f"Total queries: {stats['total_queries']}")
    logger.info(f"Avg duration: {stats['avg_duration']:.2f}s")
    logger.info(f"Avg sources: {stats['avg_sources']:.1f}")
    logger.info(f"First query: {stats['first_query']}")
    logger.info(f"Last query: {stats['last_query']}")
    
    # Test 5: Get by ID
    logger.info("\n🎯 Test 5: Get specific query by ID...")
    query_detail = history.get_by_id(1)
    if query_detail:
        logger.info(f"Query ID 1:")
        logger.info(f"  Query: {query_detail['query']}")
        logger.info(f"  Response: {query_detail['response'][:80]}...")
        logger.info(f"  Sources: {len(query_detail['sources'])}")
    
    logger.info("\n" + "=" * 60)
    logger.success("✅ All tests completed!")


if __name__ == "__main__":
    test_query_history()
