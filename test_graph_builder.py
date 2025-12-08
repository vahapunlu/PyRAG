"""
Test Graph Builder

Build knowledge graph from IS3218 2024 in ChromaDB
"""

from src.graph_builder import build_graph_from_chroma
from loguru import logger

if __name__ == "__main__":
    logger.info("🧪 Testing Graph Builder with IS3218 2024...")
    
    # Build graph from ChromaDB (clear existing data first)
    stats = build_graph_from_chroma(
        chroma_path="./chroma_db",
        collection_name="engineering_standards",
        clear_existing=True  # Start fresh
    )
    
    logger.success(f"✅ Test completed!")
    logger.info(f"📊 Final statistics: {stats}")
