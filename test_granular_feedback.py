"""
Test Granular Feedback System

Demonstrates different types of fine-grained feedback.
"""

from loguru import logger
from src.granular_feedback import get_granular_feedback_manager


def test_source_level_feedback():
    """Test source-specific feedback"""
    logger.info("\n" + "="*60)
    logger.info("TEST 1: Source-Level Feedback")
    logger.info("="*60)
    
    manager = get_granular_feedback_manager()
    
    # Simulate user rating different sources
    feedback_id = manager.add_feedback(
        query="Kablo seçimi nasıl yapılır?",
        response="Kablo seçimi IS 3218 ve NEK 606'ya göre yapılır...",
        overall_rating=4,
        source_feedbacks=[
            {
                "document": "IS3218",
                "page": "15",
                "rating": "helpful",
                "stars": 5,
                "comment": "Çok detaylı ve net açıklama"
            },
            {
                "document": "NEK606",
                "page": "8",
                "rating": "not_helpful",
                "stars": 2,
                "comment": "Konuyla alakasız gibi görünüyor"
            },
            {
                "document": "EN54-11",
                "page": "5",
                "rating": "irrelevant",
                "stars": 1,
                "comment": "Bu standardın bu soruyla alakası yok"
            }
        ],
        comment="Genel olarak iyi ama bazı kaynaklar gereksiz"
    )
    
    logger.success(f"✅ Feedback ID: {feedback_id}")


def test_text_highlights():
    """Test text selection/highlight feedback"""
    logger.info("\n" + "="*60)
    logger.info("TEST 2: Text Highlight Feedback")
    logger.info("="*60)
    
    manager = get_granular_feedback_manager()
    
    # User highlights useful parts of the response
    feedback_id = manager.add_feedback(
        query="Yangın alarm kablosu özellikleri nedir?",
        response="Yangın alarm kabloları EN 54-11 standardına uygun olmalıdır. "
                 "Kablo kesiti minimum 1.5mm² olmalıdır. "
                 "Yangın direnci 90 dakika olmalıdır.",
        overall_rating=5,
        highlights=[
            {
                "text": "EN 54-11 standardına uygun olmalıdır",
                "sentiment": "positive",
                "source": "EN54-11",
                "comment": "Tam aradığım bilgi"
            },
            {
                "text": "Kablo kesiti minimum 1.5mm² olmalıdır",
                "sentiment": "positive",
                "source": "IS3218",
                "comment": "Net ve açık"
            }
        ]
    )
    
    logger.success(f"✅ Feedback with {2} highlights added")


def test_multi_dimensional_ratings():
    """Test multi-dimensional feedback"""
    logger.info("\n" + "="*60)
    logger.info("TEST 3: Multi-Dimensional Ratings")
    logger.info("="*60)
    
    manager = get_granular_feedback_manager()
    
    feedback_id = manager.add_feedback(
        query="Topraklama nasıl yapılmalı?",
        response="Topraklama NEK 606'ya göre yapılmalıdır...",
        overall_rating=4,
        dimensions={
            "relevance": 5,      # Soruyla alakalı mı?
            "clarity": 3,        # Açık ve anlaşılır mı?
            "completeness": 4    # Eksiksiz mi?
        },
        comment="İlgili ve doğru ama biraz daha açık olabilirdi"
    )
    
    logger.success(f"✅ Multi-dimensional feedback added")


