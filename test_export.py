"""
Test Export functionality (Markdown, PDF, Word)
"""

import sys
from pathlib import Path
from loguru import logger

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.export_manager import ExportManager


def test_export():
    """Test export manager"""
    logger.info("=" * 60)
    logger.info("Testing Export Manager")
    logger.info("=" * 60)
    
    # Initialize
    export_manager = ExportManager("exports/test")
    
    # Sample data
    query = "Bakır kablo akım taşıma kapasitesi nedir?"
    response = """2.5mm² kesitli bakır kablo için akım taşıma kapasitesi şu şekildedir:

1. PVC İzolasyonlu Kablo: 25A
2. XLPE İzolasyonlu Kablo: 28A
3. Sıcaklık Düzeltme Faktörü: Ortam sıcaklığına göre Tablo 4.5'ten seçilir

Not: Bu değerler 30°C ortam sıcaklığı için geçerlidir."""
    
    sources = [
        {
            'content': 'Tablo 4.1: PVC izolasyonlu bakır iletkenler için akım taşıma kapasiteleri...',
            'metadata': {
                'document_name': 'IS10101',
                'section_title': 'Kablo Akım Kapasiteleri',
                'page_number': 45
            }
        },
        {
            'content': 'Madde 4.2: Kablo seçiminde dikkate alınması gereken faktörler...',
            'metadata': {
                'document_name': 'IS10101',
                'section_title': 'Kablo Seçim Kriterleri',
                'page_number': 42
            }
        }
    ]
    
    metadata = {
        'duration': 1.5,
        'sources_count': 2,
        'query_type': 'factual'
    }
    
    # Test 1: Markdown export
    logger.info("\n📄 Test 1: Exporting to Markdown...")
    md_path = export_manager.export_to_markdown(query, response, sources, metadata)
    if md_path:
        logger.success(f"✅ Markdown exported: {md_path}")
    else:
        logger.error("❌ Markdown export failed")
    
    # Test 2: PDF export
    logger.info("\n📕 Test 2: Exporting to PDF...")
    pdf_path = export_manager.export_to_pdf(query, response, sources, metadata)
    if pdf_path:
        logger.success(f"✅ PDF exported: {pdf_path}")
    else:
        logger.warning("⚠️ PDF export not available (install reportlab)")
    
    # Test 3: Word export
    logger.info("\n📘 Test 3: Exporting to Word...")
    word_path = export_manager.export_to_word(query, response, sources, metadata)
    if word_path:
        logger.success(f"✅ Word exported: {word_path}")
    else:
        logger.warning("⚠️ Word export not available (install python-docx)")
    
    # Test 4: Export all formats
    logger.info("\n📚 Test 4: Exporting to all formats...")
    all_paths = export_manager.export_all_formats(query, response, sources, metadata)
    logger.info("Export results:")
    for format_name, path in all_paths.items():
        if path:
            logger.success(f"  ✅ {format_name}: {path}")
        else:
            logger.warning(f"  ⚠️ {format_name}: Not available")
    
    logger.info("\n" + "=" * 60)
    logger.success("✅ All export tests completed!")
    logger.info(f"📁 Check exports/test/ directory for output files")


if __name__ == "__main__":
    test_export()
