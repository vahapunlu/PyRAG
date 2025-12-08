from src.cross_reference import CrossReferenceEngine
from src.query_engine import QueryEngine
import time

engine = QueryEngine()
cross_ref = CrossReferenceEngine(engine)

print('='*80)
print(' QUICK TEST: LDA vs IS3218 (kablo kesiti)')
print('='*80)

# Focus area ile chunk'ları al
focus_area = 'kablo kesiti'
all_chunks = cross_ref._get_all_chunks_from_document('LDA.pdf')
print(f'\n Total LDA chunks: {len(all_chunks)}')

# Focus area filtering
expanded_keywords = {'kablo', 'kesiti', 'cable', 'wire', 'conductor', 'wiring', 
                     'section', 'cross-section', 'cross section', 'size', 'sizing', 'csa'}

filtered_chunks = [
    chunk for chunk in all_chunks
    if any(kw in chunk.text.lower() for kw in expanded_keywords)
]

print(f' Filtered to: {len(filtered_chunks)} chunks with focus area')

if filtered_chunks:
    print(f'\n Testing 3 chunks against IS3218...')
    test_chunks = filtered_chunks[:3]
    
    start = time.time()
    for i, chunk in enumerate(test_chunks):
        print(f'  Chunk {i+1}/3...', end=' ', flush=True)
        results = cross_ref._semantic_search_in_document(
            query_text=chunk.text,
            document_name='IS3218 2024.pdf',
            focus_area=None,
            top_k=5
        )
        print(f'{len(results)} results')
    
    elapsed = time.time() - start
    print(f'\n 3 chunks took {elapsed:.1f} seconds ({elapsed/3:.1f}s per chunk)')
    print(f' Estimated for all {len(filtered_chunks)} chunks: {elapsed * len(filtered_chunks) / 3 / 60:.1f} minutes')
else:
    print(' No chunks matched focus area!')
