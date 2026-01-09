
from qdrant_client import QdrantClient
from qdrant_client.http import models

def fix_index():
    # Credentials from .env
    qdrant_url = "https://40610e80-00b0-4345-b0bb-cc6c4be7297a.europe-west3-0.gcp.cloud.qdrant.io"
    qdrant_api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.XnRJ5t2kNrr6IfUlossYt9vtrVlcjcGjHwjDlQvHkHg"

    print(f"Connecting to Qdrant Cloud: {qdrant_url}")
    client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)

    collection_name = "engineering_standards"
    
    # Verify collection
    try:
        client.get_collection(collection_name)
    except:
        print(f"Collection '{collection_name}' not found!")
        return

    print(f"Creating payload indexes for '{collection_name}'...")
    
    # Fields that need keyword indexing for filtering
    fields_to_index = ["categories", "file_name", "page_label", "section_title", "document_id"]
    
    for field in fields_to_index:
        try:
             client.create_payload_index(
                collection_name=collection_name,
                field_name=field,
                field_schema=models.PayloadSchemaType.KEYWORD,
            )
             print(f"✅ Index request sent for '{field}'")
        except Exception as e:
             # It implies it might already exist or another issue, usually safe to ignore if it says 'already exists'
             print(f"⚠️ Notice for '{field}': {e}")

    print("Index creation complete. You can now run the Python app.")

if __name__ == "__main__":
    fix_index()
