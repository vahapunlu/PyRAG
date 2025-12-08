"""
Test Query Analyzer
"""

from src.query_analyzer import get_query_analyzer

def test_query_analyzer():
    analyzer = get_query_analyzer()
    
    test_queries = [
        "2.5mm² kablonun akım taşıma kapasitesi nedir?",
        "Manual call point nedir?",
        "IS3218 standardına göre MCP yerleştirme",
        "Sıcaklık düzeltme faktörü nasıl hesaplanır?",
        "Fire alarm system components",
        "16mm2 bakır kablo için tablo değerleri"
    ]
    
    print("\n" + "="*60)
    print("QUERY ANALYZER TEST")
    print("="*60)
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        analysis = analyzer.analyze(query)
        
        print(f"   Intent: {analysis['intent'].value}")
        print(f"   Numbers: {analysis['numbers']}")
        print(f"   Units: {analysis['units']}")
        print(f"   References: {analysis['references']}")
        print(f"   Weights: {analysis['weights']}")

if __name__ == "__main__":
    test_query_analyzer()
