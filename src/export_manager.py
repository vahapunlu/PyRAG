"""
Export Manager

Export query results to PDF, Word, and Markdown formats
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from loguru import logger

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib import colors
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.warning("⚠️ reportlab not installed - PDF export disabled")

try:
    from docx import Document
    from docx.shared import Pt, Inches, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    logger.warning("⚠️ python-docx not installed - Word export disabled")


class ExportManager:
    """
    Export query results to various formats
    
    Features:
    - PDF export with Turkish support
    - Word document export
    - Markdown export
    """
    
    def __init__(self, export_dir: str = "exports"):
        """Initialize export manager"""
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"✅ Export Manager initialized at {export_dir}")
    
    def export_to_markdown(self, query: str, response: str, sources: List[Dict], 
                          metadata: Dict = None) -> str:
        """
        Export to Markdown
        
        Args:
            query: User query
            response: System response
            sources: Source documents
            metadata: Additional metadata
            
        Returns:
            Path to created file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"query_result_{timestamp}.md"
        filepath = self.export_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            # Header
            f.write("# PyRAG Query Result\n\n")
            f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")
            
            # Query
            f.write("## 📝 Query\n\n")
            f.write(f"{query}\n\n")
            f.write("---\n\n")
            
            # Response
            f.write("## 💡 Response\n\n")
            f.write(f"{response}\n\n")
            f.write("---\n\n")
            
            # Sources
            if sources:
                f.write("## 📚 Sources\n\n")
                for i, source in enumerate(sources, 1):
                    f.write(f"### Source {i}\n\n")
                    f.write(f"**Content:** {source.get('content', 'N/A')}\n\n")
                    
                    if 'metadata' in source:
                        meta = source['metadata']
                        f.write(f"**Document:** {meta.get('document_name', 'N/A')}\n\n")
                        f.write(f"**Section:** {meta.get('section_title', 'N/A')}\n\n")
                        f.write(f"**Page:** {meta.get('page_number', 'N/A')}\n\n")
                    
                    f.write("---\n\n")
            
            # Metadata
            if metadata:
                f.write("## ⚙️ Metadata\n\n")
                f.write(f"```json\n{metadata}\n```\n\n")
        
        logger.info(f"📄 Markdown exported: {filepath}")
        return str(filepath)
    
    def export_to_pdf(self, query: str, response: str, sources: List[Dict], 
                     metadata: Dict = None) -> Optional[str]:
        """
        Export to PDF
        
        Args:
            query: User query
            response: System response
            sources: Source documents
            metadata: Additional metadata
            
        Returns:
            Path to created file or None if failed
        """
        if not REPORTLAB_AVAILABLE:
            logger.error("❌ PDF export not available - install reportlab")
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"query_result_{timestamp}.pdf"
        filepath = self.export_dir / filename
        
        try:
            # Create PDF
            doc = SimpleDocTemplate(str(filepath), pagesize=A4,
                                   rightMargin=2*cm, leftMargin=2*cm,
                                   topMargin=2*cm, bottomMargin=2*cm)
            
            # Container for elements
            story = []
            
            # Styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                textColor=colors.HexColor('#1E40AF'),
                spaceAfter=12
            )
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#2563EB'),
                spaceAfter=10,
                spaceBefore=10
            )
            normal_style = styles['Normal']
            
            # Title
            story.append(Paragraph("PyRAG Query Result", title_style))
            story.append(Paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
            story.append(Spacer(1, 0.5*cm))
            
            # Query
            story.append(Paragraph("Query", heading_style))
            story.append(Paragraph(query, normal_style))
            story.append(Spacer(1, 0.3*cm))
            
            # Response
            story.append(Paragraph("Response", heading_style))
            story.append(Paragraph(response.replace('\n', '<br/>'), normal_style))
            story.append(Spacer(1, 0.5*cm))
            
            # Sources
            if sources:
                story.append(Paragraph("Sources", heading_style))
                for i, source in enumerate(sources, 1):
                    story.append(Paragraph(f"<b>Source {i}</b>", normal_style))
                    content = source.get('content', 'N/A')[:500]  # Limit length
                    story.append(Paragraph(content.replace('\n', '<br/>'), normal_style))
                    
                    if 'metadata' in source:
                        meta = source['metadata']
                        doc_name = meta.get('document_name', 'N/A')
                        section = meta.get('section_title', 'N/A')
                        page = meta.get('page_number', 'N/A')
                        story.append(Paragraph(f"Document: {doc_name}, Section: {section}, Page: {page}", normal_style))
                    
                    story.append(Spacer(1, 0.3*cm))
            
            # Build PDF
            doc.build(story)
            
            logger.info(f"📕 PDF exported: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"❌ PDF export failed: {e}")
            return None
    
    def export_to_word(self, query: str, response: str, sources: List[Dict], 
                      metadata: Dict = None) -> Optional[str]:
        """
        Export to Word
        
        Args:
            query: User query
            response: System response
            sources: Source documents
            metadata: Additional metadata
            
        Returns:
            Path to created file or None if failed
        """
        if not DOCX_AVAILABLE:
            logger.error("❌ Word export not available - install python-docx")
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"query_result_{timestamp}.docx"
        filepath = self.export_dir / filename
        
        try:
            # Create document
            doc = Document()
            
            # Title
            title = doc.add_heading('PyRAG Query Result', 0)
            title.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            # Date
            date_para = doc.add_paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            date_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            doc.add_paragraph()  # Space
            
            # Query
            doc.add_heading('📝 Query', level=1)
            doc.add_paragraph(query)
            
            # Response
            doc.add_heading('💡 Response', level=1)
            doc.add_paragraph(response)
            
            # Sources
            if sources:
                doc.add_heading('📚 Sources', level=1)
                for i, source in enumerate(sources, 1):
                    doc.add_heading(f'Source {i}', level=2)
                    
                    # Content
                    content = source.get('content', 'N/A')[:500]  # Limit length
                    doc.add_paragraph(content)
                    
                    # Metadata
                    if 'metadata' in source:
                        meta = source['metadata']
                        meta_para = doc.add_paragraph()
                        meta_para.add_run('Document: ').bold = True
                        meta_para.add_run(f"{meta.get('document_name', 'N/A')}\n")
                        meta_para.add_run('Section: ').bold = True
                        meta_para.add_run(f"{meta.get('section_title', 'N/A')}\n")
                        meta_para.add_run('Page: ').bold = True
                        meta_para.add_run(f"{meta.get('page_number', 'N/A')}\n")
            
            # Save
            doc.save(str(filepath))
            
            logger.info(f"📘 Word document exported: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"❌ Word export failed: {e}")
            return None
    
    def export_all_formats(self, query: str, response: str, sources: List[Dict], 
                          metadata: Dict = None) -> Dict[str, Optional[str]]:
        """
        Export to all available formats
        
        Returns:
            Dict with format -> filepath mapping
        """
        results = {}
        
        results['markdown'] = self.export_to_markdown(query, response, sources, metadata)
        results['pdf'] = self.export_to_pdf(query, response, sources, metadata)
        results['word'] = self.export_to_word(query, response, sources, metadata)
        
        return results


# Singleton instance
_export_manager = None

def get_export_manager() -> ExportManager:
    """Get or create export manager singleton"""
    global _export_manager
    
    if _export_manager is None:
        _export_manager = ExportManager()
    
    return _export_manager
