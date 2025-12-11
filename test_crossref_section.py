"""
Test cross-reference with section filtering
"""
from src.cross_reference import CrossReferenceEngine, AnalysisType
from src.query_engine import QueryEngine
from loguru import logger

logger.add("logs/crossref_test.log", rotation="10 MB")

def main():
    logger.info("="*70)
    logger.info("🧪 CROSS-REFERENCE SECTION FILTERING TEST")
    logger.info("="*70)
    
    # Initialize query engine first
    query_engine = QueryEngine()
    
    # Initialize cross-reference engine
    engine = CrossReferenceEngine(query_engine)
    
    # Test with section filtering
    selected_sections = {
        "Electrical Particular Scope of Works.pdf": ["15"]  # Section 15 only
    }
    
    logger.info(f"\n📋 Testing with sections: {selected_sections}")
    
    # Run analysis
    report = engine.analyze(
        doc_names=[
            "IS3218 2024.pdf",
            "Electrical Particular Scope of Works.pdf"
        ],
        analysis_type=AnalysisType.CONFLICTS,
        focus_area="fire alarm",
        top_k=5,
        selected_sections=selected_sections
    )
    
    logger.info(f"\n✅ Analysis complete!")
    logger.info(f"   Conflicts found: {len(report.conflicts)}")
    logger.info(f"   Documents: {report.documents}")
    
    print("\n" + "="*70)
    print(f"✅ Found {len(report.conflicts)} conflicts")
    print("="*70)
    
    if report.conflicts:
        print("\nFirst conflict:")
        print(f"  {report.conflicts[0].description}")

if __name__ == "__main__":
    main()
