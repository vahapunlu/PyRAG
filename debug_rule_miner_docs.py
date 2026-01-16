
import sys
import os
from loguru import logger
import qdrant_client

# Add project root to sys.path
sys.path.append(os.getcwd())

from src.utils import get_settings

def debug_documents():
    settings = get_settings()
    client = qdrant_client.QdrantClient(url="http://localhost:6333")
    collection_name = "pyrag_collection" # Default, or check settings

    print(f"Connecting to Qdrant at http://localhost:6333...")
    
    try:
        # Check if collection exists
        collections = client.get_collections()
        print(f"Collections: {[c.name for c in collections.collections]}")
        
        # Assume valid collection is the first one or 'pyrag_collection'
        target_collection = "pyrag_collection"
        if not any(c.name == target_collection for c in collections.collections):
            if collections.collections:
                target_collection = collections.collections[0].name
                print(f"Using found collection: {target_collection}")
            else:
                print("No collections found!")
                return

        # Scroll points
        print(f"Inspecting payloads in '{target_collection}'...")
        points, _ = client.scroll(
            collection_name=target_collection,
            limit=5,
            with_payload=True
        )
        
        if not points:
            print("No points found in collection.")
            return

        print(f"Found {len(points)} sample points.")
        for i, point in enumerate(points):
            payload = point.payload
            print(f"\n--- Point {i+1} Payload Keys ---")
            print(list(payload.keys()))
            
            if 'file_name' in payload:
                print(f"file_name: {payload['file_name']}")
            elif 'metadata' in payload and 'file_name' in payload['metadata']:
                print(f"metadata.file_name: {payload['metadata']['file_name']}")
            else:
                print("WARNING: 'file_name' not found in root payload or metadata!")
                print("Full Payload:", payload)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_documents()
