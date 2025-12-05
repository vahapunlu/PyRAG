import chromadb

client = chromadb.PersistentClient('./chroma_db')

print("Current collections:")
collections = client.list_collections()
for c in collections:
    print(f"  - {c.name}")

# Delete test collections
for c in collections:
    if 'TEST' in c.name.upper():
        print(f"\nDeleting: {c.name}")
        client.delete_collection(c.name)

print("\nRemaining collections:")
for c in client.list_collections():
    print(f"  - {c.name}")
