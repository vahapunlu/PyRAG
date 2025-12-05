import pymupdf4llm

md = pymupdf4llm.to_markdown('data/LDA.pdf', page_chunks=True)

for i, page in enumerate(md[:8]):
    print(f"\n{'='*60}")
    print(f"PAGE {i+1}")
    print('='*60)
    print(page['text'][:600])
