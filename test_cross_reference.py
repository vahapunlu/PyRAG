"""
Test Cross-Reference Engine
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.query_engine import QueryEngine
from src.cross_reference import CrossReferenceEngine, AnalysisType
from src.utils import Settings
from loguru import logger

def main():
    print("=" * 80)
    print("🧪 CROSS-REFERENCE ENGINE TEST")
    print("=" * 80)
    
    # Initialize
    query_engine = QueryEngine()
    cross_ref_engine = CrossReferenceEngine(query_engine)
    
    print("\n✅ Engines initialized")
    
    # Test documents
    base_doc = "LDA.pdf"
    compare_doc = "NSAI - National Rules for Electrical Installations (Edition 5.0).pdf"
    focus_area = None  # Test without focus first
    
    print(f"\n📄 Base Document: {base_doc}")
    print(f"📄 Compare Document: {compare_doc}")
    print(f"🎯 Focus Area: {focus_area or 'None (analyzing all chunks)'}")
    print("\n" + "=" * 80)
    print("🚀 STARTING ANALYSIS...")
    print("=" * 80 + "\n")
    
    # Run analysis
    try:
        report = cross_ref_engine.analyze(
            doc_names=[base_doc, compare_doc],
            analysis_type=AnalysisType.CONFLICTS,
            focus_area=focus_area,
            top_k=5
        )
        
        print("\n" + "=" * 80)
        print("📊 ANALYSIS COMPLETE!")
        print("=" * 80)
        print(f"\n📝 Summary: {report.summary}")
        print(f"⚠️  Conflicts Found: {len(report.conflicts)}")
        
        if report.conflicts:
            print("\n🔍 Conflicts:")
            for i, conflict in enumerate(report.conflicts[:5], 1):  # Show first 5
                print(f"\n{i}. {conflict.conflict_type}")
                print(f"   Base ({conflict.base_document}): {conflict.base_chunk[:100]}...")
                print(f"   Compare ({conflict.compare_document}): {conflict.compare_chunk[:100]}...")
                print(f"   Severity: {conflict.severity}")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        logger.exception("Test failed")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
