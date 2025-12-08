"""
Test Reference Extractor
"""

from src.reference_extractor import get_reference_extractor

def test_reference_extraction():
    extractor = get_reference_extractor()
    
    # Test text with multiple reference types
    test_texts = [
        # Test 1: Standard references
        """
        Manual call points shall comply with EN 54-11 standard.
        The system design follows IS3218 and IEC 60364-5-52 requirements.
        See also BS 5839-1 for additional guidance.
        """,
        
        # Test 2: Section references
        """
        As specified in Section 6.5.1, manual call points must be installed
        at escape routes. Refer to Annex A for detailed requirements.
        Table 6.1 shows the spacing requirements.
        """,
        
        # Test 3: Cross-references
        """
        The mounting height shall be according to IS3218 Section 6.5.
        In accordance with EN 54-11 Clause 4.2, the MCP shall be red.
        See Section 7.3 for testing procedures.
        """,
        
        # Test 4: Mixed references (real example)
        """
        Manuel çağrı noktaları, I.S. EN 54-11 standardına uygun olmalıdır.
        IS3218 2024, Bölüm 16, Sayfa 45'te belirtildiği gibi, zeminden 
        minimum 0,9 m ve maksimum 1,2 m yüksekliğe sabitlenmelidir.
        """
    ]
    
    print("\n" + "="*60)
    print("REFERENCE EXTRACTION TEST")
    print("="*60)
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n📝 TEST {i}:")
        print(f"Text: {text[:100]}...")
        
        result = extractor.extract_all(text)
        
        print(f"\n📊 Results:")
        print(f"   Standards: {result['summary']['total_standards']}")
        for std in result['standards']:
            print(f"      • {std['full']} ({std['type']})")
        
        print(f"   Sections: {result['summary']['total_sections']}")
        for sec in result['sections'][:5]:  # Show first 5
            print(f"      • {sec['full']} ({sec['type']})")
        
        print(f"   Cross-refs: {result['summary']['total_cross_refs']}")
        for ref in result['cross_references'][:3]:  # Show first 3
            print(f"      • {ref['context']} → {ref['referenced_text'][:50]}...")

if __name__ == "__main__":
    test_reference_extraction()