def test_quality_scores():
    """Test aggregated quality scores"""
    logger.info("\n" + "="*60)
    logger.info("TEST 4: Source Quality Scores")
    logger.info("="*60)
    
    # Add more feedback
    manager = get_granular_feedback_manager()
    
    # Multiple users rating IS3218 positively
    for i in range(5):
        manager.add_feedback(
            query=f"Test query {i}",
            response="Test response",
            source_feedbacks=[
                {"document": "IS3218", "rating": "helpful", "stars": 5}
            ]
        )
    
    # Some negative for NEK606
    for i in range(3):
        manager.add_feedback(
            query=f"Test query {i}",
            response="Test response",
            source_feedbacks=[
                {"document": "NEK606", "rating": "not_helpful", "stars": 2}
            ]
        )
    
    # Get quality scores
    scores = manager.get_source_quality_scores()
    
    logger.info("\n📊 Source Quality Scores:")
    for doc, data in sorted(scores.items(), key=lambda x: x[1]['quality_score'], reverse=True):
        logger.info(f"\n   {doc}:")
        logger.info(f"      Quality Score: {data['quality_score']:.1f}/100")
        logger.info(f"      Avg Rating: {data['avg_rating']:.1f}/5")
        logger.info(f"      Helpful: {data['helpful_count']}")
        logger.info(f"      Not Helpful: {data['not_helpful_count']}")
        logger.info(f"      Irrelevant: {data['irrelevant_count']}")


def test_best_sources():
    """Test getting best sources"""
    logger.info("\n" + "="*60)
    logger.info("TEST 5: Best Rated Sources")
    logger.info("="*60)
    
    manager = get_granular_feedback_manager()
    best = manager.get_best_sources(limit=5)
    
    logger.info("\n🏆 Top 5 Sources:")
    for i, source in enumerate(best, 1):
        logger.info(f"\n   {i}. {source['document']}")
        logger.info(f"      Quality: {source['quality_score']:.1f}/100")
        logger.info(f"      Avg Rating: {source['avg_rating']:.1f}/5")
        logger.info(f"      Total Feedbacks: {source['total_feedbacks']}")


def test_highlighted_snippets():
    """Test frequently highlighted snippets"""
    logger.info("\n" + "="*60)
    logger.info("TEST 6: Popular Highlighted Snippets")
    logger.info("="*60)
    
    manager = get_granular_feedback_manager()
    snippets = manager.get_highlighted_snippets(limit=5)
    
    if snippets:
        logger.info("\n✨ Most Highlighted Snippets:")
        for snippet in snippets:
            logger.info(f"\n   \"{snippet['text'][:60]}...\"")
            logger.info(f"      Source: {snippet['source']}")
            logger.info(f"      Frequency: {snippet['frequency']} times")
    else:
        logger.info("   No highlights yet")


def test_statistics():
    """Test overall statistics"""
    logger.info("\n" + "="*60)
    logger.info("TEST 7: Overall Statistics")
    logger.info("="*60)
    
    manager = get_granular_feedback_manager()
    stats = manager.get_statistics()
    
    logger.info("\n📈 Statistics:")
    logger.info(f"   Total Feedbacks: {stats['total_feedbacks']}")
    logger.info(f"   Avg Overall Rating: {stats['avg_overall_rating']:.1f}/5")
    logger.info(f"\n   Source Feedback Breakdown:")
    logger.info(f"      Total: {stats['source_feedbacks']['total']}")
    logger.info(f"      Helpful: {stats['source_feedbacks']['helpful']}")
    logger.info(f"      Not Helpful: {stats['source_feedbacks']['not_helpful']}")
    logger.info(f"      Irrelevant: {stats['source_feedbacks']['irrelevant']}")
    logger.info(f"\n   Total Highlights: {stats['total_highlights']}")


def main():
    """Run all tests"""
    logger.info("\n" + "🧪"*30)
    logger.info("GRANULAR FEEDBACK SYSTEM TEST")
    logger.info("🧪"*30 + "\n")
    
    try:
        test_source_level_feedback()
        test_text_highlights()
        test_multi_dimensional_ratings()
        test_quality_scores()
        test_best_sources()
        test_highlighted_snippets()
        test_statistics()
        
        logger.success("\n" + "="*60)
        logger.success("✅ ALL TESTS COMPLETED")
        logger.success("="*60)
        
    except Exception as e:
        logger.error(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
