"""
Update Categories in Vector Database (Qdrant)

Updates the category metadata for all documents from Uncategorized to Standard
"""

import sys
import os
from loguru import logger
import qdrant_client
from qdrant_client.http import models

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))
from utils import get_settings

def update_categories():
    """Update categories in Qdrant Vector Store"""
    settings = get_settings()
    
    try:
        logger.info(f"🔄 Updating categories in Qdrant...")
        
        # Qdrant Update
        client = qdrant_client.QdrantClient(path=settings.qdrant_path)
        collection_name = settings.get_collection_name()
        
        # Scroll all points
        offset = None
        updated_count = 0
        
        while True:
            points, next_offset = client.scroll(
                collection_name=collection_name,
                limit=100,
                offset=offset,
                with_payload=True,
                with_vectors=False
            )
            
            for point in points:
                metadata = point.payload or {}
                if metadata.get('categories') == 'Uncategorized':
                    # Update metadata
                    metadata['categories'] = 'Standard'
                    
                    # Update in Qdrant
                    client.set_payload(
                        collection_name=collection_name,
                        payload=metadata,
                        points=[point.id]
                    )
                    updated_count += 1
            
            offset = next_offset
            if offset is None:
                break
        
        client.close()
        logger.success(f"✅ Updated {updated_count} items from Uncategorized to Standard")
        
    except Exception as e:
        logger.error(f"❌ Error updating categories: {e}")
        raise

if __name__ == "__main__":
    update_categories()
