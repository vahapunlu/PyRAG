"""
Auto-Summary Dialog for PyRAG GUI

Modern full-screen interface for generating summaries from specifications.
"""

import customtkinter as ctk
from typing import Optional, Callable, List
from datetime import datetime
from tkinter import filedialog
import os
from ..auto_summary import AutoSummaryEngine, SummaryType, SummaryResult


class AutoSummaryDialog(ctk.CTkToplevel):
    """Modern full-screen auto-summary interface"""
    
    def __init__(
        self,
        parent,
        query_engine,
        available_documents: List[str],
        on_summary_complete: Optional[Callable] = None
    ):
        super().__init__(parent)
        
        self.query_engine = query_engine
        self.available_documents = available_documents
        self.on_summary_complete = on_summary_complete
        self.summary_engine = AutoSummaryEngine(query_engine)
        self.current_result = None
        
        # Window setup - Full screen
        self.title("📄 Auto-Summary - Extract Topics from Specifications")
        
        # Make fullscreen
        self.state('zoomed')  # Windows fullscreen
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        # Setup UI
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup modern full-screen interface"""
        
        # Configure grid
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # ===== TOP BAR =====
        top_bar = ctk.CTkFrame(self, height=80, corner_radius=0)
        top_bar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=0, pady=0)
        top_bar.grid_columnconfigure(1, weight=1)
        
        # Title
        ctk.CTkLabel(
            top_bar,
            text="📄 Auto-Summary"
        ).grid(row=0, column=0, padx=20, pady=10, sticky="w")
        
        # Topic input
        input_frame = ctk.CTkFrame(top_bar)
        input_frame.grid(row=0, column=1, padx=20, pady=10, sticky="ew")
        
        ctk.CTkLabel(
            input_frame,
            text="Topic:"
        ).pack(side="left", padx=(10, 5))
        
        self.topic_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Enter topic (e.g., electrical, cable, UPS)...",
            height=40
        )
        self.topic_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        # Buttons
        self.generate_button = ctk.CTkButton(
            input_frame,
            text="🚀 Generate",
            height=40,
            width=120,
            command=self._generate_summary
        )
        self.generate_button.pack(side="left", padx=5)
        
        self.export_button = ctk.CTkButton(
            input_frame,
            text="📥 Export",
            height=40,
            width=100,
            fg_color="transparent",
            border_width=2,
            command=self._export_current_summary,
            state="disabled"
        )
        self.export_button.pack(side="left", padx=5)
        
        # ===== LEFT SIDEBAR - Documents =====
        left_sidebar = ctk.CTkFrame(self, width=300)
        left_sidebar.grid(row=1, column=0, sticky="nsew", padx=(0, 0), pady=0)
        left_sidebar.grid_propagate(False)
        
        # Documents header
        ctk.CTkLabel(
            left_sidebar,
            text="📚 Documents"
        ).pack(pady=(20, 10), padx=20, anchor="w")
        
        # Documents list (scrollable)
        self.docs_frame = ctk.CTkScrollableFrame(left_sidebar)
        self.docs_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self.selected_doc_var = ctk.StringVar(value=self.available_documents[0] if self.available_documents else "")
        
        for doc in self.available_documents:
            doc_btn = ctk.CTkRadioButton(
                self.docs_frame,
                text=doc,
                variable=self.selected_doc_var,
                value=doc,
                command=self._on_doc_select
            )
            doc_btn.pack(anchor="w", pady=5, padx=10)
        
        # Quick topics section
        ctk.CTkLabel(
            left_sidebar,
            text="⚡ Quick Topics"
        ).pack(pady=(20, 10), padx=20, anchor="w")
        
        quick_topics_frame = ctk.CTkFrame(left_sidebar)
        quick_topics_frame.pack(fill="x", padx=10, pady=(0, 20))
        
        quick_topics = [
            ("⚡ Electrical", "electrical"),
            ("🔋 UPS", "UPS"),
            ("⚙️ Generator", "generator"),
            ("💡 Lighting", "lighting"),
            ("🔥 Fire Alarm", "fire alarm"),
            ("🧯 Firestopping", "firestopping"),
            ("🔌 Cable", "cable"),
            ("🧪 Testing", "testing")
        ]
        
        for label, topic in quick_topics:
            btn = ctk.CTkButton(
                quick_topics_frame,
                text=label,
                height=35,
                command=lambda t=topic: self._set_topic(t)
            )
            btn.pack(fill="x", padx=10, pady=3)
        
        # ===== RIGHT PANEL - Summary Display =====
        right_panel = ctk.CTkFrame(self)
        right_panel.grid(row=1, column=1, sticky="nsew", padx=0, pady=0)
        right_panel.grid_rowconfigure(1, weight=1)
        right_panel.grid_columnconfigure(0, weight=1)
        
        # Status bar
        status_frame = ctk.CTkFrame(right_panel, height=40)
        status_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        
        self.status_label = ctk.CTkLabel(
            status_frame,
            text="💡 Enter a topic and click Generate to create summary",
            anchor="w"
        )
        self.status_label.pack(side="left", padx=10, pady=5)
        
        self.progress_bar = ctk.CTkProgressBar(status_frame, height=5)
        self.progress_bar.pack(side="right", padx=10, pady=5, fill="x", expand=True)
        self.progress_bar.set(0)
        
        # Summary display (tabview)
        self.tabview = ctk.CTkTabview(right_panel)
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        
        # Summary tab
        self.tabview.add("📋 Summary")
        self.summary_textbox = ctk.CTkTextbox(
            self.tabview.tab("📋 Summary"),
            wrap="word"
        )
        self.summary_textbox.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Sections tab
        self.tabview.add("📄 Sections")
        self.sections_textbox = ctk.CTkTextbox(
            self.tabview.tab("📄 Sections"),
            wrap="word"
        )
        self.sections_textbox.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Initial welcome message
        self._show_welcome_message()
    
    def _show_welcome_message(self):
        """Show welcome message in summary area"""
        welcome = """

