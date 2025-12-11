"""
Test Cross-Reference Engine V2 - Compliance Analysis
"""

import sys
import os

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, '.')

from src.query_engine import QueryEngine
from src.cross_reference_v2 import CrossReferenceEngineV2, AnalysisMode


def test_full_audit():
    """Test full compliance audit between documents"""
    
    print("=" * 70)
    print("🔍 CROSS-REFERENCE ENGINE V2 - COMPLIANCE ANALYSIS TEST")
    print("=" * 70)
    
    print("\n📂 Loading query engine...")
    qe = QueryEngine()
    
    engine = CrossReferenceEngineV2(qe)
    
    print("\n🔄 Running compliance analysis...")
    print("   Source: EDC - ELECTRICAL PARTICULAR SCOPE OF WORKS.pdf")
    print("   Reference: LDA.pdf")
    print("   Focus: cable sizing cross section")
    print()
    
    report = engine.analyze(
        source_doc='EDC - ELECTRICAL PARTICULAR SCOPE OF WORKS.pdf',
        reference_docs=['LDA.pdf'],
        focus_area='cable sizing cross section',
        mode=AnalysisMode.FULL_AUDIT
    )
    
    # Summary
    print("=" * 70)
    print("📊 ANALYSIS RESULTS")
    print("=" * 70)
    print(f"📄 Source Document: {report.source_document}")
    print(f"📚 Reference Documents: {', '.join(report.reference_documents)}")
    print(f"🎯 Focus Area: {report.focus_area}")
    print(f"⏱️  Analysis Time: {report.analysis_duration:.2f} seconds")
    print()
    
    # Compliance Score
    score = report.compliance_score
    if score >= 0.8:
        emoji = "🟢"
    elif score >= 0.5:
        emoji = "🟡"
    else:
        emoji = "🔴"
    print(f"{emoji} Compliance Score: {score:.0%}")
    print()
    
    # Issue counts
    print("📋 Issue Breakdown:")
    print(f"   🔴 Critical: {report.critical_count}")
    print(f"   🟠 High: {report.high_count}")
    print(f"   🟡 Medium: {report.medium_count}")
    print(f"   🔵 Low: {report.low_count}")
    print()
    
    print(f"📊 Statistics:")
    print(f"   Total Issues: {len(report.compliance_issues)}")
    print(f"   Gaps Found: {len(report.gaps)}")
    print(f"   Value Comparisons: {len(report.value_comparisons)}")
    print(f"   Standards Missing: {len(report.standards_missing)}")
    
    # Compliance Issues
    if report.compliance_issues:
        print()
        print("=" * 70)
        print(f"⚠️  COMPLIANCE ISSUES ({len(report.compliance_issues)})")
        print("=" * 70)
        for i, issue in enumerate(report.compliance_issues[:10], 1):
            severity_emoji = {
                'critical': '🔴',
                'high': '🟠', 
                'medium': '🟡',
                'low': '🔵',
                'info': '⚪'
            }.get(issue.severity.value, '⚪')
            print(f"\n{i}. {severity_emoji} [{issue.severity.value.upper()}] {issue.category}")
            print(f"   {issue.description[:100]}...")
            if issue.source_section:
                print(f"   📍 Source: {issue.source_section[:50]}...")
            if issue.recommendation:
                print(f"   💡 Recommendation: {issue.recommendation[:80]}...")
    
    # Value Differences
    diff_values = [v for v in report.value_comparisons if v.status in ['HIGHER', 'LOWER']]
    if diff_values:
        print()
        print("=" * 70)
        print(f"📐 VALUE DIFFERENCES ({len(diff_values)} found)")
        print("=" * 70)
        for i, v in enumerate(diff_values[:15], 1):
            status_emoji = "📈" if v.status == "HIGHER" else "📉"
            print(f"\n{i}. {status_emoji} {v.parameter}")
            print(f"   Your Value: {v.source_value} {v.unit}")
            print(f"   Reference:  {v.reference_value} {v.unit}")
            print(f"   Status: {v.status}")
            if v.source_section:
                print(f"   Source Section: {v.source_section[:50]}...")
            if v.reference_section:
                print(f"   Ref Section: {v.reference_section[:50]}...")
    
    # Gaps
    if report.gaps:
        print()
        print("=" * 70)
        print(f"❓ GAPS - Missing Requirements ({len(report.gaps)})")
        print("=" * 70)
        for i, gap in enumerate(report.gaps[:10], 1):
            sev_emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🔵'}.get(gap.severity.value, '⚪')
            print(f"\n{i}. {sev_emoji} {gap.topic}")
            print(f"   Missing: {gap.missing_requirement[:70]}...")
            print(f"   📚 From: {gap.reference_doc}")
            if gap.reference_section:
                print(f"   📍 Section: {gap.reference_section[:50]}...")
            if gap.recommendation:
                print(f"   💡 {gap.recommendation[:70]}...")
    
    # Missing Standards
    if report.standards_missing:
        print()
        print("=" * 70)
        print(f"📜 MISSING STANDARDS ({len(report.standards_missing)})")
        print("=" * 70)
        for std in report.standards_missing[:20]:
            print(f"   • {std}")
    
    # Summary
    if report.summary:
        print()
        print("=" * 70)
        print("📝 ANALYSIS SUMMARY")
        print("=" * 70)
        print(report.summary)
    
    print()
    print("=" * 70)
    print("✅ Analysis Complete!")
    print("=" * 70)
    
    return report


