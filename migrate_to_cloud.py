"""
MIGRATE LOCAL DB TO CLOUD
=========================

This script reads the existing embeddings (vectors) from your local disk
and uploads them directly to the Qdrant Cloud.

Benefit: No need to pay OpenAI again for embedding generation.
"""

from qdrant_client import QdrantClient
from qdrant_client.http import models
from src.utils import get_settings
from loguru import logger
import sys

def migrate():
    settings = get_settings()
    
    # 1. Connect to Local DB
    logger.info(f"📂 Opening Local Database: {settings.qdrant_path}")
    local_client = QdrantClient(path=settings.qdrant_path)
    
    # 2. Connect to Cloud DB
    if not settings.qdrant_url or not settings.qdrant_api_key:
        logger.error("❌ Cloud credentials missing in .env")
        return

    logger.info(f"☁️  Connecting to Cloud: {settings.qdrant_url}")
    cloud_client = QdrantClient(
        url=settings.qdrant_url, 
        api_key=settings.qdrant_api_key,
        timeout=60.0  # Increase timeout for cloud uploads
    )
    
    # 3. List all collections in local
    collections = local_client.get_collections().collections
    
    if not collections:
        logger.warning("⚠️  No local collections found to migrate.")
        return

    for col in collections:
        name = col.name
        logger.info(f"🚀 Migrating Collection: '{name}'")
        
        # Get collection info to recreate it with same config
        # (Though often we just need size/distance)
        # We'll just try to create it, if exists it's fine.
        # We assume 3072 dim for text-embedding-3-large, or 1536 for others.
        # Safest is to just start scrolling and uploading.
        
        # Check cloud existence
        cloud_exists = cloud_client.collection_exists(name)
        
        if not cloud_exists:
            logger.info(f"   ✨ Creating collection '{name}' on Cloud...")
            # We assume standard vector configs. 
            # If you used different models, we might need to inspect local config.
            # But usually it's better to let Qdrant handle Auto-detection if possible, 
            # or just copy the vector param.
            
            # Retrieve local config
            local_info = local_client.get_collection(name)
            vectors_config = local_info.config.params.vectors
            
            cloud_client.create_collection(
                collection_name=name,
                vectors_config=vectors_config
            )
        
        # 4. Scroll and Upload in Batches
        logger.info("   📦 Transferring points...")
        offset = None
        total = 0
        batch_size = 20  # Reduced batch size to prevent timeouts
        
        while True:
            # Read batch of points
            records, next_offset = local_client.scroll(
                collection_name=name,
                limit=batch_size,
                offset=offset,
                with_payload=True,
                with_vectors=True
            )
            
            if not records:
                break
                
            # Upload to cloud
            # Convert Record/ScoredPoint to PointStruct for upsert
            from qdrant_client.http.models import PointStruct
            
            points_to_upload = []
            for record in records:
                points_to_upload.append(
                    PointStruct(
                        id=record.id,
                        vector=record.vector,
                        payload=record.payload
                    )
                )

            cloud_client.upsert(
                collection_name=name,
                points=points_to_upload
            )
            
            total += len(records)
            print(f"      Processed {total} vectors...", end="\r")
            
            offset = next_offset
            if offset is None:
                break
        
        print("\n")
        logger.success(f"✅ Collection '{name}' migration complete! ({total} vectors)")

if __name__ == "__main__":
    migrate()