────────────────────────────────────────────────────────────────────────────────

🎯 Welcome to Auto-Summary

Extract focused summaries from large specification documents.

────────────────────────────────────────────────────────────────────────────────

HOW TO USE:

1. 📚 Select a document from the left sidebar
2. ✏️ Enter a topic in the top text box (or click a Quick Topic button)
3. 🚀 Click "Generate" to create the summary
4. 📥 Export your results when ready


Quick Topics provide instant access to common MEP topics like:
⚡ Electrical, 🔋 UPS, ⚙️ Generator, 💡 Lighting, and more!


Ready to start? Select a document and topic above.

────────────────────────────────────────────────────────────────────────────────
"""
        
        self.summary_textbox.insert("1.0", welcome)
        self.summary_textbox.configure(state="disabled")
    
    def _set_topic(self, topic: str):
        """Set topic from quick button"""
        self.topic_entry.delete(0, 'end')
        self.topic_entry.insert(0, topic)
        self.topic_entry.focus()
    
    def _on_doc_select(self):
        """Handle document selection"""
        doc = self.selected_doc_var.get()
        self.status_label.configure(text=f"📄 Selected: {doc}")
    
    def _generate_summary(self):
        """Generate the summary"""
        topic = self.topic_entry.get().strip()
        
        if not topic:
            self.status_label.configure(text="❌ Please enter a topic")
            return
        
        document = self.selected_doc_var.get()
        
        # Update UI
        self.progress_bar.set(0.3)
        self.status_label.configure(text=f"🔍 Extracting '{topic}' sections from {document}...")
        self.update()
        
        try:
            # Generate topic summary
            self.progress_bar.set(0.5)
            result = self.summary_engine.generate_topic_summary(
                document,
                topic
                )
            
            self.progress_bar.set(1.0)
            self.status_label.configure(text=f"✅ Found {len(result.extracted_sections)} sections - Summary generated!")
            
            # Store current result
            self.current_result = result
            
            # Enable export button
            self.export_button.configure(state="normal")
            
            # Show result in main window
            self._display_result(result)
            
            # Callback
            if self.on_summary_complete:
                self.on_summary_complete(result)
        
        except Exception as e:
            self.status_label.configure(text=f"❌ Error: {str(e)}")
            self.progress_bar.set(0)
    
    def _display_result(self, result: SummaryResult):
        """Display the summary result in the main window"""
        # Clear existing content
        self.summary_textbox.configure(state="normal")
        self.summary_textbox.delete("1.0", "end")
        
        self.sections_textbox.configure(state="normal")
        self.sections_textbox.delete("1.0", "end")
        
        # === Display Summary ===
        self._insert_formatted_summary(self.summary_textbox, result.summary, result.focus_topic)
        self.summary_textbox.configure(state="disabled")
        
        # === Display Sections ===
        # Configure tags for sections
        # Use default fonts for compatibility
        pass
        
        # Insert formatted sections
        for i, section in enumerate(result.extracted_sections, 1):
            doc_prefix = f"[{section.get('document', 'N/A')}] " if 'document' in section else ""
            
            self.sections_textbox.insert("end", "\n" + "─" * 80 + "\n", "separator")
            self.sections_textbox.insert("end", f"📄 {i}. {doc_prefix}{section['section_number']} - {section['title']}\n", "section_header")
            self.sections_textbox.insert("end", f"   📍 Page: {section['page']}\n", "section_meta")
            self.sections_textbox.insert("end", "─" * 80 + "\n\n", "separator")
            self.sections_textbox.insert("end", section['content'] + "\n\n", "section_content")
        
        self.sections_textbox.configure(state="disabled")
    
    def _export_current_summary(self):
        """Export current summary to PDF file"""
        if not self.current_result:
            self.status_label.configure(text="❌ No summary to export")
            return
        
        result = self.current_result
        
        # Suggest filename
        safe_topic = "".join(c for c in result.focus_topic if c.isalnum() or c in (' ', '-', '_'))
        suggested_name = f"summary_{safe_topic}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            initialfile=suggested_name
        )
        
        if filename:
            try:
                self._export_to_pdf(filename, result)
                self.status_label.configure(text=f"✅ Exported to {os.path.basename(filename)}")
            
            except Exception as e:
                self.status_label.configure(text=f"❌ Export failed: {str(e)}")
    
    def _export_to_pdf(self, filename: str, result: SummaryResult):
        """Export summary to PDF file"""
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
        from reportlab.lib.enums import TA_LEFT, TA_CENTER
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        
        # Create PDF
        doc = SimpleDocTemplate(
            filename,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        # Build content
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor='#2c3e50',
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor='#34495e',
            spaceAfter=12,
            spaceBefore=12
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=11,
            leading=16,
            spaceAfter=10
        )
        
        section_style = ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading3'],
            fontSize=13,
            textColor='#2980b9',
            spaceAfter=8,
            spaceBefore=8
        )
        
        # Title
        story.append(Paragraph(f"📄 AUTO-SUMMARY REPORT", title_style))
        story.append(Spacer(1, 0.5*cm))
        
        # Metadata
        story.append(Paragraph(f"<b>Topic:</b> {result.focus_topic}", normal_style))
        story.append(Paragraph(f"<b>Document:</b> {result.document_name}", normal_style))
        story.append(Paragraph(f"<b>Generated:</b> {result.timestamp}", normal_style))
        story.append(Paragraph(f"<b>Sections Found:</b> {len(result.extracted_sections)}", normal_style))
        story.append(Spacer(1, 1*cm))
        
        # Summary section
        story.append(Paragraph("SUMMARY", heading_style))
        story.append(Spacer(1, 0.3*cm))
        
        # Split summary into paragraphs
        summary_paragraphs = result.summary.split('\n\n')
        for para in summary_paragraphs:
            if para.strip():
                # Clean up the text for PDF
                clean_para = para.replace('**', '<b>').replace('**', '</b>')
                story.append(Paragraph(clean_para, normal_style))
        
        story.append(PageBreak())
        
        # Extracted sections
        story.append(Paragraph("EXTRACTED SECTIONS", heading_style))
        story.append(Spacer(1, 0.5*cm))
        
        for i, section in enumerate(result.extracted_sections[:20], 1):  # Limit to 20 sections for PDF
            doc_prefix = f"[{section.get('document', 'N/A')}] " if 'document' in section else ""
            
            # Section header
            section_title = f"{i}. {doc_prefix}{section['section_number']} - {section['title']}"
            story.append(Paragraph(section_title, section_style))
            story.append(Paragraph(f"<i>Page: {section['page']}</i>", normal_style))
            story.append(Spacer(1, 0.2*cm))
            
            # Section content (truncate if too long)
            content = section['content'][:1000] + "..." if len(section['content']) > 1000 else section['content']
            story.append(Paragraph(content.replace('\n', '<br/>'), normal_style))
            story.append(Spacer(1, 0.5*cm))
        
        if len(result.extracted_sections) > 20:
            story.append(Paragraph(
                f"<i>Note: Showing first 20 of {len(result.extracted_sections)} sections. "
                "Full details available in the application.</i>",
                normal_style
            ))
        
        # Build PDF
        doc.build(story)
    
    def _insert_formatted_summary(self, textbox, summary: str, topic: str):
        """Insert formatted summary with rich text styling"""
        import re
        
        # Configure text tags for formatting
        # Configure text tags for formatting (using default fonts)
        textbox.tag_config("heading")
        textbox.tag_config("subheading")
        textbox.tag_config("bold")
        textbox.tag_config("normal")
        textbox.tag_config("code")
        textbox.tag_config("bullet")
        textbox.tag_config("number")
        
        # Add title
        textbox.insert("end", f"📋 {topic.upper()} - SUMMARY\n\n", "heading")
        textbox.insert("end", "=" * 80 + "\n\n", "normal")
        
        # Parse and format summary
        lines = summary.split('\n')
        for line in lines:
            if not line.strip():
                textbox.insert("end", "\n")
                continue
                
            # Headers (###, ##, #)
            if line.startswith('###'):
                textbox.insert("end", "\n" + line.replace('###', '').strip() + "\n", "subheading")
            elif line.startswith('##'):
                textbox.insert("end", "\n" + line.replace('##', '').strip() + "\n\n", "heading")
            elif line.startswith('#'):
                textbox.insert("end", "\n" + line.replace('#', '').strip() + "\n\n", "heading")
            
            # Bullet points
            elif line.strip().startswith(('-', '*', '•')):
                indent = len(line) - len(line.lstrip())
                bullet_text = line.strip()[1:].strip()
                textbox.insert("end", " " * indent + "  • ", "bullet")
                self._insert_inline_formatting(textbox, bullet_text)
                textbox.insert("end", "\n")
            
            # Numbered lists
            elif len(line) > 2 and line.strip()[0].isdigit() and line.strip()[1] in ('.', ')'):
                parts = line.strip().split(None, 1)
                if len(parts) == 2:
                    textbox.insert("end", f"  {parts[0]} ", "number")
                    self._insert_inline_formatting(textbox, parts[1])
                    textbox.insert("end", "\n")
                else:
                    self._insert_inline_formatting(textbox, line)
                    textbox.insert("end", "\n")
            
            # Code blocks (```)
            elif line.strip().startswith('```'):
                textbox.insert("end", line + "\n", "code")
            
            # Normal text with inline formatting
            else:
                self._insert_inline_formatting(textbox, line)
                textbox.insert("end", "\n")
    
    def _insert_inline_formatting(self, textbox, text: str):
        """Handle inline formatting (bold, italic, code)"""
        import re
        
        # Handle **bold** text
        parts = re.split(r'(\*\*.*?\*\*)', text)
        for part in parts:
            if part.startswith('**') and part.endswith('**'):
                textbox.insert("end", part[2:-2], "bold")
            else:
                # Handle `code` text
                code_parts = re.split(r'(`.*?`)', part)
                for code_part in code_parts:
                    if code_part.startswith('`') and code_part.endswith('`'):
                        textbox.insert("end", code_part[1:-1], "code")
                    else:
                        textbox.insert("end", code_part, "normal")
