from src.cross_reference import CrossReferenceEngine, AnalysisType
from src.query_engine import QueryEngine
import time

print('='*80)
print(' CROSS-REFERENCE ANALYSIS: LDA vs IS3218')
print('='*80)
print(' Focus Area: "kablo kesiti" (cable section)')
print('  Estimated time: ~6 minutes')
print('='*80)

start_time = time.time()

engine = QueryEngine()
cross_ref = CrossReferenceEngine(engine)

result = cross_ref.analyze(
    doc_names=['LDA.pdf', 'IS3218 2024.pdf'],
    analysis_type=AnalysisType.CONFLICTS,
    focus_area='kablo kesiti'
)

elapsed = time.time() - start_time

print('\n' + '='*80)
print(' ANALYSIS COMPLETE!')
print('='*80)
print(f'  Total time: {elapsed/60:.1f} minutes ({elapsed:.0f} seconds)')
print(f' Conflicts found: {len(result.conflicts)}')
print(f'\n Summary:\n{result.summary}')

if result.conflicts:
    print(f'\n Top 5 Conflicts:')
    for i, conflict in enumerate(result.conflicts[:5], 1):
        print(f'\n--- Conflict {i} ---')
        print(f'Severity: {conflict.severity}')
        print(f'Description: {conflict.description[:200]}...')
        print(f'Base Doc Page: {conflict.base_chunk.page}')
        print(f'Compare Doc Page: {conflict.compare_chunk.page}')
