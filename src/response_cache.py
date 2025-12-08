"""
Response Cache

Cache complete query responses for fast repeated queries.
Different from semantic_cache which only caches similar queries,
this caches exact responses with sources and metadata.
"""

import sqlite3
import hashlib
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path
from loguru import logger


class ResponseCache:
    """
    Cache complete query responses including sources and metadata
    
    Features:
    - Full response caching (answer + sources + metadata)
    - TTL-based expiration (default: 1 hour for fast queries)
    - Hash-based key generation
    - Automatic cleanup of expired entries
    """
    
    def __init__(self, db_path: str = "cache_db/response_cache.db", ttl_minutes: int = 60):
        """
        Initialize response cache
        
        Args:
            db_path: Path to SQLite database
            ttl_minutes: Time-to-live in minutes (default: 60)
        """
        self.db_path = db_path
        self.ttl_minutes = ttl_minutes
        
        # Create directory if needed
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        logger.info(f"✅ Response cache initialized at {db_path}")
        logger.info(f"   TTL: {ttl_minutes} minutes")
    
    def _init_database(self):
        """Create database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS response_cache (
                    query_hash TEXT PRIMARY KEY,
                    query_text TEXT NOT NULL,
                    response_json TEXT NOT NULL,
                    filters_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    hit_count INTEGER DEFAULT 0,
                    last_accessed TIMESTAMP
                )
            """)
            
            # Create indexes for performance
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_expires_at 
                ON response_cache(expires_at)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_query_text 
                ON response_cache(query_text)
            """)
            
            conn.commit()
    
    def _generate_key(self, query: str, filters: Optional[Dict] = None) -> str:
        """
        Generate cache key from query and filters
        
        Args:
            query: User query
            filters: Optional filters
            
        Returns:
            Hash key
        """
        # Normalize query (lowercase, strip whitespace)
        normalized = query.lower().strip()
        
        # Include filters in key
        filter_str = json.dumps(filters or {}, sort_keys=True)
        
        # Generate hash
        key_string = f"{normalized}|{filter_str}"
        return hashlib.sha256(key_string.encode()).hexdigest()
    
    def get(self, query: str, filters: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """
        Get cached response if available and not expired
        
        Args:
            query: User query
            filters: Optional filters
            
        Returns:
            Cached response dict or None
        """
        key = self._generate_key(query, filters)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get cached entry (check expiration manually)
            now = datetime.now().isoformat()
            result = cursor.execute("""
                SELECT response_json, hit_count, created_at, expires_at
                FROM response_cache
                WHERE query_hash = ? AND expires_at > ?
            """, (key, now)).fetchone()
            
            if result:
                # Update hit count and last accessed
                cursor.execute("""
                    UPDATE response_cache
                    SET hit_count = hit_count + 1,
                        last_accessed = CURRENT_TIMESTAMP
                    WHERE query_hash = ?
                """, (key,))
                conn.commit()
                
                # Parse and return response
                response = json.loads(result['response_json'])
                
                # Add cache metadata
                response['metadata']['cached'] = True
                response['metadata']['cache_age_seconds'] = (
                    datetime.now() - datetime.fromisoformat(result['created_at'])
                ).total_seconds()
                response['metadata']['cache_hits'] = result['hit_count'] + 1
                
                logger.info(f"💨 Cache HIT: {query[:50]}... (hits: {result['hit_count'] + 1})")
                return response
        
        logger.debug(f"❌ Cache MISS: {query[:50]}...")
        return None
    
    def set(self, query: str, response: Dict[str, Any], filters: Optional[Dict] = None):
        """
        Cache a query response
        
        Args:
            query: User query
            response: Complete response dict
            filters: Optional filters
        """
        key = self._generate_key(query, filters)
        
        # Calculate expiration time
        expires_at = datetime.now() + timedelta(minutes=self.ttl_minutes)
        
        # Serialize response (remove cache metadata if present)
        response_copy = response.copy()
        if 'metadata' in response_copy:
            metadata = response_copy['metadata'].copy()
            metadata.pop('cached', None)
            metadata.pop('cache_age_seconds', None)
            metadata.pop('cache_hits', None)
            response_copy['metadata'] = metadata
        
        response_json = json.dumps(response_copy, ensure_ascii=False)
        filters_json = json.dumps(filters or {}, ensure_ascii=False)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO response_cache 
                (query_hash, query_text, response_json, filters_json, expires_at, hit_count)
                VALUES (?, ?, ?, ?, ?, 0)
            """, (key, query, response_json, filters_json, expires_at.isoformat()))
            conn.commit()
        
        logger.debug(f"💾 Cached response: {query[:50]}... (expires in {self.ttl_minutes}m)")
    
    def clear_expired(self):
        """Remove expired cache entries"""
        now = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                DELETE FROM response_cache
                WHERE expires_at <= ?
            """, (now,))
            deleted = cursor.rowcount
            conn.commit()
        
        if deleted > 0:
            logger.info(f"🧹 Cleared {deleted} expired cache entries")
        
        return deleted
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get cache statistics"""
        now = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Total entries
            total = conn.execute("""
                SELECT COUNT(*) as count FROM response_cache
            """).fetchone()['count']
            
            # Valid (non-expired) entries
            valid = conn.execute("""
                SELECT COUNT(*) as count FROM response_cache
                WHERE expires_at > ?
            """, (now,)).fetchone()['count']
            
            # Total hits
            hits = conn.execute("""
                SELECT COALESCE(SUM(hit_count), 0) as total FROM response_cache
            """).fetchone()['total']
            
            # Most accessed queries
            top_queries = conn.execute("""
                SELECT query_text, hit_count, created_at
                FROM response_cache
                WHERE expires_at > ?
                ORDER BY hit_count DESC
                LIMIT 5
            """, (now,)).fetchall()
        
        return {
            'total_entries': total,
            'valid_entries': valid,
            'expired_entries': total - valid,
            'total_hits': hits,
            'hit_rate': round(hits / total * 100, 1) if total > 0 else 0,
            'top_queries': [
                {
                    'query': q['query_text'],
                    'hits': q['hit_count'],
                    'age': (datetime.now() - datetime.fromisoformat(q['created_at'])).total_seconds() / 60
                }
                for q in top_queries
            ]
        }
    
    def clear_all(self):
        """Clear all cache entries"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM response_cache")
            deleted = cursor.rowcount
            conn.commit()
        
        logger.warning(f"⚠️ Cleared all cache entries ({deleted} total)")
        return deleted


# Singleton instance
_response_cache = None


def get_response_cache() -> ResponseCache:
    """Get or create response cache singleton"""
    global _response_cache
    
    if _response_cache is None:
        _response_cache = ResponseCache()
    
    return _response_cache
