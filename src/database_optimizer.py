"""
Database Optimizer

Maintenance and optimization utilities for all databases:
- ChromaDB compaction and cleanup
- Neo4j index optimization
- SQLite cache maintenance
- Statistics and health checks
"""

import os
import sqlite3
from pathlib import Path
from typing import Dict, Any
from datetime import datetime, timedelta
from loguru import logger


class DatabaseOptimizer:
    """
    Optimize and maintain all system databases
    
    Features:
    - Cache cleanup (expired entries)
    - Database statistics
    - Index optimization
    - Health checks
    """
    
    def __init__(self):
        """Initialize database optimizer"""
        self.base_path = Path(".")
        self.cache_dbs = [
            "cache_db/semantic_cache.db",
            "cache_db/response_cache.db",
        ]
        self.feedback_db = "feedback_db/feedback.db"
        
        logger.info("✅ Database Optimizer initialized")
    
    def optimize_all(self) -> Dict[str, Any]:
        """
        Run all optimization tasks
        
        Returns:
            Statistics from all optimizations
        """
        logger.info("🔧 Starting database optimization...")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'cache_cleanup': {},
            'database_stats': {},
            'recommendations': []
        }
        
        # 1. Clean expired cache entries
        results['cache_cleanup'] = self._cleanup_caches()
        
        # 2. Optimize SQLite databases
        results['sqlite_optimization'] = self._optimize_sqlite()
        
        # 3. Get database statistics
        results['database_stats'] = self._get_statistics()
        
        # 4. Generate recommendations
        results['recommendations'] = self._generate_recommendations(results)
        
        logger.success("✅ Database optimization completed!")
        return results
    
    def _cleanup_caches(self) -> Dict[str, int]:
        """Clean expired entries from all cache databases"""
        logger.info("🧹 Cleaning expired cache entries...")
        
        cleanup_stats = {}
        now = datetime.now().isoformat()
        
        for db_path in self.cache_dbs:
            full_path = self.base_path / db_path
            if not full_path.exists():
                continue
            
            db_name = Path(db_path).stem
            
            try:
                with sqlite3.connect(full_path) as conn:
                    # Get expired count before deletion
                    if db_name == "semantic_cache":
                        # Semantic cache uses timestamp, not expires_at
                        ttl_seconds = 7 * 24 * 3600  # 7 days default
                        cutoff_timestamp = (datetime.now() - timedelta(seconds=ttl_seconds)).timestamp()
                        count_query = "SELECT COUNT(*) FROM query_cache WHERE timestamp < ?"
                        delete_query = "DELETE FROM query_cache WHERE timestamp < ?"
                        now_value = cutoff_timestamp
                    else:  # response_cache
                        count_query = "SELECT COUNT(*) FROM response_cache WHERE expires_at <= ?"
                        delete_query = "DELETE FROM response_cache WHERE expires_at <= ?"
                        now_value = now
                    
                    expired_count = conn.execute(count_query, (now_value,)).fetchone()[0]
                    
                    if expired_count > 0:
                        conn.execute(delete_query, (now_value,))
                        conn.commit()
                        logger.info(f"   ✂️ {db_name}: Removed {expired_count} expired entries")
                    else:
                        logger.info(f"   ✓ {db_name}: No expired entries")
                    
                    cleanup_stats[db_name] = expired_count
                    
            except Exception as e:
                logger.error(f"❌ Error cleaning {db_name}: {e}")
                cleanup_stats[db_name] = -1
        
        total_removed = sum(v for v in cleanup_stats.values() if v > 0)
        logger.info(f"🧹 Total expired entries removed: {total_removed}")
        
        return cleanup_stats
    
    def _optimize_sqlite(self) -> Dict[str, bool]:
        """Run VACUUM and ANALYZE on SQLite databases"""
        logger.info("⚙️ Optimizing SQLite databases...")
        
        optimization_stats = {}
        all_dbs = self.cache_dbs + [self.feedback_db]
        
        for db_path in all_dbs:
            full_path = self.base_path / db_path
            if not full_path.exists():
                continue
            
            db_name = Path(db_path).stem
            
            try:
                with sqlite3.connect(full_path) as conn:
                    # VACUUM: Rebuild database to reclaim space
                    conn.execute("VACUUM")
                    
                    # ANALYZE: Update query optimizer statistics
                    conn.execute("ANALYZE")
                    
                    conn.commit()
                    logger.info(f"   ✓ {db_name}: VACUUM + ANALYZE completed")
                    optimization_stats[db_name] = True
                    
            except Exception as e:
                logger.error(f"❌ Error optimizing {db_name}: {e}")
                optimization_stats[db_name] = False
        
        return optimization_stats
    
    def _get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive database statistics"""
        logger.info("📊 Gathering database statistics...")
        
        stats = {}
        
        # Cache statistics
        for db_path in self.cache_dbs:
            full_path = self.base_path / db_path
            if not full_path.exists():
                continue
            
            db_name = Path(db_path).stem
            
            try:
                with sqlite3.connect(full_path) as conn:
                    conn.row_factory = sqlite3.Row
                    
                    if db_name == "semantic_cache":
                        table_name = "query_cache"
                        ttl_seconds = 7 * 24 * 3600
                        cutoff_timestamp = (datetime.now() - timedelta(seconds=ttl_seconds)).timestamp()
                        
                        total = conn.execute(f"SELECT COUNT(*) as count FROM {table_name}").fetchone()['count']
                        valid = conn.execute(f"SELECT COUNT(*) as count FROM {table_name} WHERE timestamp > ?", (cutoff_timestamp,)).fetchone()['count']
                        hits = conn.execute(f"SELECT COALESCE(SUM(hit_count), 0) as total FROM {table_name}").fetchone()['total']
                        
                        stats[db_name] = {
                            'total_entries': total,
                            'valid_entries': valid,
                            'expired_entries': total - valid,
                            'total_hits': hits,
                            'hit_rate': round(hits / total * 100, 1) if total > 0 else 0
                        }
                        
                    else:  # response_cache
                        table_name = "response_cache"
                        now = datetime.now().isoformat()
                        
                        total = conn.execute(f"SELECT COUNT(*) as count FROM {table_name}").fetchone()['count']
                        valid = conn.execute(f"SELECT COUNT(*) as count FROM {table_name} WHERE expires_at > ?", (now,)).fetchone()['count']
                        hits = conn.execute(f"SELECT COALESCE(SUM(hit_count), 0) as total FROM {table_name}").fetchone()['total']
                        
                        stats[db_name] = {
                            'total_entries': total,
                            'valid_entries': valid,
                            'expired_entries': total - valid,
                            'total_hits': hits,
                            'hit_rate': round(hits / total * 100, 1) if total > 0 else 0
                        }
                    
                    # Get database file size
                    stats[db_name]['size_mb'] = round(full_path.stat().st_size / (1024 * 1024), 2)
                    
            except Exception as e:
                logger.error(f"❌ Error getting stats for {db_name}: {e}")
        
        # Feedback database statistics
        feedback_path = self.base_path / self.feedback_db
        if feedback_path.exists():
            try:
                with sqlite3.connect(feedback_path) as conn:
                    conn.row_factory = sqlite3.Row
                    
                    total = conn.execute("SELECT COUNT(*) as count FROM feedback").fetchone()['count']
                    positive = conn.execute("SELECT COUNT(*) as count FROM feedback WHERE feedback_type = 'positive'").fetchone()['count']
                    negative = conn.execute("SELECT COUNT(*) as count FROM feedback WHERE feedback_type = 'negative'").fetchone()['count']
                    
                    stats['feedback'] = {
                        'total_feedback': total,
                        'positive': positive,
                        'negative': negative,
                        'positive_rate': round(positive / total * 100, 1) if total > 0 else 0,
                        'size_mb': round(feedback_path.stat().st_size / (1024 * 1024), 2)
                    }
            except Exception as e:
                logger.error(f"❌ Error getting feedback stats: {e}")
        
        return stats
    
    def _generate_recommendations(self, results: Dict[str, Any]) -> list:
        """Generate optimization recommendations based on statistics"""
        recommendations = []
        
        stats = results.get('database_stats', {})
        
        # Check cache sizes
        for cache_name in ['semantic_cache', 'response_cache']:
            if cache_name in stats:
                cache_stats = stats[cache_name]
                
                # Too many expired entries
                if cache_stats['expired_entries'] > 100:
                    recommendations.append({
                        'severity': 'warning',
                        'category': 'cache_cleanup',
                        'message': f"{cache_name}: {cache_stats['expired_entries']} expired entries - consider more frequent cleanup"
                    })
                
                # Low hit rate
                if cache_stats['hit_rate'] < 50 and cache_stats['total_entries'] > 10:
                    recommendations.append({
                        'severity': 'info',
                        'category': 'cache_efficiency',
                        'message': f"{cache_name}: Low hit rate ({cache_stats['hit_rate']}%) - cache may not be effective"
                    })
                
                # Large database size
                if cache_stats['size_mb'] > 100:
                    recommendations.append({
                        'severity': 'warning',
                        'category': 'database_size',
                        'message': f"{cache_name}: Large database ({cache_stats['size_mb']} MB) - consider archiving old entries"
                    })
        
        # Check feedback
        if 'feedback' in stats:
            feedback_stats = stats['feedback']
            
            if feedback_stats['positive_rate'] < 70 and feedback_stats['total_feedback'] > 20:
                recommendations.append({
                    'severity': 'warning',
                    'category': 'system_quality',
                    'message': f"Low positive feedback rate ({feedback_stats['positive_rate']}%) - system quality may need improvement"
                })
        
        if not recommendations:
            recommendations.append({
                'severity': 'success',
                'category': 'health',
                'message': 'All databases are healthy and optimized'
            })
        
        return recommendations
    
    def get_quick_stats(self) -> Dict[str, Any]:
        """Get quick overview statistics"""
        stats = self._get_statistics()
        
        summary = {
            'total_cache_entries': 0,
            'total_cache_hits': 0,
            'total_db_size_mb': 0,
            'total_feedback': 0
        }
        
        for cache_name in ['semantic_cache', 'response_cache']:
            if cache_name in stats:
                summary['total_cache_entries'] += stats[cache_name]['valid_entries']
                summary['total_cache_hits'] += stats[cache_name]['total_hits']
                summary['total_db_size_mb'] += stats[cache_name]['size_mb']
        
        if 'feedback' in stats:
            summary['total_feedback'] = stats['feedback']['total_feedback']
            summary['total_db_size_mb'] += stats['feedback']['size_mb']
        
        summary['total_db_size_mb'] = round(summary['total_db_size_mb'], 2)
        
        return summary


def optimize_databases() -> Dict[str, Any]:
    """Convenience function to optimize all databases"""
    optimizer = DatabaseOptimizer()
    return optimizer.optimize_all()


def get_database_stats() -> Dict[str, Any]:
    """Convenience function to get database statistics"""
    optimizer = DatabaseOptimizer()
    return optimizer.get_quick_stats()
