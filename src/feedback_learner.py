"""
Feedback Learner

Learns from user feedback to create dynamic relationships in knowledge graph.
Analyzes positive feedback patterns and strengthens relevant connections.
"""

from typing import List, Dict, Tuple, Optional, Set
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from loguru import logger
import json

from .feedback_manager import get_feedback_manager
from .graph_manager import get_graph_manager


class FeedbackLearner:
    """
    Learns from user feedback to dynamically improve knowledge graph
    
    Features:
    - Co-occurrence analysis: Finds documents/standards frequently used together
    - Pattern detection: Identifies successful query-answer patterns
    - Dynamic relationship creation: Adds new edges to knowledge graph
    - Relationship strengthening: Increases weight of successful connections
    """
    
    def __init__(
        self,
        min_confidence: float = 0.6,
        min_support: int = 3,
        learning_rate: float = 0.1,
        decay_days: int = 30
    ):
        """
        Initialize feedback learner
        
        Args:
            min_confidence: Minimum confidence score for creating relationships (0-1)
            min_support: Minimum number of co-occurrences needed
            learning_rate: Weight increment for relationship strengthening
            decay_days: Days after which old feedback has less influence
        """
        self.min_confidence = min_confidence
        self.min_support = min_support
        self.learning_rate = learning_rate
        self.decay_days = decay_days
        
        self.feedback_manager = get_feedback_manager()
        self.graph_manager = get_graph_manager()
        
        logger.info(f"✅ Feedback Learner initialized (confidence≥{min_confidence}, support≥{min_support})")
    
    def learn_from_feedback(self, time_window_days: Optional[int] = None) -> Dict:
        """
        Main learning process: analyze feedback and update graph
        
        Args:
            time_window_days: Only consider feedback from last N days (None = all time)
            
        Returns:
            Statistics about learning process
        """
        logger.info("🧠 Starting feedback learning process...")
        
        stats = {
            'analyzed_feedback': 0,
            'new_relationships': 0,
            'strengthened_relationships': 0,
            'discovered_patterns': 0,
            'timestamp': datetime.now().isoformat()
        }
        
        # Step 1: Get positive feedback
        positive_feedback = self._get_positive_feedback(time_window_days)
        stats['analyzed_feedback'] = len(positive_feedback)
        
        if not positive_feedback:
            logger.warning("⚠️ No positive feedback found to learn from")
            return stats
        
        logger.info(f"   Analyzing {len(positive_feedback)} positive feedback entries")
        
        # Step 2: Analyze co-occurrences
        co_occurrences = self._analyze_co_occurrences(positive_feedback)
        logger.info(f"   Found {len(co_occurrences)} document co-occurrence patterns")
        
        # Step 3: Create/strengthen relationships
        for (doc1, doc2), confidence in co_occurrences.items():
            if confidence >= self.min_confidence:
                created = self._create_or_strengthen_relationship(
                    doc1, doc2, confidence, 'COMPLEMENTS'
                )
                if created:
                    stats['new_relationships'] += 1
                else:
                    stats['strengthened_relationships'] += 1
        
        # Step 4: Detect query patterns
        patterns = self._detect_query_patterns(positive_feedback)
        stats['discovered_patterns'] = len(patterns)
        logger.info(f"   Discovered {len(patterns)} successful query patterns")
        
        # Step 5: Create semantic relationships
        semantic_rels = self._create_semantic_relationships(patterns)
        stats['new_relationships'] += semantic_rels
        
        logger.success(f"✅ Learning complete! Created {stats['new_relationships']} new relationships, "
                      f"strengthened {stats['strengthened_relationships']} existing ones")
        
        return stats
    
    def _get_positive_feedback(self, time_window_days: Optional[int] = None) -> List[Dict]:
        """
        Retrieve positive feedback from database
        
        Args:
            time_window_days: Time window in days
            
        Returns:
            List of positive feedback entries with parsed sources
        """
        import sqlite3
        
        conn = sqlite3.connect(self.feedback_manager.db_path)
        cursor = conn.cursor()
        
        if time_window_days:
            cutoff_date = (datetime.now() - timedelta(days=time_window_days)).isoformat()
            cursor.execute("""
                SELECT query, response, source_documents, metadata, timestamp
                FROM feedback
                WHERE feedback_type = 'positive' AND timestamp >= ?
                ORDER BY timestamp DESC
            """, (cutoff_date,))
        else:
            cursor.execute("""
                SELECT query, response, source_documents, metadata, timestamp
                FROM feedback
                WHERE feedback_type = 'positive'
                ORDER BY timestamp DESC
            """)
        
        results = []
        for row in cursor.fetchall():
            query, response, sources_json, metadata_json, timestamp = row
            
            try:
                sources = json.loads(sources_json) if sources_json else []
                metadata = json.loads(metadata_json) if metadata_json else {}
                
                results.append({
                    'query': query,
                    'response': response,
                    'sources': sources,
                    'metadata': metadata,
                    'timestamp': timestamp
                })
            except json.JSONDecodeError:
                continue
        
        conn.close()
        return results
    
    def _analyze_co_occurrences(self, feedback_list: List[Dict]) -> Dict[Tuple[str, str], float]:
        """
        Analyze which documents frequently appear together in successful responses
        
        Args:
            feedback_list: List of positive feedback entries
            
        Returns:
            Dict of {(doc1, doc2): confidence_score}
        """
        # Count document pairs
        pair_counts = Counter()
        doc_counts = Counter()
        
        for feedback in feedback_list:
            sources = feedback.get('sources', [])
            doc_names = set()
            
            # Extract unique document names
            for source in sources:
                if isinstance(source, dict):
                    doc_name = source.get('document_name') or source.get('metadata', {}).get('document_name')
                    if doc_name:
                        doc_names.add(doc_name)
            
            # Count individual documents
            for doc in doc_names:
                doc_counts[doc] += 1
            
            # Count pairs (sorted to avoid duplicates)
            doc_list = sorted(doc_names)
            for i in range(len(doc_list)):
                for j in range(i + 1, len(doc_list)):
                    pair_counts[(doc_list[i], doc_list[j])] += 1
        
        # Calculate confidence scores
        co_occurrences = {}
        for (doc1, doc2), pair_count in pair_counts.items():
            if pair_count >= self.min_support:
                # Confidence = P(doc2|doc1) and P(doc1|doc2) averaged
                # Using Jaccard similarity-like metric
                max_single = max(doc_counts[doc1], doc_counts[doc2])
                confidence = pair_count / max_single if max_single > 0 else 0
                
                if confidence >= self.min_confidence:
                    co_occurrences[(doc1, doc2)] = confidence
        
        return co_occurrences
    
    def _create_or_strengthen_relationship(
        self,
        doc1: str,
        doc2: str,
        confidence: float,
        rel_type: str = 'COMPLEMENTS'
    ) -> bool:
        """
        Create new relationship or strengthen existing one
        
        Args:
            doc1: First document name
            doc2: Second document name
            confidence: Confidence score
            rel_type: Relationship type
            
        Returns:
            True if new relationship created, False if strengthened
        """
        if not self.graph_manager:
            logger.warning("⚠️ Graph manager not available")
            return False
        
        # Check if relationship exists
        existing_weight = self.graph_manager.get_relationship_weight(doc1, doc2, rel_type)
        
        if existing_weight is None:
            # Create new relationship
            self.graph_manager.create_learned_relationship(
                doc1, doc2, rel_type, confidence
            )
            logger.info(f"   ➕ Created: ({doc1})-[{rel_type}]->({doc2}) [weight={confidence:.2f}]")
            return True
        else:
            # Strengthen existing relationship
            new_weight = min(1.0, existing_weight + (confidence * self.learning_rate))
            self.graph_manager.update_relationship_weight(
                doc1, doc2, rel_type, new_weight
            )
            logger.debug(f"   ⬆️ Strengthened: ({doc1})-[{rel_type}]->({doc2}) [{existing_weight:.2f} → {new_weight:.2f}]")
            return False
    
    def _detect_query_patterns(self, feedback_list: List[Dict]) -> List[Dict]:
        """
        Detect common query patterns in successful responses
        
        Args:
            feedback_list: List of positive feedback entries
            
        Returns:
            List of pattern dictionaries
        """
        patterns = []
        query_keywords = defaultdict(list)
        
        for feedback in feedback_list:
            query = feedback.get('query', '').lower()
            sources = feedback.get('sources', [])
            
            # Extract keywords (simple tokenization)
            keywords = [word for word in query.split() if len(word) > 3]
            
            for keyword in keywords:
                query_keywords[keyword].append({
                    'query': query,
                    'sources': sources
                })
        
        # Find frequent patterns
        for keyword, occurrences in query_keywords.items():
            if len(occurrences) >= self.min_support:
                # Find most common documents for this keyword
                doc_counter = Counter()
                for occ in occurrences:
                    for source in occ['sources']:
                        if isinstance(source, dict):
                            doc_name = source.get('document_name') or source.get('metadata', {}).get('document_name')
                            if doc_name:
                                doc_counter[doc_name] += 1
                
                if doc_counter:
                    top_doc = doc_counter.most_common(1)[0]
                    confidence = top_doc[1] / len(occurrences)
                    
                    if confidence >= self.min_confidence:
                        patterns.append({
                            'keyword': keyword,
                            'document': top_doc[0],
                            'confidence': confidence,
                            'support': len(occurrences)
                        })
        
        return patterns
    
    def _create_semantic_relationships(self, patterns: List[Dict]) -> int:
        """
        Create semantic relationships based on query patterns
        
        Args:
            patterns: Detected query patterns
            
        Returns:
            Number of relationships created
        """
        created = 0
        
        # Group patterns by similar keywords
        keyword_groups = defaultdict(set)
        for pattern in patterns:
            keyword = pattern['keyword']
            doc = pattern['document']
            keyword_groups[keyword].add(doc)
        
        # Create RELATED_TO relationships between documents sharing keywords
        for keyword, docs in keyword_groups.items():
            if len(docs) >= 2:
                doc_list = sorted(docs)
                for i in range(len(doc_list)):
                    for j in range(i + 1, len(doc_list)):
                        if self.graph_manager:
                            existing = self.graph_manager.get_relationship_weight(
                                doc_list[i], doc_list[j], 'RELATED_TO'
                            )
                            if existing is None:
                                self.graph_manager.create_learned_relationship(
                                    doc_list[i], doc_list[j], 'RELATED_TO', 0.5
                                )
                                created += 1
        
        return created
    
    def get_learning_statistics(self) -> Dict:
        """
        Get statistics about learned relationships
        
        Returns:
            Statistics dictionary
        """
        if not self.graph_manager:
            return {}
        
        stats = self.graph_manager.get_learned_relationship_stats()
        return stats
    
    def prune_weak_relationships(self, min_weight: float = 0.3) -> int:
        """
        Remove learned relationships with low weights
        
        Args:
            min_weight: Minimum weight threshold
            
        Returns:
            Number of relationships removed
        """
        if not self.graph_manager:
            return 0
        
        removed = self.graph_manager.prune_learned_relationships(min_weight)
        logger.info(f"🗑️ Pruned {removed} weak relationships (weight < {min_weight})")
        return removed


# Singleton pattern
_feedback_learner = None

def get_feedback_learner() -> Optional[FeedbackLearner]:
    """Get global feedback learner instance"""
    global _feedback_learner
    if _feedback_learner is None:
        try:
            _feedback_learner = FeedbackLearner()
        except Exception as e:
            logger.error(f"❌ Failed to initialize feedback learner: {e}")
            return None
    return _feedback_learner
