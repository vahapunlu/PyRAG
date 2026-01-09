import os
import json
import re
from datetime import datetime
from typing import Dict, Any, List

# ReportLab Imports
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER

class ReportGenerator:
    """
    Generates professional engineering reports (HTML & PDF) from Rule Comparator analysis.
    Styles mimicking major firms (ARUP, BAM, EDF, WSP).
    """
    
    def __init__(self, export_dir: str = "exports"):
        # Ensure we use absolute path for exports to avoid browser issues
        self.export_dir = os.path.abspath(export_dir)
        if not os.path.exists(self.export_dir):
            os.makedirs(self.export_dir)
            
    def generate_html_report(self, data: Dict[str, Any]) -> str:
        """
        Creates an HTML file from the structured analysis data.
        Returns the absolute path to the generated file.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        filename = f"Compliance_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        filepath = os.path.join(self.export_dir, filename)
        
        doc1 = data.get("doc1", "Unknown Document")
        doc2 = data.get("doc2", "Unknown Document")
        topics = data.get("topics", [])
        
        # Calculate Stats
        total_topics = len(topics)
        project_ref = data.get("project_ref", "REF-000")
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Engineering Compliance Report - {project_ref}</title>
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');
                
                :root {{
                    --primary: #002D62; /* Engineering Navy */
                    --secondary: #00A3E0; /* Cyan Blue */
                    --accent: #E31837; /* Alert Red */
                    --success: #007A33; /* Safe Green */
                    --warning: #FFB81C; /* Safety Yellow */
                    --bg: #F5F5F5;
                    --text: #333333;
                    --border: #DDDDDD;
                }}
                
                body {{
                    font-family: 'Roboto', 'Segoe UI', Arial, sans-serif;
                    background-color: var(--bg);
                    color: var(--text);
                    margin: 0;
                    padding: 0;
                    line-height: 1.5;
                    -webkit-font-smoothing: antialiased;
                }}
                
                .container {{
                    max-width: 1100px;
                    margin: 40px auto;
                    background: white;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
                    min-height: 297mm; /* A4 height */
                }}
                
                /* HEADER */
                header {{
                    background: var(--primary);
                    color: white;
                    padding: 30px 50px;
                    display: flex;
                    justify-content: space-between;
                    align-items: flex-start;
                    border-bottom: 4px solid var(--secondary);
                }}
                
                .brand h1 {{ font-size: 24px; margin: 0; text-transform: uppercase; letter-spacing: 1px; font-weight: 700; }}
                .brand .subtitle {{ font-size: 13px; opacity: 0.8; font-weight: 300; margin-top: 5px; }}
                
                .meta-box {{
                    text-align: right;
                    font-size: 13px;
                    opacity: 0.95;
                    line-height: 1.5;
                    border-left: 1px solid rgba(255,255,255,0.3);
                    padding-left: 20px;
                    min-width: 200px;
                }}
                
                /* CONTENT SECTIONS */
                .section {{ padding: 40px 50px; border-bottom: 1px solid var(--border); }}
                .section:last-child {{ border-bottom: none; }}
                
                h2 {{
                    color: var(--primary);
                    font-size: 20px;
                    text-transform: uppercase;
                    border-bottom: 2px solid #eee;
                    padding-bottom: 10px;
                    margin-top: 0;
                    margin-bottom: 30px;
                    letter-spacing: 0.5px;
                }}
                
                p {{ color: #555; margin-bottom: 20px; }}
                
                /* DOC COMPARISON GRID */
                .comparison-grid {{
                    display: grid;
                    grid-template-columns: 1fr 60px 1fr;
                    gap: 0;
                    background: #fff;
                    border: 1px solid #e0e0e0;
                    border-radius: 6px;
                    overflow: hidden;
                    margin: 30px 0;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.03);
                }}
                
                .doc-card {{ padding: 25px; background: white; text-align: center; }}
                .doc-card h3 {{ margin: 0 0 10px 0; font-size: 12px; color: #888; text-transform: uppercase; letter-spacing: 1px; }}
                .doc-card .doc-name {{ font-weight: 600; color: var(--primary); font-size: 16px; word-break: break-all; }}
                
                .vs-badge {{
                    background: #f8f8f8;
                    color: #999;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-weight: bold;
                    font-size: 14px;
                    border-left: 1px solid #eee;
                    border-right: 1px solid #eee;
                }}
                
                /* ANALYSIS TABLES (MARKDOWN RENDERED) */
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    font-size: 13px;
                    margin: 20px 0;
                    border: 1px solid #e0e0e0;
                    font-family: 'Segoe UI', sans-serif;
                }}
                
                th {{
                    background-color: var(--primary);
                    color: white;
                    text-align: left;
                    padding: 12px 15px;
                    font-weight: 500;
                    letter-spacing: 0.5px;
                }}
                
                td {{
                    padding: 12px 15px;
                    border-bottom: 1px solid #f0f0f0;
                    vertical-align: top;
                    color: #444;
                }}
                
                tr:last-child td {{ border-bottom: none; }}
                tr:nth-child(even) {{ background-color: #fafafa; }}
                
                /* TQ TABLE SPECIAL STYLING */
                .tq-table {{ margin-top: 10px; border: 1px solid #ccc; }}
                .tq-table th {{ background-color: #444 !important; }}
                .tq-id {{ font-family: 'Consolas', monospace; font-weight: bold; color: var(--primary); }}
                
                /* PRINT OPS */
                @media print {{
                    body {{ background: white; font-size: 12px; }}
                    .container {{ box-shadow: none; margin: 0; width: 100%; max-width: 100%; min-height: 0; }}
                    header {{ padding: 20px 0; border-bottom: 2px solid black; }}
                    header * {{ color: black !important; background: transparent !important; }}
                    .section {{ padding: 20px 0; page-break-inside: avoid; }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <header>
                    <div class="brand">
                        <h1>Engineering Compliance Audit</h1>
                        <div class="subtitle">Automated Gap Analysis & Requirement Validation</div>
                    </div>
                    <div class="meta-box">
                        <strong>Project Ref:</strong> {project_ref}<br>
                        <strong>Date:</strong> {timestamp}<br>
                        <strong>Generated By:</strong> PyRAG Agent
                    </div>
                </header>
                
                <div class="section">
                    <h2>Executive Summary</h2>
                    <p>This report details the findings of an automated compliance comparison between the primary reference document and the target verification document. Special attention has been given to numeric parameters, standard citations, and mandatory constraints ("shall"/"must").</p>
                    
                    <div class="comparison-grid">
                        <div class="doc-card">
                            <h3>Reference Document</h3>
                            <div class="doc-name">{doc1}</div>
                        </div>
                        <div class="vs-badge">VS</div>
                        <div class="doc-card">
                            <h3>Target Document</h3>
                            <div class="doc-name">{doc2}</div>
                        </div>
                    </div>
                    
                    <p><strong>Total Topics Analyzed:</strong> {total_topics}</p>
                </div>
                
                <div class="section">
                    <h2>Detailed Compliance Matrix</h2>
        """
        
        # Loop through topics and render Markdown content to HTML
        # Since we receive raw markdown in 'analysis', we ideally convert it.
        
        try:
            import markdown
            has_markdown = True
        except ImportError:
            has_markdown = False
            
        import re
        tq_items = []
        
        for topic in topics:
            topic_name = topic.get("name", "General")
            raw_analysis = topic.get("analysis", "")
            
            # --- TQ Extraction ---
            # Extract content under "Action Items" or "Draft TQ"
            # Regex looks for "3. Action Items" (header) and captures the following lines
            tq_match = re.search(r"(?:###\s*3\.?|###)\s*(?:Action Items|Draft TQ).*?\n((?:.|\n)*?)(?=$|\n#)", raw_analysis, re.IGNORECASE)
            
            if tq_match:
                actions = tq_match.group(1).strip()
                # Filter out placeholders or empty "None"
                if actions and "If conflict exists" not in actions and len(actions) > 10:
                     # Convert markdown bullets to HTML list items for the summary
                     
                     # Simple conversion for TQ table
                     html_actions = markdown.markdown(actions) if has_markdown else actions
                     tq_items.append({"topic": topic_name, "content": html_actions})
            # ---------------------
            
            # Convert Markdown to HTML
            if has_markdown:
                html_analysis = markdown.markdown(raw_analysis, extensions=['tables', 'fenced_code'])
            else:
                # Fallback simple formatting
                # Replace newlines with <br>, wrap in pre for tables?
                # Actually, displaying raw markdown is better than broken html
                html_analysis = f"<pre style='white-space: pre-wrap;'>{raw_analysis}</pre>"
            
            html_content += f"""
                    <div class="topic-block">
                        <div class="topic-header">{topic_name}</div>
                        <div class="analysis-content">
                            {html_analysis}
                        </div>
                    </div>
            """
            
        # Build TQ Table
        if tq_items:
            tq_rows = ""
            for idx, item in enumerate(tq_items, 1):
                tq_rows += f"""
                <tr>
                    <td style="width: 50px; text-align: center;"><strong>TQ-{idx:03d}</strong></td>
                    <td style="width: 200px;">{item['topic']}</td>
                    <td>{item['content']}</td>
                </tr>
                """
            
            tq_section_html = f"""
            <table class="tq-table" style="width:100%; border-collapse: collapse; margin-top:20px;">
                <thead>
                    <tr style="background-color: #856404; color: white;">
                        <th>ID</th>
                        <th>Subject / Topic</th>
                        <th>Query Description</th>
                    </tr>
                </thead>
                <tbody>
                    {tq_rows}
                </tbody>
            </table>
            """
        else:
            tq_section_html = "<p>No critical technical queries were automatically generated from this analysis.</p>"

        html_content += f"""
                </div>
                
                <div class="section">
                    <h2>Technical Queries (TQs)</h2>
                    <p>The following potential Technical Queries have been identified based on conflicting requirements.</p>
                    <div style="background:#fff3cd; color:#856404; padding:15px; border:1px solid #ffeeba; border-radius:4px; margin-bottom: 20px;">
                        <strong>Note:</strong> Verify all TQs against latest project correspondence before issuing.
                    </div>
                    {tq_section_html}
                </div>
                
                <footer>
                    Generated by PyRAG Engineering Compliance Agent<br>
                    Confidential & Proprietary
                </footer>
            </div>
        </body>
        </html>
        """
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        return filepath

    def generate_pdf_report(self, data: Dict[str, Any]) -> str:
        """
        Creates a PDF file from the structured analysis data using ReportLab.
        Returns the absolute path to the generated file.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        filename_pdf = f"Compliance_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(self.export_dir, filename_pdf)
        
        doc1 = data.get("doc1", "Unknown Document")
        doc2 = data.get("doc2", "Unknown Document")
        topics = data.get("topics", [])
        project_ref = data.get("project_ref", "REF-000")
        total_topics = len(topics)
        
        # Setup Document
        doc = SimpleDocTemplate(filepath, pagesize=A4,
                                rightMargin=2*cm, leftMargin=2*cm,
                                topMargin=2*cm, bottomMargin=2*cm)
        
        story = []
        styles = getSampleStyleSheet()
        
        # Custom Styles
        style_title = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#002D62'),
            alignment=TA_CENTER,
            spaceAfter=20
        )
        style_subtitle = ParagraphStyle(
            'ReportSubtitle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.gray,
            alignment=TA_CENTER,
            spaceAfter=50
        )
        style_heading = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#002D62'),
            borderPadding=5,
            borderWidth=0,
            borderBottomWidth=1,
            borderColor=colors.HexColor('#00A3E0'),
            spaceBefore=20,
            spaceAfter=15
        )
        style_topic = ParagraphStyle(
            'TopicHeading',
            parent=styles['Heading3'],
            fontSize=12,
            textColor=colors.black,
            backColor=colors.HexColor('#F0F0F0'),
            borderPadding=6,
            spaceBefore=15,
            spaceAfter=10
        )
        style_normal = ParagraphStyle(
            'BodyText',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            spaceAfter=8
        )
        
        # --- TITLE PAGE ---
        story.append(Spacer(1, 4*cm))
        story.append(Paragraph("ENGINEERING COMPLIANCE AUDIT", style_title))
        story.append(Paragraph("Automated Gap Analysis & Requirement Validation", style_subtitle))
        
        # Meta Table
        meta_data = [
            ["Project Reference:", project_ref],
            ["Date:", timestamp],
            ["Generated By:", "PyRAG Engineering Agent"],
            ["Status:", "PRELIMINARY"]
        ]
        t_meta = Table(meta_data, colWidths=[5*cm, 8*cm])
        t_meta.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('TEXTCOLOR', (0,0), (0,-1), colors.gray),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(t_meta)
        story.append(PageBreak())
        
        # --- EXECUTIVE SUMMARY ---
        story.append(Paragraph("1. Executive Summary", style_heading))
        story.append(Paragraph(f"This report details the findings of an automated compliance comparison between <b>{doc1}</b> and <b>{doc2}</b>.", style_normal))
        story.append(Paragraph(f"Total Topics Analyzed: <b>{total_topics}</b>", style_normal))
        story.append(Spacer(1, 1*cm))
        
        # --- ANALYSIS ---
        story.append(Paragraph("2. Detailed Compliance Matrix", style_heading))
        
        for topic in topics:
            topic_name = topic.get("name", "General")
            raw_analysis = topic.get("analysis", "")
            
            story.append(Paragraph(f"Topic: {topic_name}", style_topic))
            
            # Simple Markdown Parser for ReportLab
            self._parse_markdown_to_story(raw_analysis, story, styles, style_normal)
            
            story.append(Spacer(1, 0.5*cm))
            
        doc.build(story)
        return filepath

    def _parse_markdown_to_story(self, text, story, styles, normal_style):
        """
        Converts basic Markdown (tables, lists, bold) into ReportLab Flowables.
        """
        lines = text.split('\n')
        table_buffer = []
        in_table = False
        
        for line in lines:
            line = line.strip()
            
            # Detect Table Rows
            if "|" in line:
                # Naive check for table piping
                if "---" in line:
                    continue # Skip separator lines
                    
                cols = [c.strip() for c in line.split('|') if c.strip()]
                if cols:
                    table_buffer.append(cols)
                    in_table = True
                continue
            else:
                # Flush Table if we were in one
                if in_table and table_buffer:
                    self._create_pdf_table(table_buffer, story)
                    table_buffer = []
                    in_table = False
            
            if not line:
                continue
                
            # Headers
            if line.startswith('### '):
                story.append(Paragraph(line.replace('###', '').strip(), styles['Heading4']))
            elif line.startswith('## '):
                 story.append(Paragraph(line.replace('##', '').strip(), styles['Heading3']))
            elif line.startswith('- '):
                # Bullet
                # Sanitize bold markdown **text** -> <b>text</b>
                content = self._sanitize_md_text(line[2:])
                story.append(Paragraph(f"<bullet>&bull;</bullet> {content}", normal_style))
            else:
                # Normal Text
                content = self._sanitize_md_text(line)
                story.append(Paragraph(content, normal_style))
                
        # Flush trailing table
        if in_table and table_buffer:
            self._create_pdf_table(table_buffer, story)

    def _sanitize_md_text(self, text):
        # Basic Bold conversion
        text = text.replace("**", "<b>", 1).replace("**", "</b>", 1)
        # Handle multiple occurrences? Naive replace is risky but okay for simple output
        # Better: Regex replacement
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        return text

    def _create_pdf_table(self, data, story):
        if not data:
            return
            
        # Determine cols based on first row
        col_count = len(data[0])
        
        # Style
        t = Table(data, colWidths=[(16/col_count)*cm]*col_count) # Distribute width evenly-ish
        
        # Conditional Formatting Logic
        # We need to build the style list dynamically based on content
        tbl_style = [
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#002D62')), # Header
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('WORDWRAP', (0,0), (-1,-1), True),
        ]
        
        # Check rows for status
        for row_idx, row in enumerate(data):
            for col_idx, cell in enumerate(row):
                cell_lower = cell.lower()
                if "conflict" in cell_lower or "⚠️" in cell_lower or "mismatch" in cell_lower:
                    tbl_style.append(('TEXTCOLOR', (col_idx, row_idx), (col_idx, row_idx), colors.red))
                    tbl_style.append(('FONTNAME', (col_idx, row_idx), (col_idx, row_idx), 'Helvetica-Bold'))
                elif "agreement" in cell_lower or "compliant" in cell_lower:
                     tbl_style.append(('TEXTCOLOR', (col_idx, row_idx), (col_idx, row_idx), colors.green))
        
        t.setStyle(TableStyle(tbl_style))
        story.append(t)
        story.append(Spacer(1, 0.3*cm))
