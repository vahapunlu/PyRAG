"""Test script for multi-document query and single-document refine mode"""

from src.query_engine import QueryEngine

def main():
    print("Initializing QueryEngine...")
    qe = QueryEngine()
    
    # Test 1: Single document query (should use 20 chunks + refine mode)
    print("\n" + "="*60)
    print("TEST 1: Single Document Query (IS10101)")
    print("Expected: 20 chunks + refine mode")
    print("="*60)
    
    question = "What are the cable sizing requirements?"
    print(f"\nQuestion: {question}")
    print("Filter: document=IS10101.pdf\n")
    
    result = qe.query(question, document_filter='IS10101.pdf')
    print(f"\nAnswer preview:\n{result['response'][:500]}...")
    
    # Test 2: All documents query (should use 10 chunks per doc + compact mode)
    print("\n" + "="*60)
    print("TEST 2: All Documents Query (Multi-Document)")
    print("Expected: 10 chunks per document + compact mode")
    print("="*60)
    
    print(f"\nQuestion: {question}")
    print("Filter: None (all documents)\n")
    
    results = qe.query_all_documents(question, min_relevance_score=0.1, chunks_per_doc=10)
    print(f"\nFound relevant content in {len(results)} documents")
    for r in results[:2]:  # Show first 2
        print(f"\n📄 {r['document_name']}: {r['answer'][:200]}...")
    
    print("\n" + "="*60)
    print("Tests complete!")
    print("="*60)

if __name__ == "__main__":
    main()
