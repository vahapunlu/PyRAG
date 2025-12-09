"""
Complete Database Cleanup Script

Clears both ChromaDB and Neo4j Aura databases completely.
"""

import chromadb
from chromadb.config import Settings as ChromaSettings
from pathlib import Path
from loguru import logger
import os
from src.utils import get_settings
from src.graph_manager import GraphManager

def clean_chromadb():
    """Clear ChromaDB completely"""
    try:
        settings = get_settings()
        logger.info("🗑️  Cleaning ChromaDB...")
        
        # Connect to ChromaDB
        chroma_client = chromadb.PersistentClient(
            path=settings.chroma_db_path,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        
        # Get all collections
        collections = chroma_client.list_collections()
        
        if not collections:
            logger.info("   ℹ️  ChromaDB already empty")
            return
        
        # Delete each collection
        for collection in collections:
            logger.info(f"   🗑️  Deleting collection: {collection.name}")
            chroma_client.delete_collection(collection.name)
        
        logger.success(f"✅ ChromaDB cleaned! Deleted {len(collections)} collection(s)")
        
    except Exception as e:
        logger.error(f"❌ ChromaDB cleanup error: {e}")
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
        logger.error(f"❌ Neo4j cleanup error: {e}")
        raise

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
    
    try:
        # Clean ChromaDB
        clean_chromadb()
        print()
        
        # Clean Neo4j
        clean_neo4j()
        print()
        
        # Clean cache databases
        clean_cache_databases()
        print()
        
        print("=" * 60)
        logger.success("🎉 ALL DATABASES CLEANED SUCCESSFULLY!")
        print("=" * 60)
        print("\n✅ You can now re-index your documents fresh.")
        print("   Both ChromaDB and Neo4j will be populated together.\n")
        
    except Exception as e:
        print("\n" + "=" * 60)
        logger.error(f"❌ CLEANUP FAILED: {e}")
        print("=" * 60)
        raise

if __name__ == "__main__":
    main()
