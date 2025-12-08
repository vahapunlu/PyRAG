"""
Test Hybrid Search (Phase 4)
"""

from src.query_engine import QueryEngine
from loguru import logger

def test_hybrid_search():
    logger.info("="*60)
    logger.info("TESTING HYBRID SEARCH (PHASE 4)")
    logger.info("="*60)
    
    # Initialize query engine
    engine = QueryEngine(use_cache=False)  # Disable cache for testing
    
    # Test queries with different intents (IS3218 - Fire Detection & Alarm Systems)
    test_queries = [
        {
            'query': "Manual call point kaç metre aralıklarla yerleştirilmeli?",
            'expected': "TABLE_LOOKUP - Should use keyword+table search for spacing requirements"
        },
        {
            'query': "Manual call point nedir?",
            'expected': "DEFINITION - Should use semantic search for concepts"
        },
        {
            'query': "IS3218 standardına göre MCP yerleştirme kuralları nelerdir?",
            'expected': "REFERENCE - Should use keyword search for standard references"
        },
        {
            'query': "Yangın alarm sistemi bileşenleri nelerdir?",
            'expected': "GENERAL - Should use balanced semantic search"
        }
    ]
    
    for i, test in enumerate(test_queries, 1):
        print(f"\n{'='*60}")
        print(f"TEST {i}/{len(test_queries)}")
        print(f"Query: {test['query']}")
        print(f"Expected: {test['expected']}")
        print('='*60)
        
        try:
            result = engine.query(test['query'])
            
            print(f"\n📝 ANSWER:")
            print(result['response'])
            
            print(f"\n📚 SOURCES ({len(result['sources'])}):")
            for j, source in enumerate(result['sources'][:3], 1):
                print(f"{j}. {source.get('file_name', 'Unknown')} (Page {source.get('page_label', '?')})")
            
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_hybrid_search()
