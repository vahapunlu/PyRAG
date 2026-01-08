
import sys
import os
from collections import defaultdict
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

# Add src to path
sys.path.append(os.getcwd())

from src.utils import get_settings

def compare_docs():
    settings = get_settings()
    client = QdrantClient(path=settings.qdrant_path)
    collection_name = settings.get_collection_name()
    
    print(f"Connecting to Qdrant at {settings.qdrant_path}")
    print(f"Collection: {collection_name}")
    
    # Get all points (using scroll) to aggregate unique document names
    # Ideally we'd use a group_by or specialized query, but client-side aggregation is fine for this scale
    print("Scanning database for documents...")
    
    offset = None
    doc_counts = defaultdict(int)
    
    while True:
        points, offset = client.scroll(
            collection_name=collection_name,
            limit=1000,
            offset=offset,
            with_payload=True,
            with_vectors=False
        )
        
        for point in points:
            payload = point.payload or {}
            # Check likely keys for document name
            name = payload.get("file_name") or payload.get("document_name") or "Unknown"
            doc_counts[name] += 1
            
        if offset is None:
            break
            
    print("\n📊 Document Chunk Counts:")
    print("-" * 40)
    print(f"{'Document Name':<40} | {'Chunks':<10}")
    print("-" * 40)
    
    sorted_docs = sorted(doc_counts.items(), key=lambda x: x[0])
    
    for doc, count in sorted_docs:
        # Highlight our target documents
        marker = " "
        if "IS3218" in doc or "TEST" in doc.upper() or "Test" in doc:
            marker = "👉"
            
        print(f"{marker} {doc:<38} | {count:<10}")
        
    print("-" * 40)

if __name__ == "__main__":
    compare_docs()