def test_value_comparison_only():
    """Test only value comparison mode"""
    
    print("\n" + "=" * 70)
    print("📐 VALUE COMPARISON MODE TEST")
    print("=" * 70)
    
    qe = QueryEngine()
    engine = CrossReferenceEngineV2(qe)
    
    report = engine.analyze(
        source_doc='EDC - ELECTRICAL PARTICULAR SCOPE OF WORKS.pdf',
        reference_docs=['LDA.pdf'],
        focus_area='electrical',
        mode=AnalysisMode.VALUE_COMPARISON
    )
    
    print(f"\n📊 Found {len(report.value_comparisons)} value comparisons")
    
    # Group by parameter type
    by_type = {}
    for v in report.value_comparisons:
        if v.parameter not in by_type:
            by_type[v.parameter] = []
        by_type[v.parameter].append(v)
    
    print("\n📊 Breakdown by Parameter Type:")
    for param, values in sorted(by_type.items()):
        matches = len([v for v in values if v.status == 'MATCH'])
        diffs = len([v for v in values if v.status in ['HIGHER', 'LOWER']])
        print(f"   {param}: {len(values)} total ({matches} match, {diffs} differ)")
    
    return report


def test_gap_analysis_only():
    """Test only gap analysis mode"""
    
    print("\n" + "=" * 70)
    print("❓ GAP ANALYSIS MODE TEST")
    print("=" * 70)
    
    qe = QueryEngine()
    engine = CrossReferenceEngineV2(qe)
    
    report = engine.analyze(
        source_doc='EDC - ELECTRICAL PARTICULAR SCOPE OF WORKS.pdf',
        reference_docs=['LDA.pdf'],
        focus_area='electrical',
        mode=AnalysisMode.GAP_ANALYSIS
    )
    
    print(f"\n📊 Found {len(report.gaps)} gaps")
    
    # Group by gap type
    by_type = {}
    for g in report.gaps:
        if g.gap_type not in by_type:
            by_type[g.gap_type] = []
        by_type[g.gap_type].append(g)
    
    print("\n📊 Breakdown by Gap Type:")
    for gap_type, gaps in sorted(by_type.items()):
        print(f"   {gap_type}: {len(gaps)}")
    
    return report


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Cross-Reference Engine V2")
    parser.add_argument('--mode', choices=['full', 'values', 'gaps'], default='full',
                       help='Test mode: full (default), values, or gaps')
    
    args = parser.parse_args()
    
    if args.mode == 'full':
        test_full_audit()
    elif args.mode == 'values':
        test_value_comparison_only()
    elif args.mode == 'gaps':
        test_gap_analysis_only()
