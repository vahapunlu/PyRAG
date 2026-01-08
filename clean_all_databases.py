"""
Complete Database Cleanup Script

Clears Qdrant and Neo4j Aura databases completely.
"""

import shutil
from pathlib import Path
from loguru import logger
import os
from src.utils import get_settings
from src.graph_manager import GraphManager

def clean_qdrant():
    """Clear Qdrant completely by removing local storage folder"""
    try:
        settings = get_settings()
        logger.info("🗑️  Cleaning Qdrant...")
        
        qdrant_path = Path(settings.qdrant_path)
        
        if not qdrant_path.exists():
            logger.info("   ℹ️  Qdrant folder doesn't exist")
            return
        
        # Count collections before deletion
        collection_path = qdrant_path / "collection"
        collection_count = 0
        if collection_path.exists():
            collection_count = len(list(collection_path.iterdir()))
        
        # Remove entire Qdrant folder
        shutil.rmtree(qdrant_path)
        
        logger.success(f"✅ Qdrant cleaned! Removed folder with {collection_count} collection(s)")
        
    except Exception as e:
        logger.error(f"❌ Qdrant cleanup error: {e}")
        raise

def clean_neo4j():
    """Clear Neo4j Aura completely"""
    try:
        logger.info("🗑️  Cleaning Neo4j Aura...")
        
        # Read Neo4j credentials from .env.neo4j
        env_file = Path('.env.neo4j')
        if not env_file.exists():
            logger.warning("   ⚠️  .env.neo4j not found, skipping Neo4j cleanup")
            return
        
        credentials = {}
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    credentials[key] = value
        
        if not all(k in credentials for k in ['NEO4J_URI', 'NEO4J_USERNAME', 'NEO4J_PASSWORD']):
            logger.warning("   ⚠️  Neo4j credentials incomplete, skipping cleanup")
            return
        
        # Connect to Neo4j
        graph_manager = GraphManager(
            uri=credentials['NEO4J_URI'],
            username=credentials['NEO4J_USERNAME'],
            password=credentials['NEO4J_PASSWORD']
        )
        
        # Delete all nodes and relationships
        query = """
        MATCH (n)
        DETACH DELETE n
        """
        
        result = graph_manager.driver.execute_query(query)
        
        # Get statistics
        stats_query = """
        MATCH (n)
        RETURN count(n) as node_count
        """
        
        stats = graph_manager.driver.execute_query(stats_query)
        remaining_nodes = stats.records[0]["node_count"]
        
        if remaining_nodes == 0:
            logger.success("✅ Neo4j Aura cleaned! All nodes and relationships deleted")
        else:
            logger.warning(f"⚠️  Warning: {remaining_nodes} nodes still remain")
        
        graph_manager.close()
        
    except Exception as e:
        # Neo4j may be offline/unreachable; do not fail the entire cleanup.
        logger.warning(f"⚠️  Neo4j cleanup skipped (unavailable): {e}")
        return

def clean_cache_databases():
    """Clean all cache databases (semantic cache, response cache, feedback)"""
    try:
        logger.info("🗑️  Cleaning cache databases...")
        
        cache_files = [
            Path("cache_db/semantic_cache.db"),
            Path("cache_db/response_cache.db"),
            Path("feedback_db/feedback.db"),
            Path("history_db/query_history.db")
        ]
        
        deleted = 0
        for cache_file in cache_files:
            if cache_file.exists():
                cache_file.unlink()
                logger.info(f"   🗑️  Deleted: {cache_file}")
                deleted += 1
        
        if deleted > 0:
            logger.success(f"✅ Cleaned {deleted} cache database(s)")
        else:
            logger.info("   ℹ️  No cache databases to clean")
            
    except Exception as e:
        logger.error(f"❌ Cache cleanup error: {e}")
        raise

def main():
    """Run complete cleanup"""
    print("=" * 60)
    print("🧹 COMPLETE DATABASE CLEANUP")
    print("=" * 60)
    print("\n🚀 Cleaning ALL databases...")
    print("\n" + "=" * 60)
    
    # Clean Qdrant
    clean_qdrant()
    print()
    
    # Clean Neo4j (best-effort)
    clean_neo4j()
    print()
    
    # Clean cache databases
    clean_cache_databases()
    print()
    
    print("=" * 60)
    logger.success("🎉 CLEANUP COMPLETE!")
    print("=" * 60)
    print("\n✅ You can now re-index your documents fresh.")
    print("   (Neo4j cleanup is best-effort and may be skipped if unreachable.)\n")

if __name__ == "__main__":
    main()
