
from qdrant_client import QdrantClient
from src.utils import get_settings

def check_filenames():
    settings = get_settings()
    client = QdrantClient(path=settings.qdrant_path)
    collection_name = "engineering_standards" # Default
    
    print(f"Checking collection: {collection_name}")
    
    # Scroll a bit to get samples
    points, _ = client.scroll(
        collection_name=collection_name,
        limit=100,
        with_payload=True,
        with_vectors=False
    )
    
    unique_filenames = set()
    for point in points:
        payload = point.payload or {}
        fname = payload.get("file_name", "N/A")
        unique_filenames.add(fname)
        
    print("\n📂 Filenames found in Database:")
    for name in unique_filenames:
        print(f"   - '{name}'")

if __name__ == "__main__":
    check_filenames()
