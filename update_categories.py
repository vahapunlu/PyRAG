"""
Update Categories in ChromaDB

Updates the category metadata for all documents from Uncategorized to Standard
"""

import chromadb
from chromadb.config import Settings as ChromaSettings
from loguru import logger

def update_categories():
    """Update categories in ChromaDB"""
    try:
        logger.info("🔄 Updating categories in ChromaDB...")
        
        # Connect to ChromaDB
        client = chromadb.PersistentClient(
            path='./chroma_db',
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        
        # Get collection
        collection = client.get_collection('engineering_standards')
        
        # Get all items
        results = collection.get(include=['metadatas'])
        
        logger.info(f"📊 Found {len(results['ids'])} items to update")
        
        # Update each item
        updated_count = 0
        for item_id, metadata in zip(results['ids'], results['metadatas']):
            if metadata.get('categories') == 'Uncategorized':
                # Update to Standard
                metadata['categories'] = 'Standard'
                
                # Update in ChromaDB
                collection.update(
                    ids=[item_id],
                    metadatas=[metadata]
                )
                updated_count += 1
        
        logger.success(f"✅ Updated {updated_count} items from Uncategorized to Standard")
        
    except Exception as e:
        logger.error(f"❌ Error updating categories: {e}")
        raise

if __name__ == "__main__":
    update_categories()
