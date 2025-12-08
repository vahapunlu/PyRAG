from src.query_engine import QueryEngine

engine = QueryEngine()
collection = engine.chroma_collection

# LDA için tüm chunk'ları al
result = collection.get(
    where={'file_name': 'LDA.pdf'},
    include=['documents', 'metadatas']
)

print(f'Total LDA chunks in ChromaDB: {len(result["documents"])}')

# Cable/electrical keyword'leri içeren chunk'ları say
keywords = ['cable', 'kablo', 'wire', 'conductor', 'electrical', 'wiring']
cable_chunks = []
for i, text in enumerate(result['documents']):
    text_lower = text.lower()
    if any(kw in text_lower for kw in keywords):
        cable_chunks.append(text)

print(f'Chunks with cable/electrical keywords: {len(cable_chunks)}')
print(f'Percentage: {len(cable_chunks)/len(result["documents"])*100:.1f}%')

# Size/section keyword'lerini de kontrol et
size_keywords = ['section', 'size', 'sizing', 'csa', 'cross-section', 'kesit']
size_chunks = []
for text in result['documents']:
    text_lower = text.lower()
    if any(kw in text_lower for kw in size_keywords):
        size_chunks.append(text)

print(f'\nChunks with size/section keywords: {len(size_chunks)}')

# Her iki grup keyword içeren (cable + section)
both = []
for text in result['documents']:
    text_lower = text.lower()
    has_cable = any(kw in text_lower for kw in keywords)
    has_size = any(kw in text_lower for kw in size_keywords)
    if has_cable and has_size:
        both.append(text)

print(f'Chunks with BOTH cable AND size keywords: {len(both)}')
print(f'\nFocus area filtering should reduce from {len(result["documents"])} to ~{len(both)} chunks')
