"""
Chat Component for PyRAG GUI

Handles chat display, message rendering, and quick filters.
"""

import customtkinter as ctk
from .constants import *


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
        
        # Main frame
        self.main_frame = ctk.CTkFrame(parent, corner_radius=0)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(2, weight=1)  # Chat display expands
        
        self._create_header()
        self._create_quick_filter()
        self._create_chat_display()
        self._create_feedback_area()
        self._create_input_area()
        self.display_welcome_message()
    
    def _create_header(self):
        """Create chat header"""
        header_frame = ctk.CTkFrame(self.main_frame, height=60, corner_radius=0)
        header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            header_frame,
            text="💬 Ask Your Questions",
            font=ctk.CTkFont(size=FONT_SIZES['subtitle'], weight="bold")
        ).grid(row=0, column=0, padx=30, pady=15, sticky="w")
    
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
                if selected in doc.get('categories', []):
                    display = doc.get('display_name', doc['name'])
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
    
    def _create_chat_display(self):
        """Create scrollable chat display"""
        chat_frame = ctk.CTkFrame(self.main_frame)
        chat_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(10, 10))
        chat_frame.grid_columnconfigure(0, weight=1)
        chat_frame.grid_rowconfigure(0, weight=1)
        
        self.chat_display = ctk.CTkTextbox(
            chat_frame,
            font=ctk.CTkFont(size=FONT_SIZES['normal']),
            wrap="word",
            state="disabled"
        )
        self.chat_display.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
    
    def _create_feedback_area(self):
        """Create feedback buttons area"""
        self.feedback_frame = ctk.CTkFrame(self.main_frame, fg_color=COLORS['dark_bg'], height=50)
        self.feedback_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 10))
        self.feedback_frame.grid_remove()  # Hidden by default
        
        # Left side: Label
        ctk.CTkLabel(
            self.feedback_frame,
            text="💬 Was this answer helpful?",
            font=ctk.CTkFont(size=FONT_SIZES['small'])
        ).pack(side="left", padx=15, pady=10)
        
        # Right side: Buttons
        btn_container = ctk.CTkFrame(self.feedback_frame, fg_color="transparent")
        btn_container.pack(side="right", padx=15, pady=10)
        
        # Thumbs up
        self.thumbs_up_btn = ctk.CTkButton(
            btn_container,
            text="👍 Helpful",
            command=lambda: self._on_feedback("positive"),
            width=100,
            height=35,
            fg_color=COLORS['success'],
            hover_color=COLORS['success_hover'],
            font=ctk.CTkFont(size=FONT_SIZES['tiny'])
        )
        self.thumbs_up_btn.pack(side="left", padx=5)
        
        # Thumbs down
        self.thumbs_down_btn = ctk.CTkButton(
            btn_container,
            text="👎 Not Helpful",
            command=lambda: self._on_feedback("negative"),
            width=120,
            height=35,
            fg_color=COLORS['danger'],
            hover_color=COLORS['danger_hover'],
            font=ctk.CTkFont(size=FONT_SIZES['tiny'])
        )
        self.thumbs_down_btn.pack(side="left", padx=5)
        
        # Comment button
        self.comment_btn = ctk.CTkButton(
            btn_container,
            text="📝 Comment",
            command=self._on_comment,
            width=100,
            height=35,
            fg_color="transparent",
            border_width=1,
            font=ctk.CTkFont(size=FONT_SIZES['tiny'])
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
            # Show feedback buttons
            if self.feedback_callback:
                self.feedback_frame.grid()
            
        elif sender == "system":
            self.chat_display.insert("end", text + "\n", "system_tag")
            
        elif sender == "source":
            self.chat_display.insert("end", text + "\n", "source_tag")
        
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")
    
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
        
        # Hide feedback buttons
        self.feedback_frame.grid_remove()
    
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
    
    def clear_chat(self):
        """Clear all chat messages"""
        self.chat_display.configure(state="normal")
        self.chat_display.delete("1.0", "end")
        self.chat_display.configure(state="disabled")
        self.chat_history = []
        self.display_welcome_message()
    
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
