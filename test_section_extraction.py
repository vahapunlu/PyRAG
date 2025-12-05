from src.ingestion import DocumentIngestion
from pathlib import Path

ing = DocumentIngestion(collection_name='TEST_SECTIONS')
docs = ing.parse_pdf_with_tables(Path('data/LDA.pdf'))

print(f"\nExtracted {len(docs)} pages\n")
print("="*80)

for doc in docs[:15]:
    meta = doc.metadata
    page = meta.get('page_number', '?')
    sec_num = meta.get('section_number', '')
    sec_title = meta.get('section_title', '')
    
    if sec_num:
        print(f"Page {page:2d}: Section {sec_num:6s} - {sec_title}")
    else:
        print(f"Page {page:2d}: [No section header]")
