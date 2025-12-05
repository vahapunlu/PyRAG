from src.query_engine import QueryEngine
from src.utils import setup_logger

# Setup debug logging
setup_logger(level="DEBUG")

# Initialize
engine = QueryEngine()

# Test query
print("\n" + "="*60)
print("Testing query...")
print("="*60)

result = engine.query("What should be the dimensions of the operating room?")

print("\n" + "="*60)
print("RESULT:")
print("="*60)
print(f"Answer: {result['answer']}")
print(f"\nSources: {len(result['sources'])}")
for src in result['sources']:
    print(f"  - {src['metadata'].get('file_name')} (Page {src['metadata'].get('page_label')})")
