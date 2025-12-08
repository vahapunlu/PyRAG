"""
Test Auto-Summary with LDA.pdf and Cable topic
"""
from src.query_engine import QueryEngine
from src.auto_summary import AutoSummaryEngine

# Initialize query engine
print('🔧 Initializing query engine...')
qe = QueryEngine()

# Create auto-summary engine
print('📄 Creating auto-summary engine...')
summary_engine = AutoSummaryEngine(qe)

# Generate summary for cables in LDA.pdf
print('🔍 Generating summary for cables in LDA.pdf...')
result = summary_engine.generate_topic_summary('LDA.pdf', 'cable')

print('\n' + '='*80)
print(f'📊 SUMMARY RESULT')
print('='*80)
print(f'Topic: {result.focus_topic}')
print(f'Document: {result.document_name}')
print(f'Sections found: {len(result.extracted_sections)}')
print(f'Timestamp: {result.timestamp}')
print('\n' + '='*80)
print('SUMMARY:')
print('='*80)
print(result.summary)
print('\n' + '='*80)
print('FIRST 3 SECTIONS:')
print('='*80)
for i, section in enumerate(result.extracted_sections[:3], 1):
    print(f'\n{i}. {section["section_number"]} - {section["title"]}')
    print(f'   Page: {section["page"]}')
    print(f'   Content preview: {section["content"][:200]}...')

print('\n✅ Test completed!')
