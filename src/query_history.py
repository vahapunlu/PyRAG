"""
Query History Manager

Tracks user queries and responses for quick access and analytics
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from loguru import logger


class QueryHistory:
    """
    Manage query history with SQLite backend
    
    Features:
    - Store queries, responses, and metadata
    - Search history
    - Retrieve recent queries
    - Clear history
    """
    
    def __init__(self, db_path: str = "history_db/query_history.db"):
        """Initialize query history"""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_database()
        logger.info(f"✅ Query History initialized at {db_path}")
    
    def _init_database(self):
        """Create database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS query_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    response TEXT NOT NULL,
                    sources_json TEXT,
                    metadata_json TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    duration_seconds REAL,
                    sources_count INTEGER DEFAULT 0
                )
            """)
            
            # Create indexes
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON query_history(timestamp DESC)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_query 
                ON query_history(query)
            """)
            
            conn.commit()
    
    def add_query(self, query: str, response: str, sources: List[Dict] = None, 
                  metadata: Dict = None, duration: float = None):
        """
        Add query to history
        
        Args:
            query: User query
            response: System response
            sources: List of source documents
            metadata: Additional metadata
            duration: Query duration in seconds
        """
        sources_json = json.dumps(sources or [], ensure_ascii=False)
        metadata_json = json.dumps(metadata or {}, ensure_ascii=False)
        sources_count = len(sources) if sources else 0
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO query_history 
                (query, response, sources_json, metadata_json, duration_seconds, sources_count)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (query, response, sources_json, metadata_json, duration, sources_count))
            conn.commit()
        
        logger.debug(f"📝 Added to history: {query[:50]}...")
    
    def get_recent(self, limit: int = 20) -> List[Dict]:
        """
        Get recent queries
        
        Args:
            limit: Maximum number of queries to return
            
        Returns:
            List of query dicts
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT id, query, response, sources_json, metadata_json, 
                       timestamp, duration_seconds, sources_count
                FROM query_history
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row['id'],
                    'query': row['query'],
                    'response': row['response'],
                    'sources': json.loads(row['sources_json']),
                    'metadata': json.loads(row['metadata_json']),
                    'timestamp': row['timestamp'],
                    'duration': row['duration_seconds'],
                    'sources_count': row['sources_count']
                })
            
            return results
    
    def search(self, search_term: str, limit: int = 20) -> List[Dict]:
        """
        Search query history
        
        Args:
            search_term: Search term
            limit: Maximum results
            
        Returns:
            List of matching queries
        """
        search_pattern = f"%{search_term}%"
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT id, query, response, sources_json, metadata_json, 
                       timestamp, duration_seconds, sources_count
                FROM query_history
                WHERE query LIKE ? OR response LIKE ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (search_pattern, search_pattern, limit))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row['id'],
                    'query': row['query'],
                    'response': row['response'][:200] + '...',  # Preview
                    'sources': json.loads(row['sources_json']),
                    'metadata': json.loads(row['metadata_json']),
                    'timestamp': row['timestamp'],
                    'duration': row['duration_seconds'],
                    'sources_count': row['sources_count']
                })
            
            return results
    
    def get_by_id(self, query_id: int) -> Optional[Dict]:
        """Get specific query by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT id, query, response, sources_json, metadata_json, 
                       timestamp, duration_seconds, sources_count
                FROM query_history
                WHERE id = ?
            """, (query_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': row['id'],
                    'query': row['query'],
                    'response': row['response'],
                    'sources': json.loads(row['sources_json']),
                    'metadata': json.loads(row['metadata_json']),
                    'timestamp': row['timestamp'],
                    'duration': row['duration_seconds'],
                    'sources_count': row['sources_count']
                }
        
        return None
    
    def clear_all(self) -> int:
        """Clear all history
        
        Returns:
            Number of deleted records
        """
        with sqlite3.connect(self.db_path) as conn:
            # Get count before deleting
            count = conn.execute("SELECT COUNT(*) FROM query_history").fetchone()[0]
            conn.execute("DELETE FROM query_history")
            conn.commit()
        
        logger.warning(f"⚠️ Query history cleared ({count} records deleted)")
        return count
    
    def get_statistics(self) -> Dict:
        """Get history statistics"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            stats = conn.execute("""
                SELECT 
                    COUNT(*) as total_queries,
                    AVG(duration_seconds) as avg_duration,
                    AVG(sources_count) as avg_sources,
                    MIN(timestamp) as first_query,
                    MAX(timestamp) as last_query
                FROM query_history
            """).fetchone()
            
            return {
                'total_queries': stats['total_queries'],
                'avg_duration': round(stats['avg_duration'], 2) if stats['avg_duration'] else 0,
                'avg_sources': round(stats['avg_sources'], 1) if stats['avg_sources'] else 0,
                'first_query': stats['first_query'],
                'last_query': stats['last_query']
            }


# Singleton instance
_query_history = None

def get_query_history() -> QueryHistory:
    """Get or create query history singleton"""
    global _query_history
    
    if _query_history is None:
        _query_history = QueryHistory()
    
    return _query_history
