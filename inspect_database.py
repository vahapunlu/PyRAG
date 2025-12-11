"""
Inspect Qdrant database to see how documents are stored
"""

from qdrant_client import QdrantClient
from src.utils import get_settings
import json

def inspect_database():
    settings = get_settings()
    client = QdrantClient(path=settings.qdrant_path)
    
    # Get collection info
    collections = client.get_collections()
    print("=" * 60)
    print("QDRANT DATABASE INSPECTION")
    print("=" * 60)
    
    print("\n📦 COLLECTIONS:")
    for col in collections.collections:
        print(f"   - {col.name}")
    
    # Get collection details
    collection_name = settings.get_collection_name()
    info = client.get_collection(collection_name)
    
    print(f"\n📊 COLLECTION: {collection_name}")
    print(f"   Total Vectors: {info.points_count}")
    print(f"   Vector Dimension: {info.config.params.vectors.size}")
    
    # Get sample points
    print("\n" + "=" * 60)
    print("SAMPLE CHUNKS (first 10)")
    print("=" * 60)
    
    points = client.scroll(collection_name, limit=10, with_payload=True, with_vectors=False)[0]
    
    contextual_count = 0
    entity_count = 0
    table_count = 0
    
    for i, point in enumerate(points, 1):
        payload = point.payload
        point_id = str(point.id)[:8] if point.id else "?"
        
        print(f"\n--- Chunk {i} (ID: {point_id}...) ---")
        
        # Document info
        doc_name = payload.get("document_name", payload.get("file_name", "Unknown"))
        page = payload.get("page_label", "?")
        section_num = payload.get("section_number", "")
        section_title = payload.get("section_title", "")
        
        print(f"   📄 Document: {doc_name}")
        print(f"   📑 Page: {page}")
        if section_num or section_title:
            print(f"   📌 Section: {section_num} {section_title}")
        
        # Get text content
        node_content = payload.get("_node_content", "")
        if node_content:
            try:
                content_dict = json.loads(node_content)
                text = content_dict.get("text", "")
            except:
                text = node_content
        else:
            text = payload.get("text", "")
        
        # Check for contextual enrichment
        has_context = "[CONTEXT:" in text or "[BAĞLAM:" in text or "Document:" in text[:100]
        if has_context:
            contextual_count += 1
        print(f"   🎯 Contextual Prefix: {'✅ YES' if has_context else '❌ NO'}")
        
        # Show text preview
        preview = text[:300].replace("\n", " ").strip()
        print(f"   📝 Text Preview:")
        print(f"      {preview}...")
        
        # Metadata
        has_table = payload.get("has_table", False)
        if has_table:
            table_count += 1
        print(f"   📊 Has Table: {'✅' if has_table else '❌'}")
        
        ref_standards = payload.get("referenced_standards", [])
        if ref_standards:
            print(f"   📚 Referenced Standards: {ref_standards[:5]}")
        
        entities = payload.get("entities", [])
        if entities:
            entity_count += 1
            print(f"   🏷️ Entities: {entities[:3]}...")
        
        # Check for original_text (contextual chunking stores this)
        original_text = payload.get("original_text", "")
        if original_text and original_text != text:
            print(f"   💡 Has Original Text: ✅ (contextual enrichment applied)")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"   Total Chunks: {info.points_count}")
    print(f"   Sample Size: {len(points)}")
    print(f"   With Contextual Prefix: {contextual_count}/{len(points)}")
    print(f"   With Entities: {entity_count}/{len(points)}")
    print(f"   With Tables: {table_count}/{len(points)}")
    
    # Check all metadata keys
    if points:
        all_keys = set()
        for p in points:
            all_keys.update(p.payload.keys())
        print(f"\n   📋 All Metadata Keys: {sorted(all_keys)}")

if __name__ == "__main__":
    inspect_database()
