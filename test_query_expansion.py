"""
Test Query Expansion functionality
"""

from src.query_expansion import QueryExpander
from src.utils import setup_logger
from loguru import logger


def test_expansion():
    """Test query expansion with various MEP terms"""
    setup_logger("INFO")
    
    logger.info("=" * 60)
    logger.info("QUERY EXPANSION TEST")
    logger.info("=" * 60)
    
    expander = QueryExpander(max_expansions=3)
    
    # Test cases
    test_queries = [
        # Electrical
        "kablo kapasitesi nedir?",
        "What is the current carrying capacity?",
        "Cable sizing for installation",
        "Topraklama direnci",
        
        # Fire Safety
        "Fire alarm requirements",
        "Yangın algılama sistemi",
        "Smoke detector placement",
        
        # UPS and Power
        "UPS system specifications",
        "Generator capacity",
        "Emergency power supply",
        
        # Lighting
        "Lighting levels required",
        "Aydınlatma seviyesi",
        "Luminaire selection",
        
        # HVAC
        "HVAC system design",
        "Havalandırma gereksinimleri",
        
        # Standards
        "Standard compliance requirements",
        "Şartname gereklilikleri",
    ]
    
    logger.info("\n🔍 Testing query expansion:\n")
    
    for query in test_queries:
        expanded = expander.expand(query)
        if expanded != query:
            logger.success(f"✅ '{query}'")
            logger.info(f"   → '{expanded}'")
        else:
            logger.info(f"⚪ '{query}' (no expansion)")
    
    # Test synonym lookup
    logger.info("\n📚 Testing synonym lookup:\n")
    
    test_terms = ["cable", "kablo", "ups", "fire alarm", "topraklama"]
    for term in test_terms:
        synonyms = expander.get_synonyms(term)
        logger.info(f"'{term}' → {synonyms[:5]}...")  # Show first 5
    
    logger.info("\n" + "=" * 60)
    logger.info("TEST COMPLETE")
    logger.info("=" * 60)


if __name__ == "__main__":
    test_expansion()
