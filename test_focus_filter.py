from src.cross_reference import CrossReferenceEngine
from src.query_engine import QueryEngine

engine = QueryEngine()
cross_ref = CrossReferenceEngine(engine)

# Manuel olarak focus area filtering'i test et
focus_area = 'kablo kesiti'
print(f'Testing focus area: {focus_area}')

# Keyword expansion'ı göster
keyword_map = {
    'kablo': ['cable', 'wire', 'conductor', 'wiring'],
    'kesiti': ['section', 'cross-section', 'size', 'csa', 'cross section'],
}

expanded_keywords = []
for word in focus_area.lower().split():
    if word in keyword_map:
        expanded_keywords.extend(keyword_map[word])
        print(f'{word} -> {keyword_map[word]}')
    else:
        expanded_keywords.append(word)

print(f'\nExpanded keywords: {expanded_keywords}')

# Tüm chunk'ları al
chunks = cross_ref._get_all_chunks_from_document('LDA.pdf')
print(f'\nTotal LDA chunks: {len(chunks)}')

# Manuel filtering - text'te keyword var mı?
filtered = []
for chunk in chunks:
    text_lower = chunk.text.lower()
    if any(keyword in text_lower for keyword in expanded_keywords):
        filtered.append(chunk)

print(f'Manually filtered chunks: {len(filtered)}')

if filtered:
    print(f'\n--- Sample filtered chunk ---')
    print(filtered[0].text[:300])
