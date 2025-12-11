import sys
import os
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from query_engine import QueryEngine

load_dotenv()

def test_query():
    print("Initializing QueryEngine...")
    qe = QueryEngine()
    
    query = "cable cross-sections electrical wiring"
    print(f"\nQuery: {query}")
    
    response = qe.query(query)
    
    print("\nResponse:")
    print(response['response'])
    
    print("\nSources:")
    for source in response['sources']:
        print(f"- {source['file_name']} (Score: {source['score']:.4f})")
        print(f"  Text: {source['text'][:100]}...")

if __name__ == "__main__":
    test_query()
