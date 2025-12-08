"""
Test Database Optimizer

Test database maintenance and optimization
"""

from src.database_optimizer import DatabaseOptimizer, optimize_databases, get_database_stats
from loguru import logger
import json

if __name__ == "__main__":
    logger.info("🧪 Testing Database Optimizer...")
    
    optimizer = DatabaseOptimizer()
    
    # Test 1: Quick stats
    logger.info("\n" + "="*60)
    logger.info("Test 1: Quick Statistics")
    logger.info("="*60)
    
    quick_stats = get_database_stats()
    logger.info(f"Total cache entries: {quick_stats['total_cache_entries']}")
    logger.info(f"Total cache hits: {quick_stats['total_cache_hits']}")
    logger.info(f"Total feedback: {quick_stats['total_feedback']}")
    logger.info(f"Total database size: {quick_stats['total_db_size_mb']} MB")
    
    # Test 2: Detailed statistics
    logger.info("\n" + "="*60)
    logger.info("Test 2: Detailed Statistics")
    logger.info("="*60)
    
    detailed_stats = optimizer._get_statistics()
    
    for db_name, stats in detailed_stats.items():
        logger.info(f"\n📊 {db_name}:")
        for key, value in stats.items():
            logger.info(f"   {key}: {value}")
    
    # Test 3: Cache cleanup
    logger.info("\n" + "="*60)
    logger.info("Test 3: Cache Cleanup")
    logger.info("="*60)
    
    cleanup_results = optimizer._cleanup_caches()
    logger.info(f"Cleanup results: {cleanup_results}")
    
    # Test 4: SQLite optimization
    logger.info("\n" + "="*60)
    logger.info("Test 4: SQLite Optimization")
    logger.info("="*60)
    
    optimization_results = optimizer._optimize_sqlite()
    logger.info(f"Optimization results: {optimization_results}")
    
    # Test 5: Full optimization with recommendations
    logger.info("\n" + "="*60)
    logger.info("Test 5: Full Optimization")
    logger.info("="*60)
    
    full_results = optimize_databases()
    
    logger.info("\n📋 Recommendations:")
    for rec in full_results['recommendations']:
        severity_emoji = {
            'success': '✅',
            'info': 'ℹ️',
            'warning': '⚠️',
            'error': '❌'
        }.get(rec['severity'], 'ℹ️')
        
        logger.info(f"{severity_emoji} [{rec['category']}] {rec['message']}")
    
    # Save results to file
    logger.info("\n" + "="*60)
    logger.info("Saving results to optimization_report.json")
    logger.info("="*60)
    
    with open("optimization_report.json", "w", encoding='utf-8') as f:
        json.dump(full_results, f, indent=2, ensure_ascii=False)
    
    logger.success("✅ Report saved to optimization_report.json")
    
    logger.success("\n✅ All database optimizer tests completed!")
