"""
Rebuild Neo4j Graph from Existing Vector Store

This script rebuilds the Neo4j knowledge graph without re-ingesting documents.
It reads existing chunks from Vector Store (Qdrant/Chroma) and recreates section nodes.
"""

from src.graph_builder import GraphBuilder
from src.utils import setup_logger
from loguru import logger
import sys

def main():
    """Rebuild graph from existing Vector Store data"""
    setup_logger()
    
    logger.info("=" * 80)
    logger.info("🔄 Neo4j Graph Rebuild")
    logger.info("=" * 80)
    logger.info("")
    logger.info("This will:")
    logger.info("  1. Clear existing Neo4j graph")
    logger.info("  2. Read chunks from Vector Store (NO re-ingestion)")
    logger.info("  3. Recreate sections with improved patterns")
    logger.info("  4. Rebuild all relationships")
    logger.info("")
    logger.info("⚠️  Vector Store data will NOT be touched!")
    logger.info("")
    
    try:
        # Initialize graph builder with default paths
        from src.utils import get_settings
        settings = get_settings()
        
        collection_name = settings.get_collection_name()
        
        logger.info(f"🗄️  Vector Store: {settings.vector_store_type}")
        logger.info(f"📚 Collection: {collection_name}")
        logger.info("")
        
        # Initialize graph builder
        builder = GraphBuilder(collection_name=collection_name)
        
        # Build from existing index
        logger.info("🔧 Starting graph rebuild...")
        logger.info("")
        
        stats = builder.build_graph(clear_existing=True)
        
        # Display results
        logger.success("")
        logger.success("=" * 80)
        logger.success("✅ Graph Rebuild Complete!")
        logger.success("=" * 80)
        logger.success(f"📄 Documents: {stats.get('documents', 0)}")
        logger.success(f"📑 Sections: {stats.get('sections', 0)}")
        logger.success(f"📘 Standards: {stats.get('standards', 0)}")
        logger.success(f"🔗 Relationships: {stats.get('relationships', 0)}")
        logger.success("")
        
        # Compare before/after
        logger.info("💡 Expected improvements:")
        logger.info("   • IS10101: 7 → ~100+ sections")
        logger.info("   • EDC PARTICULAR: 0 → ~20+ sections")
        logger.info("   • Better Annex/Table/Figure detection")
        logger.info("")
        
    except Exception as e:
        logger.error(f"❌ Rebuild failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
