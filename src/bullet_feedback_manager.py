"""
Bullet-Level Feedback Manager

Tracks user feedback on individual bullet points to:
1. Identify irrelevant chunks (false positives from retrieval)
2. Learn query-chunk relevance patterns
3. Penalize irrelevant chunks in future retrievals

Simple approach: ✓ (relevant) / ✗ (irrelevant)
"""

import sqlite3
import json
import re
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from datetime import datetime
from loguru import logger


class BulletFeedbackManager:
    """Manages bullet-level relevance feedback"""
    
    def __init__(self, db_path: str = "feedback_db/bullet_feedback.db"):
        """Initialize bullet feedback manager"""
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        logger.info(f"✅ BulletFeedbackManager initialized at {db_path}")
    
    def _init_database(self):
        """Create database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Bullet feedback table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bullet_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                response_id TEXT NOT NULL,
                query TEXT NOT NULL,
                bullet_index INTEGER NOT NULL,
                bullet_text TEXT NOT NULL,
                source_ref TEXT,  -- Extracted source reference (e.g., "IS 3218, 6.5.1.13")
                is_relevant BOOLEAN NOT NULL,  -- True=✓, False=✗
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Query-chunk relevance patterns
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chunk_relevance_score (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_pattern TEXT NOT NULL,  -- Normalized query (e.g., "dedektör yerleştirme")
                source_ref TEXT NOT NULL,     -- Chunk reference (e.g., "IS3218#6.5.1.13")
                relevant_count INTEGER DEFAULT 0,
                irrelevant_count INTEGER DEFAULT 0,
                relevance_score REAL,  -- Calculated: relevant / (relevant + irrelevant)
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(query_pattern, source_ref)
            )
        """)
        
        # Indexes for fast lookup
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_bullet_response 
            ON bullet_feedback(response_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_bullet_query 
            ON bullet_feedback(query)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_chunk_pattern 
            ON chunk_relevance_score(query_pattern)
        """)
        
        conn.commit()
        conn.close()
        logger.info("📊 Bullet feedback database schema initialized")
    
    def add_feedback(self, 
                     response_id: str,
                     query: str,
                     bullet_index: int,
                     bullet_text: str,
                     is_relevant: bool) -> int:
        """
        Add feedback for a bullet point
        
        Args:
            response_id: Unique response identifier
            query: Original user query
            bullet_index: Index of bullet in response (0-based)
            bullet_text: Full bullet text
            is_relevant: True if relevant (✓), False if irrelevant (✗)
            
        Returns:
            Feedback ID
        """
        # Extract source reference from bullet
        source_ref = self._extract_source_reference(bullet_text)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Insert feedback
        cursor.execute("""
            INSERT INTO bullet_feedback 
            (response_id, query, bullet_index, bullet_text, source_ref, is_relevant)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (response_id, query, bullet_index, bullet_text, source_ref, is_relevant))
        
        feedback_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Update relevance scores
        if source_ref:
            self._update_relevance_score(query, source_ref, is_relevant)
        
        logger.info(f"{'✓' if is_relevant else '✗'} Bullet feedback: {bullet_text[:50]}... → {source_ref}")
        
        return feedback_id
    
    def _extract_source_reference(self, bullet_text: str) -> Optional[str]:
        """
        Extract source reference from bullet text
        
        Examples:
            "Text (IS 3218, 6.5.1.13)" → "IS3218#6.5.1.13"
            "Text (NEK 606, Table 2)" → "NEK606#Table2"
            "Text [IS 3218]" → "IS3218"
        """
        # Pattern 1: (Source, Section)
        match = re.search(r'\(([A-Z][A-Za-z0-9\s]+),\s*([\d.]+|Table\s*\d+|Tablo\s*\d+)\)', bullet_text)
        if match:
            source = match.group(1).replace(' ', '')
            section = match.group(2).replace(' ', '')
            return f"{source}#{section}"
        
        # Pattern 2: (Source)
        match = re.search(r'\(([A-Z][A-Za-z0-9\s]+)\)', bullet_text)
        if match:
            return match.group(1).replace(' ', '')
        
        # Pattern 3: [Source]
        match = re.search(r'\[([A-Z][A-Za-z0-9\s]+)\]', bullet_text)
        if match:
            return match.group(1).replace(' ', '')
        
        return None
    
    def _normalize_query(self, query: str) -> str:
        """
        Normalize query for pattern matching
        
        Examples:
            "Dedektör yerleştirme kuralları nedir?" → "dedektör yerleştirme"
            "Isı dedektörü alan hesabı" → "isı dedektörü alan"
        """
        # Lowercase
        normalized = query.lower()
        
        # Remove common question words
        remove_words = ['nedir', 'nasıl', 'ne', 'nelerdir', 'kaç', 'hangi', 'kuralları', 'için']
        for word in remove_words:
            normalized = re.sub(r'\b' + word + r'\b', '', normalized)
        
        # Remove extra spaces
        normalized = ' '.join(normalized.split())
        
        # Take first 3-4 significant words
        words = normalized.split()[:4]
        
        return ' '.join(words).strip()
    
    def _update_relevance_score(self, query: str, source_ref: str, is_relevant: bool):
        """Update relevance score for query-chunk pair"""
        query_pattern = self._normalize_query(query)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get or create record
        cursor.execute("""
            SELECT relevant_count, irrelevant_count 
            FROM chunk_relevance_score
            WHERE query_pattern = ? AND source_ref = ?
        """, (query_pattern, source_ref))
        
        row = cursor.fetchone()
        
        if row:
            relevant_count, irrelevant_count = row
            if is_relevant:
                relevant_count += 1
            else:
                irrelevant_count += 1
        else:
            relevant_count = 1 if is_relevant else 0
            irrelevant_count = 0 if is_relevant else 1
        
        # Calculate relevance score
        total = relevant_count + irrelevant_count
        relevance_score = relevant_count / total if total > 0 else 0.5
        
        # Upsert
        cursor.execute("""
            INSERT INTO chunk_relevance_score 
            (query_pattern, source_ref, relevant_count, irrelevant_count, relevance_score, last_updated)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(query_pattern, source_ref) 
            DO UPDATE SET 
                relevant_count = ?,
                irrelevant_count = ?,
                relevance_score = ?,
                last_updated = ?
        """, (
            query_pattern, source_ref, relevant_count, irrelevant_count, relevance_score, datetime.now(),
            relevant_count, irrelevant_count, relevance_score, datetime.now()
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"📊 Updated relevance: {query_pattern} + {source_ref} = {relevance_score:.2%} ({relevant_count}✓/{irrelevant_count}✗)")
    
    def get_irrelevant_chunks(self, query: str, threshold: float = 0.3) -> List[str]:
        """
        Get chunks that are likely irrelevant for this query
        
        Args:
            query: User query
            threshold: Relevance score threshold (chunks below this are considered irrelevant)
            
        Returns:
            List of source references to penalize
        """
        query_pattern = self._normalize_query(query)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get chunks with low relevance score for similar queries
        cursor.execute("""
            SELECT source_ref, relevance_score, relevant_count, irrelevant_count
            FROM chunk_relevance_score
            WHERE query_pattern = ? AND relevance_score < ?
            ORDER BY relevance_score ASC
        """, (query_pattern, threshold))
        
        irrelevant = []
        for row in cursor.fetchall():
            source_ref, score, rel_count, irrel_count = row
            irrelevant.append(source_ref)
            logger.debug(f"  ⚠️ {source_ref}: {score:.1%} ({rel_count}✓/{irrel_count}✗)")
        
        conn.close()
        
        if irrelevant:
            logger.info(f"🚫 Found {len(irrelevant)} irrelevant chunks for '{query_pattern}'")
        
        return irrelevant
    
    def get_feedback_stats(self) -> Dict:
        """Get feedback statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total feedback
        cursor.execute("SELECT COUNT(*) FROM bullet_feedback")
        total = cursor.fetchone()[0]
        
        # Relevant vs irrelevant
        cursor.execute("SELECT COUNT(*) FROM bullet_feedback WHERE is_relevant = 1")
        relevant = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM bullet_feedback WHERE is_relevant = 0")
        irrelevant = cursor.fetchone()[0]
        
        # Unique queries
        cursor.execute("SELECT COUNT(DISTINCT query) FROM bullet_feedback")
        unique_queries = cursor.fetchone()[0]
        
        # Learned patterns
        cursor.execute("SELECT COUNT(*) FROM chunk_relevance_score")
        patterns = cursor.fetchone()[0]
        
        # Top irrelevant chunks
        cursor.execute("""
            SELECT source_ref, relevance_score, relevant_count, irrelevant_count
            FROM chunk_relevance_score
            WHERE irrelevant_count > 0
            ORDER BY relevance_score ASC
            LIMIT 10
        """)
        top_irrelevant = [
            {
                'source': row[0],
                'score': row[1],
                'relevant': row[2],
                'irrelevant': row[3]
            }
            for row in cursor.fetchall()
        ]
        
        conn.close()
        
        return {
            'total_feedback': total,
            'relevant': relevant,
            'irrelevant': irrelevant,
            'unique_queries': unique_queries,
            'learned_patterns': patterns,
            'top_irrelevant': top_irrelevant
        }


# Singleton instance
_bullet_feedback_manager: Optional[BulletFeedbackManager] = None


def get_bullet_feedback_manager() -> BulletFeedbackManager:
    """Get or create BulletFeedbackManager singleton"""
    global _bullet_feedback_manager
    if _bullet_feedback_manager is None:
        _bullet_feedback_manager = BulletFeedbackManager()
    return _bullet_feedback_manager


if __name__ == "__main__":
    # Test the manager
    manager = get_bullet_feedback_manager()
    
    print("\n=== Testing Bullet Feedback Manager ===\n")
    
    # Add some test feedback
    manager.add_feedback(
        response_id="resp_001",
        query="Dedektör yerleştirme kuralları nedir?",
        bullet_index=0,
        bullet_text="Isı dedektörleri için: Alan (m²) / 50 (IS 3218, 6.5.1.13)",
        is_relevant=True
    )
    
    manager.add_feedback(
        response_id="resp_001",
        query="Dedektör yerleştirme kuralları nedir?",
        bullet_index=1,
        bullet_text="Kablo kesit alanı 2.5mm² kullanılır (IS 3218, 8.2.1)",
        is_relevant=False  # Irrelevant!
    )
    
    manager.add_feedback(
        response_id="resp_002",
        query="Dedektör alan hesabı nasıl yapılır?",
        bullet_index=0,
        bullet_text="Duman dedektörleri için: Alan (m²) / 100 (IS 3218, 6.5.1.14)",
        is_relevant=True
    )
    
    # Get irrelevant chunks
    print("\n--- Irrelevant Chunks for 'Dedektör yerleştirme' ---")
    irrelevant = manager.get_irrelevant_chunks("Dedektör yerleştirme kuralları", threshold=0.5)
    print(f"Found {len(irrelevant)} irrelevant chunks: {irrelevant}")
    
    # Get stats
    print("\n--- Statistics ---")
    stats = manager.get_feedback_stats()
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    
    print("\n✅ Test completed!")
