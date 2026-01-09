
import sys
import logging
from src.query_engine import QueryEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_retrieval():
    print("Initializing QueryEngine...")
    try:
        qe = QueryEngine()
        print("QueryEngine initialized.")
    except Exception as e:
        print(f"Failed to init QueryEngine: {e}")
        return

    test_doc = "IS10101.pdf"
    query = "What is the scope of this standard?"

    print(f"\nTesting query with document_filter='{test_doc}'...")
    try:
        result = qe.query(
            question=query,
            document_filter=test_doc
        )
        
        sources = result.get("sources", [])
        print(f"Found {len(sources)} sources.")
        
        if sources:
            print("First source snippet:")
            print(sources[0]["text"])
            print("Metadata keys:", sources[0]["metadata"].keys())
            if "file_name" in sources[0]["metadata"]:
                print(f"file_name in metadata: {sources[0]['metadata']['file_name']}")
        else:
            print("No sources found. Checking without filter...")
            
            # Try without filter to see if we get anything
            result_no_filter = qe.query(question=query)
            sources_nf = result_no_filter.get("sources", [])
            print(f"Found {len(sources_nf)} sources (no filter).")
            if sources_nf:
                print("First source metadata:")
                print(sources_nf[0]["metadata"])
                
    except Exception as e:
        print(f"Query failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_retrieval()
