from qdrant_client import QdrantClient
c = QdrantClient(path='./qdrant_db')
r = c.scroll('engineering_standards', limit=5, with_payload=['file_name', 'document_name'])
for p in r[0]:
    fn = p.payload.get('file_name')
    dn = p.payload.get('document_name')
    print(f"file_name: {fn}, document_name: {dn}")
