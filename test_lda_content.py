from src.cross_reference import CrossReferenceEngine
from src.query_engine import QueryEngine

engine = QueryEngine()
cross_ref = CrossReferenceEngine(engine)

# Focus area OLMADAN LDA chunk'larını çek
print('Getting LDA chunks WITHOUT focus area filter...')
chunks = cross_ref._get_all_chunks_from_document('LDA.pdf')
print(f'Total chunks: {len(chunks)}')

if chunks:
    # İlk 3 chunk'ın içeriğini göster
    for i, chunk in enumerate(chunks[:3]):
        print(f'\n--- Chunk {i+1} (first 200 chars) ---')
        print(chunk.text[:200])
        print(f'Has cable/wire: {any(w in chunk.text.lower() for w in ["cable", "kablo", "wire", "conductor"])}')
