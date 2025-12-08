from src.cross_reference import CrossReferenceEngine
from src.query_engine import QueryEngine

engine = QueryEngine()
cross_ref = CrossReferenceEngine(engine)

print('Getting all LDA chunks...')
chunks = cross_ref._get_all_chunks_from_document('LDA.pdf')
print(f'Total: {len(chunks)}')

# Cable/wire içeren chunk'ları bul
keywords = ['cable', 'kablo', 'wire', 'conductor', 'wiring', 'electrical']
cable_chunks = []
for chunk in chunks:
    text_lower = chunk.text.lower()
    if any(kw in text_lower for kw in keywords):
        cable_chunks.append(chunk)

print(f'\nChunks with cable/electrical keywords: {len(cable_chunks)}')

if cable_chunks:
    print(f'\n--- Sample cable-related chunk ---')
    print(cable_chunks[0].text[:400])
else:
    print('\nNO cable-related chunks found!')
    print('Checking random chunks for content type...')
    import random
    sample = random.sample(chunks, min(5, len(chunks)))
    for i, c in enumerate(sample):
        print(f'\n--- Random chunk {i+1} (first 150 chars) ---')
        print(c.text[:150])
