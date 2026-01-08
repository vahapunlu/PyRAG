"""
Test Feedback Learning System

Tests the new feedback-based learning system that creates dynamic relationships.
"""

from loguru import logger
from src.feedback_learner import get_feedback_learner
from src.feedback_manager import get_feedback_manager
from src.graph_manager import get_graph_manager
import json


def setup_test_feedback():
    """Create some test feedback data"""
    feedback_manager = get_feedback_manager()
    
    # Test scenario: Users frequently ask about cable selection
    # and the system uses IS 3218 and NEK 606 together successfully
    
    test_feedbacks = [
        {
            'query': 'kablo seçimi nasıl yapılır?',
            'response': 'Kablo seçimi IS 3218 ve NEK 606 standartlarına göre yapılmalıdır...',
            'sources': [
                {'document_name': 'IS3218', 'page': '15', 'text': 'Kablo seçim kriterleri...'},
                {'document_name': 'NEK606', 'page': '8', 'text': 'Elektrik tesisatı kuralları...'}
            ]
        },
        {
            'query': 'elektrik tesisatında kablo tipi nasıl belirlenir?',
            'response': 'IS 3218 ve NEK 606 standartları birlikte kullanılmalıdır...',
            'sources': [
                {'document_name': 'IS3218', 'page': '20', 'text': 'Kablo tipleri...'},
                {'document_name': 'NEK606', 'page': '12', 'text': 'Tesisat kuralları...'}
            ]
        },
        {
            'query': 'yangın alarm kablosu hangi standarda uygun olmalı?',
            'response': 'EN 54-11 ve IS 3218 standartlarını kontrol edin...',
            'sources': [
                {'document_name': 'EN54-11', 'page': '5', 'text': 'Yangın alarm kabloları...'},
                {'document_name': 'IS3218', 'page': '30', 'text': 'Yangın direnci...'}
            ]
        },
        {
            'query': 'kablo kesiti nasıl hesaplanır?',
            'response': 'IS 3218 standardına göre hesaplama yapılır...',
            'sources': [
                {'document_name': 'IS3218', 'page': '25', 'text': 'Kesit hesaplama...'},
                {'document_name': 'NEK606', 'page': '18', 'text': 'Akım taşıma kapasitesi...'}
            ]
        },
        {
            'query': 'topraklama nasıl yapılmalı?',
            'response': 'NEK 606 ve IS 10101 standartlarına göre yapılmalıdır...',
            'sources': [
                {'document_name': 'NEK606', 'page': '25', 'text': 'Topraklama kuralları...'},
                {'document_name': 'IS10101', 'page': '10', 'text': 'Koruma önlemleri...'}
            ]
        }
    ]
    
    logger.info("📝 Creating test feedback data...")
    
    for fb in test_feedbacks:
        feedback_manager.add_feedback(
            query=fb['query'],
            response=fb['response'],
            feedback_type='positive',
            sources=fb['sources'],
            comment='Test feedback'
        )
    
    logger.success(f"✅ Created {len(test_feedbacks)} positive feedback entries")


def test_co_occurrence_analysis():
    """Test co-occurrence analysis"""
    logger.info("\n" + "="*60)
    logger.info("TEST 1: Co-occurrence Analysis")
    logger.info("="*60)
    
    learner = get_feedback_learner()
    feedback_list = learner._get_positive_feedback()
    
    logger.info(f"📊 Analyzing {len(feedback_list)} positive feedback entries")
    
    co_occurrences = learner._analyze_co_occurrences(feedback_list)
    
    logger.info(f"\n📈 Found {len(co_occurrences)} document co-occurrence patterns:")
    for (doc1, doc2), confidence in sorted(co_occurrences.items(), key=lambda x: x[1], reverse=True):
        logger.info(f"   • {doc1} ↔ {doc2}: {confidence:.2%} confidence")
    
    return co_occurrences


def test_pattern_detection():
    """Test query pattern detection"""
    logger.info("\n" + "="*60)
    logger.info("TEST 2: Query Pattern Detection")
    logger.info("="*60)
    
    learner = get_feedback_learner()
    feedback_list = learner._get_positive_feedback()
    
    patterns = learner._detect_query_patterns(feedback_list)
    
    logger.info(f"\n🔍 Discovered {len(patterns)} query patterns:")
    for pattern in sorted(patterns, key=lambda x: x['confidence'], reverse=True):
        logger.info(f"   • Keyword: '{pattern['keyword']}'")
        logger.info(f"     → Document: {pattern['document']}")
        logger.info(f"     → Confidence: {pattern['confidence']:.2%}")
        logger.info(f"     → Support: {pattern['support']} queries")
    
    return patterns


