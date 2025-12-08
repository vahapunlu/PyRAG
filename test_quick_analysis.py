from src.cross_reference import CrossReferenceEngine
from src.query_engine import QueryEngine
import time

engine = QueryEngine()
cross_ref = CrossReferenceEngine(engine)

print('='*80)
print(' QUICK CROSS-REFERENCE TEST (5 chunks only)')
print('='*80)

# Focus area ile chunk'ları al
focus_area = 'kablo kesiti'
print(f'\n Focus area: {focus_area}')

all_chunks = cross_ref._get_all_chunks_from_document('LDA.pdf')
print(f' Total LDA chunks: {len(all_chunks)}')

# Focus area filtering (koddan kopyala)
focus_lower = focus_area.lower()
keywords = focus_lower.split()

expanded_keywords = set(keywords)
keyword_map = {
    'kablo': ['cable', 'wire', 'conductor', 'wiring'],
    'kesiti': ['section', 'cross-section', 'cross section', 'size', 'sizing', 'csa'],
}

for keyword in keywords:
    if keyword in keyword_map:
        expanded_keywords.update(keyword_map[keyword])

print(f' Expanded keywords: {expanded_keywords}')

filtered_chunks = [
    chunk for chunk in all_chunks
    if any(kw in chunk.text.lower() for kw in expanded_keywords)
]

print(f' Filtered to: {len(filtered_chunks)} chunks')

if filtered_chunks:
    print(f'\n Testing analysis time for 5 chunks...')
    test_chunks = filtered_chunks[:5]
    
    start = time.time()
    for i, chunk in enumerate(test_chunks):
        print(f'  Chunk {i+1}/5...', end=' ', flush=True)
        results = cross_ref._semantic_search_in_document(
            query_text=chunk.text,
            document_name='NSAI - National Rules for Electrical Installations (Edition 5.0).pdf',
            focus_area=None,
            top_k=5
        )
        print(f'{len(results)} results')
    
    elapsed = time.time() - start
    print(f'\n 5 chunks took {elapsed:.1f} seconds')
    print(f' Estimated time for all {len(filtered_chunks)} chunks: {elapsed * len(filtered_chunks) / 5 / 60:.1f} minutes')
else:
    print(' No chunks matched focus area!')
