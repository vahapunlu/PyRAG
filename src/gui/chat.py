"""
Chat Component for PyRAG GUI

Handles chat display, message rendering, and quick filters.
"""

import tkinter as tk
import customtkinter as ctk
from loguru import logger
from .constants import *
import uuid

# HTML rendering disabled - using enhanced text tags with embedded table widgets
HTML_RENDERING_AVAILABLE = False


class ChatArea:
    """Chat display and input component with Quick Filter bar"""
    
    def __init__(self, parent, send_callback, filter_change_callback, feedback_callback=None):
        """
        Initialize chat area
        
        Args:
            parent: Parent window
            send_callback: Callback function for sending messages
            filter_change_callback: Callback when filters change
            feedback_callback: Callback function for feedback (query, response, sources, feedback_type)
        """
        self.parent = parent
        self.send_callback = send_callback
        self.filter_change_callback = filter_change_callback
        self.feedback_callback = feedback_callback
        self.chat_history = []
        self.last_query = None
        self.last_response = None
        self.last_sources = []
        self.last_query_analysis = None  # Store query analysis data
        
        # Active filters
        self.active_filters = {
            'document': None,
            'category': None,
            'project': None
        }
        
        # Store filter data
        self.all_documents = []  # All document metadata
        self.all_projects = []  # All project names
        self.all_categories = []  # All category names
        
        # Main frame (Docker Dark Background)
        self.main_frame = ctk.CTkFrame(parent, corner_radius=0, fg_color=COLORS['dark_bg'])
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(2, weight=1)  # Chat display expands
        
        self._create_header()
        self._create_quick_filter()
        self._create_chat_display()
        self._create_feedback_area()
        self._create_input_area()
        self.display_welcome_message()
        
        # Initialize follow-up frame reference
        self.followup_frame = None
    
    def _create_header(self):
        """Create chat header with query templates"""
        header_frame = ctk.CTkFrame(self.main_frame, height=60, corner_radius=0, fg_color=COLORS['dark_bg'])
        header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(
            header_frame,
            text="💬 Ask Your Questions",
            font=ctk.CTkFont(size=FONT_SIZES['subtitle'], weight="bold")
        ).grid(row=0, column=0, padx=30, pady=15, sticky="w")
        
        # Query Templates dropdown
        self.template_var = ctk.StringVar(value="📝 Templates")
        self.template_menu = ctk.CTkOptionMenu(
            header_frame,
            variable=self.template_var,
            values=[
                "📝 Templates",
                "───────────────",
                "What is the {specification} for {system}?",
                "List all requirements for {topic}",
                "What are the testing requirements?",
                "Compare {doc1} vs {doc2} for {topic}",
                "What is the cable sizing for {current}A?",
                "What are the IP ratings required?",
                "Summarize the {section} section",
                "What are the safety requirements?",
            ],
            command=self._on_template_select,
            width=280,
            height=35,
            font=ctk.CTkFont(size=FONT_SIZES['tiny']),
            fg_color=COLORS['darker_bg'],       # Sidebar color for headers contrast
            button_color=COLORS['primary'],
            button_hover_color=COLORS['primary_hover']
        )
        self.template_menu.grid(row=0, column=1, padx=30, pady=15, sticky="e")
    
    def _on_template_select(self, template):
        """Handle template selection"""
        # Reset dropdown to default
        self.template_var.set("📝 Templates")
        
        # Skip separator and header
        if template.startswith("──") or template == "📝 Templates":
            return
        
        # Insert template into input field
        self.input_entry.delete(0, "end")
        self.input_entry.insert(0, template)
        self.input_entry.focus_set()
        
        # Select placeholder text for easy replacement
        # Find first { and last } to highlight
        text = template
        start = text.find('{')
        if start != -1:
            self.input_entry.icursor(start)
            self.input_entry.selection_range(start, start + text[start:].find('}') + 1)
    
    def _create_quick_filter(self):
        """Create quick filter bar above chat"""
        filter_frame = ctk.CTkFrame(self.main_frame, fg_color=COLORS['dark_bg'], height=70)
        filter_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(10, 0))
        filter_frame.grid_columnconfigure(3, weight=1)
        
        # Label
        ctk.CTkLabel(
            filter_frame,
            text="🔍 Quick Filter:",
            font=ctk.CTkFont(size=FONT_SIZES['small'], weight="bold")
        ).grid(row=0, column=0, padx=(15, 10), pady=15, sticky="w")
        
        # 1st Dropdown: Category or Project selector
        self.cat_filter_var = ctk.StringVar(value="All Categories")
        self.cat_filter = ctk.CTkOptionMenu(
            filter_frame,
            variable=self.cat_filter_var,
            values=["All Categories"],
            command=self._on_category_change,
            width=180,
            height=35,
            font=ctk.CTkFont(size=FONT_SIZES['tiny'])
        )
        self.cat_filter.grid(row=0, column=1, padx=5, pady=15)
        
        # 2nd Dropdown: Documents (by category) OR Projects
        self.doc_filter_var = ctk.StringVar(value="All Documents")
        self.doc_filter = ctk.CTkOptionMenu(
            filter_frame,
            variable=self.doc_filter_var,
            values=["All Documents"],
            command=self._on_document_change,
            width=180,
            height=35,
            font=ctk.CTkFont(size=FONT_SIZES['tiny'])
        )
        self.doc_filter.grid(row=0, column=2, padx=5, pady=15)
        
        # 3rd Dropdown: Documents (by project)
        self.proj_doc_filter_var = ctk.StringVar(value="All Documents")
        self.proj_doc_filter = ctk.CTkOptionMenu(
            filter_frame,
            variable=self.proj_doc_filter_var,
            values=["All Documents"],
            command=self._on_project_document_change,
            width=180,
            height=35,
            font=ctk.CTkFont(size=FONT_SIZES['tiny'])
        )
        self.proj_doc_filter.grid(row=0, column=3, padx=5, pady=15, sticky="w")
        
        # Clear all button
        self.clear_filters_btn = ctk.CTkButton(
            filter_frame,
            text="✕ Clear All",
            command=self.clear_all_filters,
            width=100,
            height=35,
            font=ctk.CTkFont(size=FONT_SIZES['tiny']),
            fg_color="transparent",
            border_width=1,
            text_color=("gray10", "gray70")
        )
        self.clear_filters_btn.grid(row=0, column=4, padx=(10, 15), pady=15, sticky="e")
    
    def _on_category_change(self, selection=None):
        """Handle 1st dropdown (category/project selector) change"""
        selected = self.cat_filter_var.get()
        
        if selected == "All Categories":
            # Reset all filters
            self.doc_filter_var.set("All Documents")
            self.proj_doc_filter_var.set("All Documents")
            self.doc_filter.configure(values=["All Documents"])
            self.proj_doc_filter.configure(values=["All Documents"])
            self.active_filters['category'] = None
            self.active_filters['document'] = None
            self.active_filters['project'] = None
            
        elif selected == "Project":
            # Show only projects that have documents in 2nd dropdown
            projects_with_docs = set()
            for doc in self.all_documents:
                proj = doc.get('project')
                if proj and proj != 'N/A':
                    projects_with_docs.add(proj)
            
            if projects_with_docs:
                project_list = ["All Projects"] + sorted(list(projects_with_docs))
            else:
                project_list = ["All Projects"]
            
            self.doc_filter_var.set("All Projects")
            self.doc_filter.configure(values=project_list)
            self.proj_doc_filter_var.set("All Documents")
            self.proj_doc_filter.configure(values=["All Documents"])
            self.active_filters['category'] = None
            self.active_filters['document'] = None
            self.active_filters['project'] = None
            
        else:
            # Show documents with this category in 2nd dropdown
            # Store mapping: display_name -> name
            self.doc_name_mapping = {}
            docs_in_category = []
            
            for doc in self.all_documents:
                # Check if document belongs to this category
                if selected in doc.get('categories', []):
                    # For "Standard" category, prefer standard_no if available
                    if selected == "Standard" and 'standard_no' in doc and doc['standard_no']:
                        display = doc['standard_no']
                    else:
                        display = doc.get('display_name', doc['name'])
                    
                    # Add to list if not already there
                    if display not in docs_in_category:
                        docs_in_category.append(display)
                        self.doc_name_mapping[display] = doc['name']
            
            if docs_in_category:
                doc_list = ["All Documents"] + sorted(docs_in_category)
            else:
                doc_list = ["All Documents"]
            
            self.doc_filter_var.set("All Documents")
            self.doc_filter.configure(values=doc_list)
            self.proj_doc_filter_var.set("All Documents")
            self.proj_doc_filter.configure(values=["All Documents"])
            self.active_filters['category'] = selected
            self.active_filters['document'] = None
            self.active_filters['project'] = None
        
        self._notify_filter_change()
    
    def _on_document_change(self, selection=None):
        """Handle 2nd dropdown change (document or project)"""
        selected = self.doc_filter_var.get()
        category = self.cat_filter_var.get()
        
        if category == "Project":
            # This is a project selection
            if selected == "All Projects":
                # Clear project filter, show all documents
                self.proj_doc_filter_var.set("All Documents")
                self.proj_doc_filter.configure(values=["All Documents"])
                self.active_filters['project'] = None
                self.active_filters['document'] = None
            else:
                # Show documents for this project in 3rd dropdown
                # Store mapping: display_name -> name
                if not hasattr(self, 'doc_name_mapping'):
                    self.doc_name_mapping = {}
                
                docs_in_project = []
                for doc in self.all_documents:
                    if doc.get('project') == selected:
                        display = doc.get('display_name', doc['name'])
                        docs_in_project.append(display)
                        self.doc_name_mapping[display] = doc['name']
                
                doc_list = ["All Documents"] + sorted(docs_in_project)
                self.proj_doc_filter_var.set("All Documents")
                self.proj_doc_filter.configure(values=doc_list)
                self.active_filters['project'] = selected
                self.active_filters['document'] = None
        else:
            # This is a document selection from category
            if selected == "All Documents":
                self.active_filters['document'] = None
            else:
                # Convert display name to actual file name for filter
                actual_name = self.doc_name_mapping.get(selected, selected) if hasattr(self, 'doc_name_mapping') else selected
                self.active_filters['document'] = actual_name
                self.active_filters['project'] = None
            # Reset 3rd dropdown
            self.proj_doc_filter_var.set("All Documents")
            self.proj_doc_filter.configure(values=["All Documents"])
        
        self._notify_filter_change()
    
    def _on_project_document_change(self, selection=None):
        """Handle 3rd dropdown change (document from project)"""
        selected = self.proj_doc_filter_var.get()
        
        if selected == "All Documents":
            self.active_filters['document'] = None
        else:
            # Convert display name to actual file name for filter
            actual_name = self.doc_name_mapping.get(selected, selected) if hasattr(self, 'doc_name_mapping') else selected
            self.active_filters['document'] = actual_name
        
        self._notify_filter_change()
    
    def _notify_filter_change(self):
        """Notify parent of filter changes and show status"""
        # Notify parent
        if self.filter_change_callback:
            self.filter_change_callback(self.active_filters)
        
        # Show filter status
        active_count = sum(1 for v in self.active_filters.values() if v is not None)
        if active_count > 0:
            filters_text = []
            if self.active_filters['category']:
                filters_text.append(f"Cat: {self.active_filters['category']}")
            if self.active_filters['project']:
                filters_text.append(f"Proj: {self.active_filters['project']}")
            if self.active_filters['document']:
                filters_text.append(f"Doc: {self.active_filters['document']}")
            
            self.append_message(f"\n🔍 Active Filters: {' | '.join(filters_text)}", "system")
    
    def clear_all_filters(self):
        """Clear all active filters"""
        self.cat_filter_var.set("All Categories")
        self.doc_filter_var.set("All Documents")
        self.proj_doc_filter_var.set("All Documents")
        self.doc_filter.configure(values=["All Documents"])
        self.proj_doc_filter.configure(values=["All Documents"])
        self.active_filters = {
            'document': None,
            'category': None,
            'project': None
        }
        
        if self.filter_change_callback:
            self.filter_change_callback(self.active_filters)
        
        self.append_message("\n✕ All filters cleared", "system")
    
    def update_filter_options(self, documents=None, categories=None, projects=None):
        """Update available filter options
        
        Args:
            documents: List of dicts with {'name': str, 'categories': list, 'project': str}
            categories: List of category names
            projects: List of project names
        """
        if documents:
            self.all_documents = documents
        
        if categories:
            self.all_categories = categories
            # Add "Project" as special category
            cat_list = ["All Categories"] + categories + ["Project"]
            self.cat_filter.configure(values=cat_list)
        
        if projects:
            self.all_projects = projects
    
    def get_active_filters(self):
        """Get currently active filters"""
        return {k: v for k, v in self.active_filters.items() if v is not None}
    
    def update_status_message(self, message):
        """Update or create status message (replaces previous status)
        
        Args:
            message: Status message to display
        """
        self.chat_display.configure(state="normal")
        
        # Find and remove previous status message if exists
        if hasattr(self, '_status_start_index') and self._status_start_index:
            try:
                self.chat_display.delete(self._status_start_index, "end")
            except:
                pass
        
        # Insert new status message
        self._status_start_index = self.chat_display.index("end-1c")
        self.chat_display.insert("end", f"\n{message}\n", "system_tag")
        
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")
    
    def clear_status_message(self):
        """Clear the current status message"""
        if hasattr(self, '_status_start_index') and self._status_start_index:
            self.chat_display.configure(state="normal")
            try:
                self.chat_display.delete(self._status_start_index, "end")
            except:
                pass
            self.chat_display.configure(state="disabled")
            self._status_start_index = None
    
    def _create_chat_display(self):
        """Create scrollable chat display with styled text tags"""
        chat_frame = ctk.CTkFrame(self.main_frame)
        chat_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(10, 10))
        chat_frame.grid_columnconfigure(0, weight=1)
        chat_frame.grid_rowconfigure(0, weight=1)
        
        # Use text-based display with enhanced styling
        self._use_html_rendering = False
        self.chat_display = ctk.CTkTextbox(
            chat_frame,
            font=ctk.CTkFont(size=FONT_SIZES['normal']),
            wrap="word",
            state="disabled"
        )
        self.chat_display.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Configure text tags for styled rendering
        self._configure_text_tags()
    
    def _configure_text_tags(self):
        """Configure text tags for Markdown-style rendering"""
        # Get internal textbox widget
        textbox = self.chat_display._textbox
        
        # Header styles - Blue tones for hierarchy
        textbox.tag_configure("h1", font=ctk.CTkFont(size=22, weight="bold"), foreground="#60a5fa", spacing3=10)
        textbox.tag_configure("h2", font=ctk.CTkFont(size=18, weight="bold"), foreground="#3b82f6", spacing3=8)
        textbox.tag_configure("h3", font=ctk.CTkFont(size=15, weight="bold"), foreground="#2563eb", spacing3=6)
        
        # Emphasis styles
        textbox.tag_configure("bold", font=ctk.CTkFont(weight="bold"), foreground="#ffffff")
        textbox.tag_configure("italic", font=ctk.CTkFont(slant="italic"))
        textbox.tag_configure("code", font=ctk.CTkFont(family="Consolas", size=12), foreground="#e74c3c", background="#2c2c2c")
        
        # List styles
        textbox.tag_configure("bullet", foreground="#9b59b6", lmargin1=20, lmargin2=35)
        textbox.tag_configure("numbered", foreground="#3498db", lmargin1=20, lmargin2=35)
        
        # Table styles
        textbox.tag_configure("table_header", font=ctk.CTkFont(weight="bold"), foreground="#f39c12", background="#2c3e50")
        textbox.tag_configure("table_row", foreground="#ecf0f1", background="#34495e")
        textbox.tag_configure("table_separator", foreground="#7f8c8d")
        
        # Special content styles
        textbox.tag_configure("source_ref", foreground="#95a5a6", font=ctk.CTkFont(size=11))
        textbox.tag_configure("warning", foreground="#e74c3c", font=ctk.CTkFont(weight="bold"))
        textbox.tag_configure("success", foreground="#27ae60", font=ctk.CTkFont(weight="bold"))
        textbox.tag_configure("info", foreground="#3498db")
        textbox.tag_configure("highlight", foreground="#f1c40f", background="#2c3e50")
        
        # Message type tags
        textbox.tag_configure("user_tag", foreground="#e74c3c", font=ctk.CTkFont(size=14, weight="bold"))
        textbox.tag_configure("assistant_tag", foreground="#27ae60", font=ctk.CTkFont(size=14, weight="bold"))
        textbox.tag_configure("system_tag", foreground="#7f8c8d", font=ctk.CTkFont(size=12, slant="italic"))
        textbox.tag_configure("source_tag", foreground="#9b59b6", font=ctk.CTkFont(size=11))
        
        # Document separator for multi-doc results
        textbox.tag_configure("doc_separator", foreground="#3498db", font=ctk.CTkFont(size=13, weight="bold"), spacing1=15, spacing3=5)
        textbox.tag_configure("doc_score", foreground="#f39c12", font=ctk.CTkFont(size=11))
    
    def _render_markdown(self, text):
        """
        Parse and render Markdown-formatted text with styled tags.
        Returns a list of (text, tag) tuples for insertion.
        Tables are marked with special 'TABLE' tag containing table data.
        """
        import re
        
        result = []
        lines = text.split('\n')
        in_table = False
        table_data = []
        
        for line_idx, line in enumerate(lines):
            # Table detection
            if '|' in line and line.strip().startswith('|'):
                cells = [c.strip() for c in line.strip().strip('|').split('|')]
                
                # Check if this is a separator line (---|---|---)
                if all(set(c.strip()).issubset({'-', ':', ' '}) for c in cells if c.strip()):
                    # Table separator line - skip
                    continue
                
                if not in_table:
                    in_table = True
                    table_data = []
                
                table_data.append(cells)
                
                # Check if next line ends table
                next_idx = line_idx + 1
                if next_idx >= len(lines) or not ('|' in lines[next_idx] and lines[next_idx].strip().startswith('|')):
                    # End of table - emit table data
                    result.append((table_data, "TABLE"))
                    in_table = False
                    table_data = []
                continue
            else:
                if in_table and table_data:
                    result.append((table_data, "TABLE"))
                in_table = False
                table_data = []
            
            # Headers
            if line.startswith('### '):
                result.append((line[4:] + '\n', "h3"))
                continue
            elif line.startswith('## '):
                result.append((line[3:] + '\n', "h2"))
                continue
            elif line.startswith('# '):
                result.append((line[2:] + '\n', "h1"))
                continue
            
            # Bullet points
            bullet_match = re.match(r'^(\s*)[-*•]\s+(.+)$', line)
            if bullet_match:
                indent, content = bullet_match.groups()
                # Store bullet as special tuple: (content, "BULLET")
                result.append((content, "BULLET"))
                continue
            
            # Numbered lists
            num_match = re.match(r'^(\s*)(\d+)\.\s+(.+)$', line)
            if num_match:
                indent, num, content = num_match.groups()
                formatted_parts = self._parse_inline_formatting(content)
                result.append((f"  {num}. ", "numbered"))
                result.extend(formatted_parts)
                result.append(("\n", None))
                continue
            
            # Source references (📚, 📄, Source:, etc.)
            if any(marker in line for marker in ['📚', '📄', 'Source:', '[Source', '(Page', 'Reference:']):
                result.append((line + '\n', "source_ref"))
                continue
            
            # Warning/Important lines
            if any(marker in line.lower() for marker in ['warning:', 'important:', 'note:', '⚠', '❗']):
                result.append((line + '\n', "warning"))
                continue
            
            # Success/Conclusion lines  
            if any(marker in line.lower() for marker in ['✓', '✔', 'conclusion:', 'summary:']):
                result.append((line + '\n', "success"))
                continue
            
            # Regular text with inline formatting
            if line.strip():
                formatted_parts = self._parse_inline_formatting(line)
                result.extend(formatted_parts)
                result.append(("\n", None))
            else:
                result.append(("\n", None))
        
        return result
    
    def _parse_inline_formatting(self, text):
        """Parse inline Markdown formatting (bold, italic, code)"""
        import re
        result = []
        
        # Pattern for **bold**, *italic*, `code`
        pattern = r'(\*\*(.+?)\*\*|\*(.+?)\*|`(.+?)`)'
        last_end = 0
        
        for match in re.finditer(pattern, text):
            # Add text before match
            if match.start() > last_end:
                result.append((text[last_end:match.start()], None))
            
            full_match = match.group(0)
            if full_match.startswith('**'):
                result.append((match.group(2), "bold"))
            elif full_match.startswith('`'):
                result.append((match.group(4), "code"))
            elif full_match.startswith('*'):
                result.append((match.group(3), "italic"))
            
            last_end = match.end()
        
        # Add remaining text
        if last_end < len(text):
            result.append((text[last_end:], None))
        
        return result if result else [(text, None)]
    
    def append_styled_message(self, text, message_type="assistant"):
        """
        Append a message with styled Markdown rendering including embedded tables.
        
        Args:
            text: Message text (can contain Markdown)
            message_type: "user", "assistant", "system", "source"
        """
        self.chat_display.configure(state="normal")
        textbox = self.chat_display._textbox
        
        if message_type == "user":
            textbox.insert("end", "\n\n❓ YOU:\n", "user_tag")
            textbox.insert("end", text + "\n")
            self.last_query = text
            self.feedback_frame.grid_remove()
            
        elif message_type == "assistant":
            textbox.insert("end", "\n✅ ASSISTANT:\n", "assistant_tag")
            
            # Render with Markdown formatting including tables
            formatted_parts = self._render_markdown(text)
            for content, tag in formatted_parts:
                if tag == "TABLE":
                    # Insert embedded table widget
                    self._insert_table_widget(textbox, content)
                elif tag == "BULLET":
                    # Insert styled bullet (without feedback buttons)
                    self._insert_styled_bullet(textbox, content)
                elif tag:
                    textbox.insert("end", content, tag)
                else:
                    textbox.insert("end", content)
            
            self.last_response = text
            if self.feedback_callback:
                self.feedback_frame.grid()
                
        elif message_type == "system":
            textbox.insert("end", text + "\n", "system_tag")
            
        elif message_type == "source":
            textbox.insert("end", text + "\n", "source_tag")
        
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")
    
    def _insert_table_widget(self, textbox, table_data):
        """
        Insert a styled table widget into the textbox.
        
        Args:
            textbox: The text widget to insert into
            table_data: List of rows, each row is a list of cell values
        """
        import tkinter as tk
        
        if not table_data:
            return
        
        # Create table frame
        table_frame = tk.Frame(textbox, bg='#1e3a5f', padx=5, pady=5)
        
        # Determine number of columns
        num_cols = max(len(row) for row in table_data)
        
        # Style definitions
        header_bg = '#2563eb'
        header_fg = 'white'
        row_bg_1 = '#2d3748'
        row_bg_2 = '#374151'
        row_fg = '#e5e7eb'
        border_color = '#4b5563'
        
        for row_idx, row in enumerate(table_data):
            is_header = (row_idx == 0)
            
            for col_idx in range(num_cols):
                cell_value = row[col_idx] if col_idx < len(row) else ""
                
                # Choose colors
                if is_header:
                    bg = header_bg
                    fg = header_fg
                    font_weight = 'bold'
                else:
                    bg = row_bg_1 if row_idx % 2 == 1 else row_bg_2
                    fg = row_fg
                    font_weight = 'normal'
                
                # Wrap long text to multiple lines (max 40 chars per line for headers, 50 for data)
                max_chars = 40 if is_header else 50
                if len(cell_value) > max_chars:
                    words = cell_value.split()
                    lines = []
                    current_line = ""
                    for word in words:
                        if not current_line:
                            current_line = word
                        elif len(current_line) + 1 + len(word) <= max_chars:
                            current_line += " " + word
                        else:
                            lines.append(current_line)
                            current_line = word
                    if current_line:
                        lines.append(current_line)
                    cell_value = "\n".join(lines)
                
                # Create cell label with wraplength for all cells
                cell = tk.Label(
                    table_frame,
                    text=cell_value,
                    bg=bg,
                    fg=fg,
                    font=('Segoe UI', 10, font_weight),
                    padx=12,
                    pady=6,
                    relief='flat',
                    borderwidth=1,
                    anchor='center',
                    justify='center',
                    wraplength=300 if is_header else 350  # Auto-wrap at pixel width
                )
                cell.grid(row=row_idx, column=col_idx, sticky='nsew', padx=1, pady=1)
        
        # Configure column weights for equal distribution
        for col in range(num_cols):
            table_frame.grid_columnconfigure(col, weight=1)
        
        # Insert newline before table
        textbox.insert("end", "\n")
        
        # Insert table widget into textbox
        textbox.window_create("end", window=table_frame, padx=10, pady=5)
        
        # Insert newline after table
        textbox.insert("end", "\n\n")
    
    def _insert_styled_bullet(self, textbox, bullet_text):
        """
        Insert a styled bullet point with professional formatting
        
        Args:
            textbox: Text widget to insert into
            bullet_text: Bullet content text
        """
        import tkinter as tk
        import re
        
        # Remove ** markers from text
        cleaned_text = bullet_text.replace('**', '')
        
        # Create frame for bullet
        bullet_frame = tk.Frame(textbox, bg='#1e1e1e')
        
        # Bullet symbol
        bullet_symbol = tk.Label(
            bullet_frame,
            text="  • ",
            bg='#1e1e1e',
            fg='#4ade80',
            font=('Segoe UI', 11, 'bold'),
            anchor='nw'
        )
        bullet_symbol.pack(side=tk.LEFT, anchor='n', padx=(0, 5))
        
        # Check if text has "Label:" format - make label bold
        colon_match = re.match(r'^([^:]+):\s*(.*)$', cleaned_text)
        
        if colon_match:
            # Split into label (bold) and rest (normal)
            label_text = colon_match.group(1)
            rest_text = colon_match.group(2)
            
            # Container for text with mixed formatting (vertical stack)
            text_container = tk.Frame(bullet_frame, bg='#1e1e1e')
            text_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=2)
            
            # Bold label on first line
            label_widget = tk.Label(
                text_container,
                text=label_text + ":",
                bg='#1e1e1e',
                fg='#ffffff',
                font=('Segoe UI', 11, 'bold'),
                justify=tk.LEFT,
                anchor='w'
            )
            label_widget.pack(anchor='w')
            
            # Normal rest text below, indented slightly
            rest_widget = tk.Label(
                text_container,
                text=rest_text,
                bg='#1e1e1e',
                fg='#ffffff',
                font=('Segoe UI', 11),
                justify=tk.LEFT,
                anchor='w',
                wraplength=680
            )
            rest_widget.pack(anchor='w', padx=(0, 0))
        else:
            # No colon - just regular text
            bullet_label = tk.Label(
                bullet_frame,
                text=cleaned_text,
                bg='#1e1e1e',
                fg='#ffffff',
                font=('Segoe UI', 11),
                justify=tk.LEFT,
                anchor='w',
                wraplength=700
            )
            bullet_label.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=2)
        
        # Insert bullet frame into textbox
        textbox.window_create("end", window=bullet_frame, padx=5, pady=2)
        textbox.insert("end", "\n")
    
    def _create_feedback_area(self):
        """Create feedback buttons area"""
        self.feedback_frame = ctk.CTkFrame(self.main_frame, fg_color=COLORS['dark_bg'], height=50)
        self.feedback_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 5))
        self.feedback_frame.grid_remove()  # Hidden by default
        
        # Left side: Quick Actions
        actions_container = ctk.CTkFrame(self.feedback_frame, fg_color="transparent")
        actions_container.pack(side="left", padx=15, pady=10)
        
        # Copy button
        self.copy_btn = ctk.CTkButton(
            actions_container,
            text="📋 Copy",
            command=self._copy_response,
            width=80,
            height=30,
            font=ctk.CTkFont(size=FONT_SIZES['tiny']),
            fg_color="transparent",
            border_width=1
        )
        self.copy_btn.pack(side="left", padx=3)
        
        # Export button
        self.export_btn = ctk.CTkButton(
            actions_container,
            text="📤 Export",
            command=self._export_response,
            width=80,
            height=30,
            font=ctk.CTkFont(size=FONT_SIZES['tiny']),
            fg_color="transparent",
            border_width=1
        )
        self.export_btn.pack(side="left", padx=3)
        
        # Separator
        ctk.CTkLabel(
            actions_container,
            text="|",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack(side="left", padx=10)
        
        # Feedback label
        ctk.CTkLabel(
            actions_container,
            text="Was this helpful?",
            font=ctk.CTkFont(size=FONT_SIZES['tiny'])
        ).pack(side="left", padx=5)
        
        # Thumbs up
        self.thumbs_up_btn = ctk.CTkButton(
            actions_container,
            text="👍",
            command=lambda: self._on_feedback("positive"),
            width=40,
            height=30,
            fg_color=COLORS['success'],
            hover_color=COLORS['success_hover'],
            font=ctk.CTkFont(size=14)
        )
        self.thumbs_up_btn.pack(side="left", padx=3)
        
        # Thumbs down
        self.thumbs_down_btn = ctk.CTkButton(
            actions_container,
            text="👎",
            command=lambda: self._on_feedback("negative"),
            width=40,
            height=30,
            fg_color=COLORS['danger'],
            hover_color=COLORS['danger_hover'],
            font=ctk.CTkFont(size=14)
        )
        self.thumbs_down_btn.pack(side="left", padx=3)
        
        # Comment button
        self.comment_btn = ctk.CTkButton(
            actions_container,
            text="📝",
            command=self._on_comment,
            width=40,
            height=30,
            fg_color="transparent",
            border_width=1,
            font=ctk.CTkFont(size=14)
        )
        self.comment_btn.pack(side="left", padx=5)
    
    def _create_input_area(self):
        """Create message input area"""
        input_frame = ctk.CTkFrame(self.main_frame, corner_radius=0)
        input_frame.grid(row=4, column=0, sticky="ew", padx=0, pady=0)
        input_frame.grid_columnconfigure(0, weight=1)
        
        self.input_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Type your question here... (e.g., What is the current capacity for 2.5mm² cable?)",
            height=50,
            font=ctk.CTkFont(size=FONT_SIZES['medium'])
        )
        self.input_entry.grid(row=0, column=0, padx=(20, 10), pady=20, sticky="ew")
        self.input_entry.bind("<Return>", lambda e: self.send_callback())
        
        self.send_button = ctk.CTkButton(
            input_frame,
            text="Send ➤",
            command=self.send_callback,
            height=50,
            width=120,
            font=ctk.CTkFont(size=FONT_SIZES['medium'], weight="bold")
        )
        self.send_button.grid(row=0, column=1, padx=(0, 20), pady=20)
    
    def display_welcome_message(self):
        """Display welcome message"""
        self.append_message(MESSAGES['welcome'], "system")
    
    def append_message(self, text, sender="user", query=None, sources=None):
        """
        Append message to chat display
        
        Args:
            text: Message text
            sender: Message sender ("user", "assistant", "system", "source")
            query: Original query (for feedback tracking)
            sources: Source documents (for feedback tracking)
        """
        # Use HTML rendering if available
        if hasattr(self, '_use_html_rendering') and self._use_html_rendering:
            self._append_html_message(text, sender)
            if sender == "assistant" and sources:
                self.last_sources = sources
            return
        
        # Fallback to text-based rendering
        self.chat_display.configure(state="normal")
        
        if sender == "user":
            prefix = "\n\n❓ YOU:\n"
            self.chat_display.insert("end", prefix, "user_tag")
            self.chat_display.insert("end", text + "\n")
            # Store query for feedback
            self.last_query = text
            # Hide feedback buttons when new question is asked
            self.feedback_frame.grid_remove()
            
        elif sender == "assistant":
            prefix = "\n✅ ASSISTANT:\n"
            self.chat_display.insert("end", prefix, "assistant_tag")
            self.chat_display.insert("end", text + "\n")
            # Store response for feedback
            self.last_response = text
            if sources:
                self.last_sources = sources
            # Show query analysis if available
            if hasattr(self, 'last_query_analysis') and self.last_query_analysis:
                self._display_query_analysis()
            # Show feedback buttons
            if self.feedback_callback:
                self.feedback_frame.grid()
            
        elif sender == "system":
            self.chat_display.insert("end", text + "\n", "system_tag")
            
        elif sender == "source":
            self.chat_display.insert("end", text + "\n", "source_tag")
        
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")
    
    def _copy_response(self):
        """Copy the last response to clipboard"""
        if self.last_response:
            self.parent.clipboard_clear()
            
            # Format the copy content
            copy_text = f"Question: {self.last_query}\n\nAnswer: {self.last_response}"
            
            # Add sources if available
            if self.last_sources:
                copy_text += "\n\nSources:\n"
                for i, src in enumerate(self.last_sources[:3], 1):
                    copy_text += f"  {i}. {src.get('document', 'Unknown')} (Page {src.get('page', 'N/A')})\n"
            
            self.parent.clipboard_append(copy_text)
            
            # Show confirmation
            self.chat_display.configure(state="normal")
            self.chat_display.insert("end", "\n✅ Copied to clipboard!\n", "system_tag")
            self.chat_display.configure(state="disabled")
            self.chat_display.see("end")
    
    def _export_response(self):
        """Export the last response to PDF"""
        if not self.last_response:
            return
        
        from tkinter import filedialog
        from datetime import datetime
        from src.export_manager import get_export_manager
        
        # Ask for save location
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            initialfile=f"query_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        )
        
        if filename:
            try:
                # Use export manager for professional PDF
                export_manager = get_export_manager()
                
                # Create PDF
                result = export_manager.export_to_pdf(
                    query=self.last_query,
                    response=self.last_response,
                    sources=self.last_sources,
                    metadata={}
                )
                
                if result:
                    # Move to user's selected location
                    import shutil
                    shutil.move(result, filename)
                    
                    # Show confirmation
                    self.chat_display.configure(state="normal")
                    self.chat_display.insert("end", f"\n✅ PDF exported to {filename}\n", "system_tag")
                    self.chat_display.configure(state="disabled")
                    self.chat_display.see("end")
                else:
                    raise Exception("PDF generation failed")
                
            except Exception as e:
                self.chat_display.configure(state="normal")
                self.chat_display.insert("end", f"\n❌ Export failed: {str(e)}\n", "system_tag")
                self.chat_display.configure(state="disabled")
    
    def _on_feedback(self, feedback_type):
        """Handle feedback button click"""
        if not self.feedback_callback or not self.last_query or not self.last_response:
            return
        
        # Call parent callback
        self.feedback_callback(
            query=self.last_query,
            response=self.last_response,
            sources=self.last_sources,
            feedback_type=feedback_type,
            comment=None
        )
        
        # Show confirmation
        emoji = "✅" if feedback_type == "positive" else "📝"
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", f"\n{emoji} Thank you for your feedback!\n", "system_tag")
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")
    
    def _on_comment(self):
        """Handle comment button click - open dialog for comment"""
        from tkinter import simpledialog
        
        if not self.feedback_callback or not self.last_query or not self.last_response:
            return
        
        # Ask for comment
        comment = simpledialog.askstring(
            "Feedback Comment",
            "Please provide additional feedback:",
            parent=self.parent
        )
        
        if comment:
            # Assume negative feedback if they're leaving a comment
            self.feedback_callback(
                query=self.last_query,
                response=self.last_response,
                sources=self.last_sources,
                feedback_type="negative",
                comment=comment
            )
            
            # Show confirmation
            self.chat_display.configure(state="normal")
            self.chat_display.insert("end", f"\n💬 Thank you for your detailed feedback!\n", "system_tag")
            self.chat_display.configure(state="disabled")
            self.chat_display.see("end")
            
            # Hide feedback buttons
            self.feedback_frame.grid_remove()
    
    def _display_query_analysis(self):
        """Display query analysis information"""
        if not self.last_query_analysis:
            return
        
        analysis = self.last_query_analysis
        
        # Format analysis text
        intent = analysis.get('intent', 'unknown')
        weights = analysis.get('weights', {})
        retrieval_info = analysis.get('retrieval_info', {})
        
        # Create readable intent name
        intent_names = {
            'table_lookup': 'Table Lookup',
            'definition': 'Definition',
            'reference': 'Standard Reference',
            'calculation': 'Calculation',
            'general': 'General Query'
        }
        intent_display = intent_names.get(intent, intent.title())
        
        # Format weights
        semantic_w = weights.get('semantic', 0.5)
        keyword_w = weights.get('keyword', 0.3)
        
        # Build analysis text
        analysis_text = f"\n🧠 Query Analysis: {intent_display}"
        analysis_text += f" | Strategy: Semantic {semantic_w:.0%}/Keyword {keyword_w:.0%}"
        
        if retrieval_info:
            semantic_count = retrieval_info.get('semantic_nodes', 0)
            bm25_count = retrieval_info.get('bm25_nodes', 0)
            blended_count = retrieval_info.get('blended_nodes', 0)
            analysis_text += f" | Retrieved: {semantic_count}+{bm25_count}→{blended_count} nodes"
        
        # Add graph info if available
        graph_info = analysis.get('graph_info')
        if graph_info and graph_info.get('references'):
            ref_count = len(graph_info['references'])
            entities = graph_info.get('entities_found', [])
            if entities:
                analysis_text += f" | 🕸️ Graph: {ref_count} cross-refs found"
        
        analysis_text += "\n"
        
        # Insert analysis (using system style for now)
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", analysis_text)
        self.chat_display.configure(state="disabled")
    
    def set_query_analysis(self, analysis):
        """Store query analysis data"""
        self.last_query_analysis = analysis
    
    def clear_chat(self):
        """Clear all chat messages"""
        # Clear HTML content if using HTML rendering
        if hasattr(self, '_use_html_rendering') and self._use_html_rendering:
            self._html_content = []
            self._update_html_display()
        else:
            self.chat_display.configure(state="normal")
            self.chat_display.delete("1.0", "end")
            self.chat_display.configure(state="disabled")
        
        self.chat_history = []
        self.last_query_analysis = None
        self._status_start_index = None
        # Remove follow-up buttons if they exist
        if hasattr(self, 'followup_frame') and self.followup_frame:
            self.followup_frame.destroy()
            self.followup_frame = None
        self.display_welcome_message()
    
    def display_follow_ups(self, questions, callback):
        """Display follow-up question suggestions as clickable buttons
        
        Args:
            questions: List of follow-up question strings
            callback: Function to call when a question is clicked
        """
        if not questions:
            return
        
        # Remove existing follow-up frame if any
        if hasattr(self, 'followup_frame') and self.followup_frame:
            self.followup_frame.destroy()
        
        # Create follow-up frame
        self.followup_frame = ctk.CTkFrame(self.main_frame, fg_color=COLORS['dark_bg'])
        self.followup_frame.grid(row=5, column=0, sticky="ew", padx=20, pady=(5, 10))
        
        # Label
        ctk.CTkLabel(
            self.followup_frame,
            text="💡 Related questions:",
            font=ctk.CTkFont(size=FONT_SIZES['tiny'], weight="bold")
        ).pack(side="left", padx=(15, 10), pady=8)
        
        # Create buttons for each question
        for question in questions:
            btn = ctk.CTkButton(
                self.followup_frame,
                text=question[:50] + ("..." if len(question) > 50 else ""),
                command=lambda q=question: self._on_followup_click(q, callback),
                height=30,
                font=ctk.CTkFont(size=FONT_SIZES['tiny']),
                fg_color="transparent",
                border_width=1,
                text_color=COLORS.get('primary', '#3498db'),
                hover_color=COLORS.get('hover', '#2c3e50')
            )
            btn.pack(side="left", padx=5, pady=8)
    
    def _on_followup_click(self, question, callback):
        """Handle follow-up button click"""
        # Remove follow-up frame
        if hasattr(self, 'followup_frame') and self.followup_frame:
            self.followup_frame.destroy()
            self.followup_frame = None
        # Call the callback with the question
        callback(question)
    
    def get_input(self):
        """Get current input text"""
        return self.input_entry.get().strip()
    
    def clear_input(self):
        """Clear input field"""
        self.input_entry.delete(0, "end")
    
    def set_input_state(self, enabled=True):
        """Enable or disable input controls"""
        state = "normal" if enabled else "disabled"
        self.input_entry.configure(state=state)
        self.send_button.configure(state=state)
