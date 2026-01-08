"""
Granular Feedback Manager

Supports fine-grained feedback on responses:
- Source-level feedback (each document separately)
- Text selection feedback (highlight useful parts)
- Multi-dimensional ratings
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from loguru import logger
import json


class GranularFeedbackManager:
    """
    Manages detailed, granular user feedback
    
    Features:
    - Rate individual sources
    - Highlight useful text snippets
    - Multi-dimensional ratings (relevance, clarity, etc.)
    - Learn which sources are most valuable
    """
    
    def __init__(self, db_path: str = "feedback_db/granular_feedback.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        logger.info(f"✅ Granular Feedback Manager initialized at {self.db_path}")
    
    def _init_database(self):
        """Initialize enhanced database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Main feedback table (overall)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                query TEXT NOT NULL,
                response TEXT NOT NULL,
                overall_rating INTEGER,  -- 1-5 stars
                relevance_rating INTEGER,
                clarity_rating INTEGER,
                completeness_rating INTEGER,
                comment TEXT
            )
        """)
        
        # Source-level feedback
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS source_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feedback_id INTEGER NOT NULL,
                document_name TEXT NOT NULL,
                page_number TEXT,
                chunk_text TEXT,
                rating TEXT,  -- 'helpful', 'not_helpful', 'irrelevant'
                stars INTEGER,  -- 1-5
                comment TEXT,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (feedback_id) REFERENCES feedback(id)
            )
        """)
        
        # Text highlights (user selected useful text)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS text_highlights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feedback_id INTEGER NOT NULL,
                highlighted_text TEXT NOT NULL,
                start_position INTEGER,
                end_position INTEGER,
                sentiment TEXT,  -- 'positive', 'negative', 'neutral'
                source_document TEXT,
                comment TEXT,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (feedback_id) REFERENCES feedback(id)
            )
        """)
        
        # Aggregated source scores (learned from feedback)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS source_quality_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_name TEXT NOT NULL UNIQUE,
                avg_rating REAL DEFAULT 0.0,
                helpful_count INTEGER DEFAULT 0,
                not_helpful_count INTEGER DEFAULT 0,
                irrelevant_count INTEGER DEFAULT 0,
                total_feedbacks INTEGER DEFAULT 0,
                quality_score REAL DEFAULT 0.0,
                last_updated TEXT NOT NULL
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info("📊 Granular feedback database schema initialized")
    
    def add_feedback(
        self,
        query: str,
        response: str,
        overall_rating: Optional[int] = None,
        source_feedbacks: Optional[List[Dict]] = None,
        highlights: Optional[List[Dict]] = None,
        dimensions: Optional[Dict[str, int]] = None,
        comment: Optional[str] = None
    ) -> int:
        """
        Add granular feedback
        
        Args:
            query: User query
            response: AI response
            overall_rating: 1-5 stars for overall response
            source_feedbacks: List of source-specific feedback
                [{"document": "IS3218", "rating": "helpful", "stars": 5, "comment": "..."}]
            highlights: List of highlighted text
                [{"text": "...", "sentiment": "positive", "source": "IS3218"}]
            dimensions: Multi-dimensional ratings
                {"relevance": 5, "clarity": 4, "completeness": 3}
            comment: Overall comment
            
        Returns:
            Feedback ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        timestamp = datetime.now().isoformat()
        
        # Insert main feedback
        cursor.execute("""
            INSERT INTO feedback 
            (timestamp, query, response, overall_rating, relevance_rating, 
             clarity_rating, completeness_rating, comment)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp,
            query,
            response,
            overall_rating,
            dimensions.get('relevance') if dimensions else None,
            dimensions.get('clarity') if dimensions else None,
            dimensions.get('completeness') if dimensions else None,
            comment
        ))
        
        feedback_id = cursor.lastrowid
        
        # Insert source-level feedback
        if source_feedbacks:
            for src_fb in source_feedbacks:
                cursor.execute("""
                    INSERT INTO source_feedback
                    (feedback_id, document_name, page_number, chunk_text, 
                     rating, stars, comment, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    feedback_id,
                    src_fb.get('document'),
                    src_fb.get('page'),
                    src_fb.get('text', '')[:500],
                    src_fb.get('rating'),
                    src_fb.get('stars'),
                    src_fb.get('comment'),
                    timestamp
                ))
                
                # Update aggregated scores
                self._update_source_quality(cursor, src_fb.get('document'), 
                                            src_fb.get('rating'), 
                                            src_fb.get('stars', 3))
        
        # Insert highlights
        if highlights:
            for highlight in highlights:
                cursor.execute("""
                    INSERT INTO text_highlights
                    (feedback_id, highlighted_text, start_position, end_position,
                     sentiment, source_document, comment, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    feedback_id,
                    highlight.get('text'),
                    highlight.get('start_pos'),
                    highlight.get('end_pos'),
                    highlight.get('sentiment', 'positive'),
                    highlight.get('source'),
                    highlight.get('comment'),
                    timestamp
                ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Granular feedback added (ID: {feedback_id})")
        if source_feedbacks:
            logger.info(f"   📚 {len(source_feedbacks)} source ratings")
        if highlights:
            logger.info(f"   ✨ {len(highlights)} text highlights")
        
        return feedback_id
    
    def _update_source_quality(self, cursor, doc_name: str, rating: str, stars: int):
        """Update aggregated quality scores for a document"""
        timestamp = datetime.now().isoformat()
        
        # Get current stats
        cursor.execute("""
            SELECT helpful_count, not_helpful_count, irrelevant_count, 
                   total_feedbacks, avg_rating
            FROM source_quality_scores
            WHERE document_name = ?
        """, (doc_name,))
        
        result = cursor.fetchone()
        
        if result:
            helpful, not_helpful, irrelevant, total, avg_rating = result
            total += 1
            
            # Update counts based on rating
            if rating == 'helpful':
                helpful += 1
            elif rating == 'not_helpful':
                not_helpful += 1
            elif rating == 'irrelevant':
                irrelevant += 1
            
            # Update average rating
            new_avg = ((avg_rating * (total - 1)) + stars) / total
            
            # Calculate quality score (0-100)
            # Helpful = +10, Not helpful = -5, Irrelevant = -10
            quality_score = (helpful * 10 - not_helpful * 5 - irrelevant * 10) / total
            quality_score = max(0, min(100, quality_score + 50))  # Normalize to 0-100
            
            cursor.execute("""
                UPDATE source_quality_scores
                SET helpful_count = ?, not_helpful_count = ?, irrelevant_count = ?,
                    total_feedbacks = ?, avg_rating = ?, quality_score = ?,
                    last_updated = ?
                WHERE document_name = ?
            """, (helpful, not_helpful, irrelevant, total, new_avg, 
                  quality_score, timestamp, doc_name))
        else:
            # Insert new
            helpful = 1 if rating == 'helpful' else 0
            not_helpful = 1 if rating == 'not_helpful' else 0
            irrelevant = 1 if rating == 'irrelevant' else 0
            quality_score = 50  # Neutral start
            
            cursor.execute("""
                INSERT INTO source_quality_scores
                (document_name, avg_rating, helpful_count, not_helpful_count,
                 irrelevant_count, total_feedbacks, quality_score, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (doc_name, stars, helpful, not_helpful, irrelevant, 
                  1, quality_score, timestamp))
    
    def get_source_quality_scores(self) -> Dict[str, Dict]:
        """
        Get quality scores for all sources
        
        Returns:
            Dict of {document_name: {avg_rating, quality_score, counts}}
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT document_name, avg_rating, quality_score, helpful_count,
                   not_helpful_count, irrelevant_count, total_feedbacks
            FROM source_quality_scores
            ORDER BY quality_score DESC
        """)
        
        scores = {}
        for row in cursor.fetchall():
            doc, avg_rating, quality, helpful, not_helpful, irrelevant, total = row
            scores[doc] = {
                'avg_rating': avg_rating,
                'quality_score': quality,
                'helpful_count': helpful,
                'not_helpful_count': not_helpful,
                'irrelevant_count': irrelevant,
                'total_feedbacks': total
            }
        
        conn.close()
        return scores
    
    def get_best_sources(self, limit: int = 10) -> List[Dict]:
        """Get top-rated sources"""
        scores = self.get_source_quality_scores()
        sorted_sources = sorted(
            scores.items(), 
            key=lambda x: x[1]['quality_score'], 
            reverse=True
        )
        
        return [
            {
                'document': doc,
                'quality_score': data['quality_score'],
                'avg_rating': data['avg_rating'],
                'total_feedbacks': data['total_feedbacks']
            }
            for doc, data in sorted_sources[:limit]
        ]
    
    def get_highlighted_snippets(self, limit: int = 20) -> List[Dict]:
        """Get most frequently highlighted text snippets"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT highlighted_text, source_document, sentiment, 
                   COUNT(*) as frequency
            FROM text_highlights
            WHERE sentiment = 'positive'
            GROUP BY highlighted_text
            ORDER BY frequency DESC
            LIMIT ?
        """, (limit,))
        
        snippets = []
        for row in cursor.fetchall():
            text, source, sentiment, freq = row
            snippets.append({
                'text': text,
                'source': source,
                'sentiment': sentiment,
                'frequency': freq
            })
        
        conn.close()
        return snippets
    
    def get_source_feedback_for_document(self, document: str) -> Dict:
        """Get detailed feedback for a specific document"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT rating, stars, comment, timestamp
            FROM source_feedback
            WHERE document_name = ?
            ORDER BY timestamp DESC
        """, (document,))
        
        feedbacks = []
        for row in cursor.fetchall():
            rating, stars, comment, timestamp = row
            feedbacks.append({
                'rating': rating,
                'stars': stars,
                'comment': comment,
                'timestamp': timestamp
            })
        
        conn.close()
        return {
            'document': document,
            'feedbacks': feedbacks,
            'total_count': len(feedbacks)
        }
    
    def get_statistics(self) -> Dict:
        """Get overall statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Overall stats
        cursor.execute("SELECT COUNT(*), AVG(overall_rating) FROM feedback")
        total_feedback, avg_overall = cursor.fetchone()
        
        # Source feedback stats
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN rating = 'helpful' THEN 1 ELSE 0 END) as helpful,
                SUM(CASE WHEN rating = 'not_helpful' THEN 1 ELSE 0 END) as not_helpful,
                SUM(CASE WHEN rating = 'irrelevant' THEN 1 ELSE 0 END) as irrelevant
            FROM source_feedback
        """)
        src_stats = cursor.fetchone()
        
        # Highlights stats
        cursor.execute("SELECT COUNT(*) FROM text_highlights")
        total_highlights = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_feedbacks': total_feedback or 0,
            'avg_overall_rating': avg_overall or 0,
            'source_feedbacks': {
                'total': src_stats[0] or 0,
                'helpful': src_stats[1] or 0,
                'not_helpful': src_stats[2] or 0,
                'irrelevant': src_stats[3] or 0
            },
            'total_highlights': total_highlights or 0
        }


# Singleton
_granular_feedback_manager = None

def get_granular_feedback_manager() -> GranularFeedbackManager:
    """Get global instance"""
    global _granular_feedback_manager
    if _granular_feedback_manager is None:
        _granular_feedback_manager = GranularFeedbackManager()
    return _granular_feedback_manager
