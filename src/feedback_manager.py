"""
Feedback Manager

Manages user feedback on AI responses for active learning.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from loguru import logger


class FeedbackManager:
    """
    Manages user feedback storage and retrieval for active learning
    """
    
    def __init__(self, db_path: str = "feedback_db/feedback.db"):
        """
        Initialize feedback manager
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        logger.info(f"✅ Feedback Manager initialized at {self.db_path}")
    
    def _init_database(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Feedback table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                query TEXT NOT NULL,
                response TEXT NOT NULL,
                feedback_type TEXT NOT NULL,  -- 'positive' or 'negative'
                comment TEXT,
                source_documents TEXT,  -- JSON string of source docs
                metadata TEXT  -- JSON string of additional metadata
            )
        """)
        
        # Source relevance scores table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS source_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_name TEXT NOT NULL,
                page_number TEXT,
                chunk_text TEXT NOT NULL,
                relevance_score REAL DEFAULT 0.0,
                positive_count INTEGER DEFAULT 0,
                negative_count INTEGER DEFAULT 0,
                last_updated TEXT NOT NULL,
                UNIQUE(document_name, page_number, chunk_text)
            )
        """)
        
        # Query patterns table (for learning common queries)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS query_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_normalized TEXT NOT NULL UNIQUE,
                query_count INTEGER DEFAULT 1,
                positive_feedback_count INTEGER DEFAULT 0,
                negative_feedback_count INTEGER DEFAULT 0,
                last_queried TEXT NOT NULL
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info("📊 Feedback database schema initialized")
    
    def add_feedback(
        self,
        query: str,
        response: str,
        feedback_type: str,
        sources: List[Dict],
        comment: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> int:
        """
        Add user feedback
        
        Args:
            query: User query
            response: AI response
            feedback_type: 'positive' or 'negative'
            sources: List of source documents
            comment: Optional user comment
            metadata: Optional additional metadata
            
        Returns:
            Feedback ID
        """
        import json
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        sources_json = json.dumps(sources)
        metadata_json = json.dumps(metadata) if metadata else None
        
        cursor.execute("""
            INSERT INTO feedback (timestamp, query, response, feedback_type, comment, source_documents, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (timestamp, query, response, feedback_type, comment, sources_json, metadata_json))
        
        feedback_id = cursor.lastrowid
        
        # Update source scores
        self._update_source_scores(cursor, sources, feedback_type)
        
        # Update query patterns
        self._update_query_patterns(cursor, query, feedback_type)
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Feedback added: {feedback_type} (ID: {feedback_id})")
        return feedback_id
    
    def _update_source_scores(self, cursor, sources: List[Dict], feedback_type: str):
        """Update relevance scores for source documents"""
        score_delta = 1.0 if feedback_type == 'positive' else -0.5
        
        for source in sources:
            doc_name = source.get('document', 'Unknown')
            page = source.get('page', 'N/A')
            chunk_text = source.get('text', '')[:500]  # First 500 chars
            
            timestamp = datetime.now().isoformat()
            
            # Check if record exists
            cursor.execute("""
                SELECT relevance_score, positive_count, negative_count
                FROM source_scores
                WHERE document_name = ? AND page_number = ? AND chunk_text = ?
            """, (doc_name, page, chunk_text))
            
            result = cursor.fetchone()
            
            if result:
                # Update existing
                current_score, pos_count, neg_count = result
                new_score = current_score + score_delta
                
                if feedback_type == 'positive':
                    pos_count += 1
                else:
                    neg_count += 1
                
                cursor.execute("""
                    UPDATE source_scores
                    SET relevance_score = ?, positive_count = ?, negative_count = ?, last_updated = ?
                    WHERE document_name = ? AND page_number = ? AND chunk_text = ?
                """, (new_score, pos_count, neg_count, timestamp, doc_name, page, chunk_text))
            else:
                # Insert new
                pos_count = 1 if feedback_type == 'positive' else 0
                neg_count = 1 if feedback_type == 'negative' else 0
                
                cursor.execute("""
                    INSERT INTO source_scores (document_name, page_number, chunk_text, relevance_score, positive_count, negative_count, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (doc_name, page, chunk_text, score_delta, pos_count, neg_count, timestamp))
    
    def _update_query_patterns(self, cursor, query: str, feedback_type: str):
        """Update query pattern statistics"""
        # Normalize query (lowercase, strip)
        query_normalized = query.lower().strip()
        timestamp = datetime.now().isoformat()
        
        cursor.execute("""
            SELECT query_count, positive_feedback_count, negative_feedback_count
            FROM query_patterns
            WHERE query_normalized = ?
        """, (query_normalized,))
        
        result = cursor.fetchone()
        
        if result:
            query_count, pos_count, neg_count = result
            query_count += 1
            
            if feedback_type == 'positive':
                pos_count += 1
            else:
                neg_count += 1
            
            cursor.execute("""
                UPDATE query_patterns
                SET query_count = ?, positive_feedback_count = ?, negative_feedback_count = ?, last_queried = ?
                WHERE query_normalized = ?
            """, (query_count, pos_count, neg_count, timestamp, query_normalized))
        else:
            pos_count = 1 if feedback_type == 'positive' else 0
            neg_count = 1 if feedback_type == 'negative' else 0
            
            cursor.execute("""
                INSERT INTO query_patterns (query_normalized, query_count, positive_feedback_count, negative_feedback_count, last_queried)
                VALUES (?, 1, ?, ?, ?)
            """, (query_normalized, pos_count, neg_count, timestamp))
    
    def get_source_score(self, document_name: str, page: str, chunk_text: str) -> float:
        """
        Get relevance score for a source chunk
        
        Args:
            document_name: Document name
            page: Page number
            chunk_text: Chunk text (first 500 chars)
            
        Returns:
            Relevance score (default 0.0)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT relevance_score
            FROM source_scores
            WHERE document_name = ? AND page_number = ? AND chunk_text = ?
        """, (document_name, page, chunk_text[:500]))
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else 0.0
    
    def get_statistics(self) -> Dict:
        """Get feedback statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total feedback count
        cursor.execute("SELECT COUNT(*) FROM feedback")
        total_feedback = cursor.fetchone()[0]
        
        # Positive/Negative counts
        cursor.execute("SELECT COUNT(*) FROM feedback WHERE feedback_type = 'positive'")
        positive_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM feedback WHERE feedback_type = 'negative'")
        negative_count = cursor.fetchone()[0]
        
        # Top performing sources
        cursor.execute("""
            SELECT document_name, AVG(relevance_score) as avg_score
            FROM source_scores
            GROUP BY document_name
            ORDER BY avg_score DESC
            LIMIT 5
        """)
        top_sources = cursor.fetchall()
        
        # Most queried patterns
        cursor.execute("""
            SELECT query_normalized, query_count
            FROM query_patterns
            ORDER BY query_count DESC
            LIMIT 5
        """)
        top_queries = cursor.fetchall()
        
        conn.close()
        
        return {
            'total_feedback': total_feedback,
            'positive_count': positive_count,
            'negative_count': negative_count,
            'satisfaction_rate': (positive_count / total_feedback * 100) if total_feedback > 0 else 0,
            'top_sources': [{'document': doc, 'score': score} for doc, score in top_sources],
            'top_queries': [{'query': q, 'count': c} for q, c in top_queries]
        }
    
    def get_recent_feedback(self, limit: int = 10) -> List[Dict]:
        """Get recent feedback entries"""
        import json
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, timestamp, query, response, feedback_type, comment
            FROM feedback
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        feedback_list = []
        for row in results:
            feedback_list.append({
                'id': row[0],
                'timestamp': row[1],
                'query': row[2],
                'response': row[3][:200] + '...',  # Truncate
                'feedback_type': row[4],
                'comment': row[5]
            })
        
        return feedback_list


# Singleton instance
_feedback_manager = None

def get_feedback_manager(db_path: str = "feedback_db/feedback.db") -> FeedbackManager:
    """Get singleton feedback manager instance"""
    global _feedback_manager
    if _feedback_manager is None:
        _feedback_manager = FeedbackManager(db_path)
    return _feedback_manager
