"""
Semantic Cache for RAG queries
Caches query-answer pairs using embedding similarity for fast retrieval
"""

import json
import sqlite3
import time
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import numpy as np
from loguru import logger

from src.utils import Settings


class SemanticCache:
    """
    Semantic cache using embeddings for similarity-based query matching
    
    Features:
    - Stores query embeddings and answers
    - Fuzzy matching with similarity threshold
    - TTL (time-to-live) support
    - SQLite backend for persistence
    - Automatic cleanup of expired entries
    """
    
    def __init__(
        self,
        cache_db_path: str = "./cache_db/semantic_cache.db",
        similarity_threshold: float = 0.92,
        ttl_seconds: int = 86400 * 7,  # 7 days default
        max_cache_size: int = 1000
    ):
        """
        Initialize semantic cache
        
        Args:
            cache_db_path: Path to SQLite database
            similarity_threshold: Minimum similarity for cache hit (0.92 = 92%)
            ttl_seconds: Time to live for cache entries (default 7 days)
            max_cache_size: Maximum number of cached entries
        """
        self.cache_db_path = Path(cache_db_path)
        self.similarity_threshold = similarity_threshold
        self.ttl_seconds = ttl_seconds
        self.max_cache_size = max_cache_size
        
        # Create cache directory
        self.cache_db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_db()
        
        # Statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "total_queries": 0
        }
        
        logger.info(f"✅ Semantic cache initialized at {self.cache_db_path}")
        logger.info(f"   Similarity threshold: {self.similarity_threshold}")
        logger.info(f"   TTL: {ttl_seconds / 86400:.1f} days")
    
    def _init_db(self):
        """Initialize SQLite database with schema"""
        conn = sqlite3.connect(str(self.cache_db_path))
        cursor = conn.cursor()
        
        # Create cache table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS query_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                query_embedding TEXT NOT NULL,
                answer TEXT NOT NULL,
                sources TEXT,
                timestamp REAL NOT NULL,
                hit_count INTEGER DEFAULT 0,
                last_accessed REAL NOT NULL
            )
        """)
        
        # Create index on timestamp for cleanup
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp ON query_cache(timestamp)
        """)
        
        conn.commit()
        conn.close()
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def _get_query_embedding(self, query: str) -> List[float]:
        """Generate embedding for query using OpenAI"""
        try:
            # Check if Settings.embed_model is configured
            if hasattr(Settings, 'embed_model') and Settings.embed_model is not None:
                embedding_model = Settings.embed_model
            else:
                # Fallback: create embedding model from settings
                from llama_index.embeddings.openai import OpenAIEmbedding
                from src.utils import get_settings
                settings = get_settings()
                embedding_model = OpenAIEmbedding(
                    model=settings.embedding_model,
                    api_key=settings.openai_api_key
                )
            
            # Get embedding (returns list of floats)
            embedding = embedding_model.get_text_embedding(query)
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return []
    
    def get(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Get cached answer for query if similar query exists
        
        Args:
            query: User query string
            
        Returns:
            Cached response dict or None if no match found
        """
        self.stats["total_queries"] += 1
        
        # Generate embedding for incoming query
        query_embedding = self._get_query_embedding(query)
        if not query_embedding:
            self.stats["misses"] += 1
            return None
        
        # Search cache for similar queries
        conn = sqlite3.connect(str(self.cache_db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, query, query_embedding, answer, sources, timestamp, hit_count
            FROM query_cache
            WHERE timestamp > ?
            ORDER BY last_accessed DESC
            LIMIT 100
        """, (time.time() - self.ttl_seconds,))
        
        best_match = None
        best_similarity = 0.0
        best_entry_id = None
        
        for row in cursor.fetchall():
            entry_id, cached_query, cached_embedding_str, answer, sources, timestamp, hit_count = row
            
            # Parse cached embedding
            cached_embedding = json.loads(cached_embedding_str)
            
            # Calculate similarity
            similarity = self._cosine_similarity(query_embedding, cached_embedding)
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = {
                    "query": cached_query,
                    "answer": answer,
                    "sources": json.loads(sources) if sources else None,
                    "similarity": similarity,
                    "hit_count": hit_count,
                    "cached_at": timestamp
                }
                best_entry_id = entry_id
        
        # Check if best match exceeds threshold
        if best_match and best_similarity >= self.similarity_threshold:
            # Update hit count and last accessed
            cursor.execute("""
                UPDATE query_cache
                SET hit_count = hit_count + 1, last_accessed = ?
                WHERE id = ?
            """, (time.time(), best_entry_id))
            conn.commit()
            
            self.stats["hits"] += 1
            logger.info(f"🎯 Cache HIT! Similarity: {best_similarity:.3f} | Query: {query[:50]}...")
            logger.info(f"   Matched with: {best_match['query'][:50]}...")
            
            conn.close()
            return best_match
        
        conn.close()
        self.stats["misses"] += 1
        return None
    
    def set(self, query: str, answer: str, sources: Optional[List[Dict]] = None):
        """
        Cache query-answer pair
        
        Args:
            query: User query string
            answer: Generated answer
            sources: List of source documents (optional)
        """
        # Generate embedding
        query_embedding = self._get_query_embedding(query)
        if not query_embedding:
            logger.warning("Failed to cache query - no embedding generated")
            return
        
        conn = sqlite3.connect(str(self.cache_db_path))
        cursor = conn.cursor()
        
        # Check cache size and cleanup if needed
        cursor.execute("SELECT COUNT(*) FROM query_cache")
        cache_size = cursor.fetchone()[0]
        
        if cache_size >= self.max_cache_size:
            # Remove oldest entries (by last accessed)
            cursor.execute("""
                DELETE FROM query_cache
                WHERE id IN (
                    SELECT id FROM query_cache
                    ORDER BY last_accessed ASC
                    LIMIT ?
                )
            """, (self.max_cache_size // 10,))  # Remove 10%
            logger.info(f"🧹 Cache cleanup: removed {cursor.rowcount} old entries")
        
        # Insert new entry
        cursor.execute("""
            INSERT INTO query_cache (query, query_embedding, answer, sources, timestamp, last_accessed)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            query,
            json.dumps(query_embedding),
            answer,
            json.dumps(sources) if sources else None,
            time.time(),
            time.time()
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"💾 Cached query: {query[:50]}...")
    
    def clear(self):
        """Clear all cache entries"""
        conn = sqlite3.connect(str(self.cache_db_path))
        cursor = conn.cursor()
        cursor.execute("DELETE FROM query_cache")
        conn.commit()
        conn.close()
        
        self.stats = {"hits": 0, "misses": 0, "total_queries": 0}
        logger.info("🗑️ Cache cleared")
    
    def cleanup_expired(self):
        """Remove expired cache entries based on TTL"""
        conn = sqlite3.connect(str(self.cache_db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM query_cache
            WHERE timestamp < ?
        """, (time.time() - self.ttl_seconds,))
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        if deleted_count > 0:
            logger.info(f"🧹 Cleaned up {deleted_count} expired cache entries")
        
        return deleted_count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        conn = sqlite3.connect(str(self.cache_db_path))
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM query_cache")
        total_entries = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT AVG(hit_count), MAX(hit_count)
            FROM query_cache
        """)
        avg_hits, max_hits = cursor.fetchone()
        
        conn.close()
        
        hit_rate = (self.stats["hits"] / self.stats["total_queries"] * 100) if self.stats["total_queries"] > 0 else 0
        
        return {
            "total_entries": total_entries,
            "total_queries": self.stats["total_queries"],
            "cache_hits": self.stats["hits"],
            "cache_misses": self.stats["misses"],
            "hit_rate_percent": hit_rate,
            "avg_hits_per_entry": avg_hits or 0,
            "max_hits_per_entry": max_hits or 0,
            "similarity_threshold": self.similarity_threshold,
            "ttl_days": self.ttl_seconds / 86400
        }
    
    def get_top_queries(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Get most frequently accessed queries"""
        conn = sqlite3.connect(str(self.cache_db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT query, hit_count
            FROM query_cache
            ORDER BY hit_count DESC
            LIMIT ?
        """, (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        return results


# Global cache instance
_cache_instance: Optional[SemanticCache] = None


def get_cache() -> SemanticCache:
    """Get global cache instance (singleton pattern)"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = SemanticCache()
    return _cache_instance
