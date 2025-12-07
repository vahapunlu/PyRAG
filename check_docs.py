import chromadb

c = chromadb.PersistentClient(path='./chroma_db')
col = c.get_collection('engineering_standards')

# Check unlocked version
r1 = col.get(where={'document_name': 'IS3217 2023_unlocked'}, limit=10000)
print(f'IS3217 2023_unlocked: {len(r1["ids"])} chunks')

# Check clean version  
r2 = col.get(where={'document_name': 'IS3217 2023'}, limit=10000)
print(f'IS3217 2023: {len(r2["ids"])} chunks')

# Check file_name in unlocked chunks
if r1['metadatas']:
    print(f'Sample unlocked file_name: {r1["metadatas"][0].get("file_name", "N/A")}')

if r2['metadatas']:
    print(f'Sample clean file_name: {r2["metadatas"][0].get("file_name", "N/A")}')
