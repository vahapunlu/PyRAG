"""
Quick test of Query Engine with new features
"""

import sys
from pathlib import Path
from loguru import logger

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.query_engine import QueryEngine


def main():
    logger.info("=" * 60)
    logger.info("🚀 PyRAG Quick Test")
    logger.info("=" * 60)
    
    # Initialize
    logger.info("\n1️⃣ Initializing Query Engine...")
    engine = QueryEngine()
    logger.success("✅ Query Engine ready!")
    
    # Check system health
    logger.info("\n2️⃣ System Health Check...")
    health = engine.get_system_health()
    logger.info(f"Overall status: {health['overall_status'].value}")
    logger.info(f"Components: {health['summary']}")
    
    # Test query
    logger.info("\n3️⃣ Testing Query...")
    query = "Bakır kablo akım taşıma kapasitesi nedir?"
    logger.info(f"Query: {query}")
    
    result = engine.query(query, return_sources=True)
    
    logger.info(f"\n💡 Response:")
    logger.info(result['response'][:200] + "..." if len(result['response']) > 200 else result['response'])
    logger.info(f"\n📚 Sources: {len(result.get('sources', []))}")
    
    # Check history
    logger.info("\n4️⃣ Query History...")
    history = engine.get_query_history(limit=5)
    logger.info(f"Total queries in history: {len(history)}")
    
    # Export test
    logger.info("\n5️⃣ Export Test...")
    try:
        md_path = engine.export_result(
            query=query,
            response=result['response'],
            sources=result.get('sources', []),
            format='markdown'
        )
        logger.success(f"✅ Markdown exported: {md_path}")
    except Exception as e:
        logger.error(f"❌ Export failed: {e}")
    
    # Error stats
    logger.info("\n6️⃣ Error Statistics...")
    error_stats = engine.get_error_statistics()
    logger.info(f"Total errors: {error_stats['total_errors']}")
    
    logger.info("\n" + "=" * 60)
    logger.success("✅ All tests completed!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
