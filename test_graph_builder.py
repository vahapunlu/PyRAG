"""
Test Graph Builder

Build knowledge graph from Vector Store
"""

from src.graph_builder import build_graph_from_store
from loguru import logger

if __name__ == "__main__":
    logger.info("🧪 Testing Graph Builder...")
    
    # Build graph from Vector Store (clear existing data first)
    stats = build_graph_from_store(
        collection_name="engineering_standards",
        clear_existing=True  # Start fresh
    )
    
    logger.success(f"✅ Test completed!")
    logger.info(f"📊 Final statistics: {stats}")
