#!/usr/bin/env python3
"""Test section retrieval with normalized document names"""

from src.cross_reference import CrossReferenceEngine
from src.query_engine import QueryEngine

def main():
    print("🔧 Initializing...")
    qe = QueryEngine()
    cr = CrossReferenceEngine(qe)
    
    test_docs = ['IS10101.pdf', 'IS3218.pdf', 'LDA.pdf', 'ESB-DOC-030303-AEN.pdf']
    
    for doc in test_docs:
        print(f"\n📄 Testing: {doc}")
        sections = cr.get_document_sections(doc)
        print(f"   Found {len(sections)} sections")
        if sections:
            print("   First 3 sections:")
            for s in sections[:3]:
                print(f"      • {s['name']}")

if __name__ == "__main__":
    main()
