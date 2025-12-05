import chromadb

client = chromadb.PersistentClient('./chroma_db')
col = client.get_collection('LDA')
print(f'Documents in LDA: {col.count()}')

if col.count() > 0:
    results = col.peek(3)
    print(f'\nFirst 3 documents:')
    for i, doc in enumerate(results['documents'][:3]):
        print(f'\n--- Document {i+1} ---')
        print(doc[:300])