def test_full_learning():
    """Test complete learning process"""
    logger.info("\n" + "="*60)
    logger.info("TEST 3: Full Learning Process")
    logger.info("="*60)
    
    learner = get_feedback_learner()
    
    # Run learning
    stats = learner.learn_from_feedback(time_window_days=None)
    
    logger.info("\n📊 Learning Results:")
    logger.info(f"   ✅ Analyzed feedback: {stats['analyzed_feedback']}")
    logger.info(f"   ➕ New relationships: {stats['new_relationships']}")
    logger.info(f"   ⬆️ Strengthened relationships: {stats['strengthened_relationships']}")
    logger.info(f"   🔍 Patterns discovered: {stats['discovered_patterns']}")
    
    return stats


def test_graph_relationships():
    """Test created relationships in graph"""
    logger.info("\n" + "="*60)
    logger.info("TEST 4: Inspect Graph Relationships")
    logger.info("="*60)
    
    graph_manager = get_graph_manager()
    
    if not graph_manager:
        logger.warning("⚠️ Graph manager not available")
        return
    
    # Get learned relationship statistics
    stats = graph_manager.get_learned_relationship_stats()
    
    logger.info("\n📊 Learned Relationship Statistics:")
    logger.info(f"   Total learned relationships: {stats.get('total_learned', 0)}")
    logger.info(f"   Average weight: {stats.get('avg_weight', 0):.2f}")
    logger.info(f"   Max weight: {stats.get('max_weight', 0):.2f}")
    logger.info(f"   Min weight: {stats.get('min_weight', 0):.2f}")
    logger.info(f"   Relationship types: {stats.get('relationship_types', 0)}")
    
    # Test related documents query
    test_docs = ['IS3218', 'NEK606', 'EN54-11']
    
    logger.info("\n🔗 Related Documents:")
    for doc in test_docs:
        related = graph_manager.get_related_documents(doc, min_weight=0.3)
        if related:
            logger.info(f"\n   {doc}:")
            for rel in related[:5]:  # Top 5
                logger.info(f"      → {rel['document']} "
                          f"[{rel['relationship_type']}] "
                          f"(weight: {rel['weight']:.2f}, "
                          f"learned: {rel.get('learned', False)})")
        else:
            logger.info(f"\n   {doc}: No related documents found")


def test_pruning():
    """Test relationship pruning"""
    logger.info("\n" + "="*60)
    logger.info("TEST 5: Relationship Pruning")
    logger.info("="*60)
    
    learner = get_feedback_learner()
    
    # Prune weak relationships
    removed = learner.prune_weak_relationships(min_weight=0.2)
    
    logger.info(f"\n🗑️ Pruned {removed} weak relationships (weight < 0.2)")


def test_incremental_learning():
    """Test that learning strengthens existing relationships"""
    logger.info("\n" + "="*60)
    logger.info("TEST 6: Incremental Learning")
    logger.info("="*60)
    
    graph_manager = get_graph_manager()
    learner = get_feedback_learner()
    
    if not graph_manager:
        logger.warning("⚠️ Graph manager not available")
        return
    
    # Check initial weight
    initial_weight = graph_manager.get_relationship_weight('IS3218', 'NEK606', 'COMPLEMENTS')
    logger.info(f"Initial weight (IS3218 → NEK606): {initial_weight}")
    
    # Add more positive feedback
    feedback_manager = get_feedback_manager()
    feedback_manager.add_feedback(
        query='kablo seçimi test',
        response='Test response',
        feedback_type='positive',
        sources=[
            {'document_name': 'IS3218', 'page': '1', 'text': 'test'},
            {'document_name': 'NEK606', 'page': '1', 'text': 'test'}
        ]
    )
    
    # Run learning again
    learner.learn_from_feedback()
    
    # Check updated weight
    updated_weight = graph_manager.get_relationship_weight('IS3218', 'NEK606', 'COMPLEMENTS')
    logger.info(f"Updated weight (IS3218 → NEK606): {updated_weight}")
    
    if updated_weight and initial_weight:
        if updated_weight > initial_weight:
            logger.success(f"✅ Weight increased by {updated_weight - initial_weight:.4f}")
        else:
            logger.info(f"Weight remained same or decreased")


def main():
    """Run all tests"""
    logger.info("\n" + "🧪"*30)
    logger.info("FEEDBACK LEARNING SYSTEM TEST")
    logger.info("🧪"*30 + "\n")
    
    try:
        # Setup test data
        setup_test_feedback()
        
        # Run tests
        test_co_occurrence_analysis()
        test_pattern_detection()
        test_full_learning()
        test_graph_relationships()
        test_incremental_learning()
        test_pruning()
        
        logger.success("\n" + "="*60)
        logger.success("✅ ALL TESTS COMPLETED")
        logger.success("="*60)
        
    except Exception as e:
        logger.error(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
