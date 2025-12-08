"""
Test cross-reference engine directly
"""
import sys
sys.path.insert(0, 'd:/PYT/RAG')

from src.cross_reference import CrossReferenceEngine, AnalysisType
from src.query_engine import QueryEngine
from loguru import logger

# Setup
logger.info("=== DIRECT CROSS-REFERENCE TEST ===")

# Initialize
query_engine = QueryEngine()
cross_ref = CrossReferenceEngine(query_engine)

# Test with small documents
doc_names = ["LDA.pdf", "NSAI - National Rules for Electrical Installations (Edition 5.0).pdf"]
focus_area = "kablo kesiti"

logger.info(f"📋 Documents: {doc_names}")
logger.info(f"🎯 Focus: {focus_area}")

# Run analysis
logger.info("🚀 Starting analysis...")
report = cross_ref.analyze(
    doc_names=doc_names,
    analysis_type=AnalysisType.CONFLICTS,
    focus_area=focus_area,
    top_k=5  # Reduce to 5 for faster test
)

logger.info(f"✅ Analysis complete!")
logger.info(f"📊 Summary: {report.summary}")
logger.info(f"🔥 Conflicts found: {len(report.conflicts)}")

for i, conflict in enumerate(report.conflicts[:3], 1):
    logger.info(f"\nConflict {i}:")
    logger.info(f"  Type: {conflict.conflict_type}")
    logger.info(f"  Base: {conflict.base_text[:100]}...")
    logger.info(f"  Compare: {conflict.compare_text[:100]}...")
