"""
Database Manager Dialog

Dialog for editing document metadata in the Qdrant collection.
"""

import customtkinter as ctk
from tkinter import messagebox

from loguru import logger

from ..utils import load_app_settings
from .constants import *


class DatabaseManagerDialog(ctk.CTkToplevel):
    """Database management dialog for editing document metadata"""
    
    def __init__(self, parent, query_engine):
        super().__init__(parent)
        
        self.parent = parent
        self.query_engine = query_engine
        self.title("Database Manager")
        
        # Window size
        width = 900
        height = 750
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        pos_x = (screen_w - width) // 2
        pos_y = (screen_h - height) // 2
        self.geometry(f"{width}x{height}+{pos_x}+{pos_y}")
        self.resizable(True, True)
        
        self.transient(parent)
        self.grab_set()
        
        # State
        self.documents = []
        self.selected_doc = None
        self.app_settings = load_app_settings()
        
        self.create_widgets()
        self.load_documents()
    
    def create_widgets(self):
        """Create database manager UI"""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=25, pady=(25, 10), sticky="ew")
        header_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(
            header_frame,
            text="🗄️ Database Manager",
            font=ctk.CTkFont(size=FONT_SIZES['subtitle'], weight="bold")
        ).grid(row=0, column=0, sticky="w")
        
        self.doc_count_label = ctk.CTkLabel(
            header_frame,
            text="0 documents",
            font=ctk.CTkFont(size=FONT_SIZES['small']),
            text_color="gray"
        )
        self.doc_count_label.grid(row=0, column=1, sticky="e")
        
        # Main content - split view
        content_frame = ctk.CTkFrame(self)
        content_frame.grid(row=1, column=0, padx=25, pady=10, sticky="nsew")
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_columnconfigure(1, weight=2)
        content_frame.grid_rowconfigure(0, weight=1)
        
        # Left: Document list
        self._create_document_list(content_frame)
        
        # Right: Edit panel
        self._create_edit_panel(content_frame)
        
        # Bottom buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=2, column=0, padx=25, pady=(0, 25), sticky="ew")
        btn_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkButton(
            btn_frame,
            text="🔄 Refresh",
            command=self.load_documents,
            width=100,
            height=36,
            fg_color="transparent",
            border_width=2
        ).pack(side="left")
        
        ctk.CTkButton(
            btn_frame,
            text="Close",
            command=self.destroy,
            width=100,
            height=36
        ).pack(side="right")
    
    def _create_document_list(self, parent):
        """Create document list panel"""
        list_frame = ctk.CTkFrame(parent)
        list_frame.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="nsew")
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(
            list_frame,
            text="📚 Documents",
            font=ctk.CTkFont(size=FONT_SIZES['large'], weight="bold")
        ).grid(row=0, column=0, padx=15, pady=(15, 10), sticky="w")
        
        # Scrollable list
        self.doc_scroll = ctk.CTkScrollableFrame(list_frame, height=400)
        self.doc_scroll.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        self.doc_scroll.grid_columnconfigure(0, weight=1)
    
    def _create_edit_panel(self, parent):
        """Create edit panel"""
        edit_frame = ctk.CTkScrollableFrame(parent)
        edit_frame.grid(row=0, column=1, padx=(5, 10), pady=10, sticky="nsew")
        edit_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            edit_frame,
            text="✏️ Edit Document",
            font=ctk.CTkFont(size=FONT_SIZES['large'], weight="bold")
        ).grid(row=0, column=0, padx=15, pady=(15, 20), sticky="w")
        
        # Document name
        ctk.CTkLabel(
            edit_frame,
            text="Document Name:",
            font=ctk.CTkFont(size=FONT_SIZES['small'], weight="bold")
        ).grid(row=1, column=0, padx=15, pady=(0, 5), sticky="w")
        
        self.name_entry = ctk.CTkEntry(
            edit_frame,
            placeholder_text="Document name",
            height=36
        )
        self.name_entry.grid(row=2, column=0, padx=15, pady=(0, 15), sticky="ew")
        
        # Category dropdown
        ctk.CTkLabel(
            edit_frame,
            text="Category:",
            font=ctk.CTkFont(size=FONT_SIZES['small'], weight="bold")
        ).grid(row=3, column=0, padx=15, pady=(0, 5), sticky="w")
        
        self.category_var = ctk.StringVar(value="Select category")
        self.category_menu = ctk.CTkOptionMenu(
            edit_frame,
            variable=self.category_var,
            values=self.app_settings.get("categories", []),
            height=36
        )
        self.category_menu.grid(row=4, column=0, padx=15, pady=(0, 15), sticky="ew")
        
        # Project dropdown
        ctk.CTkLabel(
            edit_frame,
            text="Project:",
            font=ctk.CTkFont(size=FONT_SIZES['small'], weight="bold")
        ).grid(row=5, column=0, padx=15, pady=(0, 5), sticky="w")
        
        self.project_var = ctk.StringVar(value="N/A")
        project_list = ["N/A"] + self.app_settings.get("projects", [])
        self.project_menu = ctk.CTkOptionMenu(
            edit_frame,
            variable=self.project_var,
            values=project_list,
            height=36
        )
        self.project_menu.grid(row=6, column=0, padx=15, pady=(0, 15), sticky="ew")
        
        # Standard No
        ctk.CTkLabel(
            edit_frame,
            text="Standard No:",
            font=ctk.CTkFont(size=FONT_SIZES['small'], weight="bold")
        ).grid(row=7, column=0, padx=15, pady=(0, 5), sticky="w")
        
        self.standard_no_entry = ctk.CTkEntry(
            edit_frame,
            placeholder_text="e.g., IEC 60364-5-52",
            height=36
        )
        self.standard_no_entry.grid(row=8, column=0, padx=15, pady=(0, 15), sticky="ew")
        
        # Date
        ctk.CTkLabel(
            edit_frame,
            text="Date:",
            font=ctk.CTkFont(size=FONT_SIZES['small'], weight="bold")
        ).grid(row=9, column=0, padx=15, pady=(0, 5), sticky="w")
        
        self.date_entry = ctk.CTkEntry(
            edit_frame,
            placeholder_text="e.g., 2024-03",
            height=36
        )
        self.date_entry.grid(row=10, column=0, padx=15, pady=(0, 15), sticky="ew")
        
        # Description
        ctk.CTkLabel(
            edit_frame,
            text="Description:",
            font=ctk.CTkFont(size=FONT_SIZES['small'], weight="bold")
        ).grid(row=11, column=0, padx=15, pady=(0, 5), sticky="w")
        
        self.description_entry = ctk.CTkEntry(
            edit_frame,
            placeholder_text="Brief description",
            height=36
        )
        self.description_entry.grid(row=12, column=0, padx=15, pady=(0, 25), sticky="ew")
        
        # Action buttons
        self.update_btn = ctk.CTkButton(
            edit_frame,
            text="💾 Update Document",
            command=self.update_document,
            height=40,
            state="disabled",
            fg_color=COLORS['primary'],
            hover_color=COLORS['primary_hover'],
            font=ctk.CTkFont(size=FONT_SIZES['normal'], weight="bold")
        )
        self.update_btn.grid(row=13, column=0, padx=15, pady=(0, 10), sticky="ew")
        
        self.delete_btn = ctk.CTkButton(
            edit_frame,
            text="🗑️ Delete Document",
            command=self.delete_document,
            height=40,
            state="disabled",
            fg_color=COLORS['danger'],
            hover_color=COLORS['danger_hover'],
            font=ctk.CTkFont(size=FONT_SIZES['normal'])
        )
        self.delete_btn.grid(row=14, column=0, padx=15, pady=(0, 15), sticky="ew")
        
        # Info label
        self.info_label = ctk.CTkLabel(
            edit_frame,
            text="← Select a document to edit",
            font=ctk.CTkFont(size=FONT_SIZES['tiny']),
            text_color="gray"
        )
        self.info_label.grid(row=15, column=0, padx=15, pady=(10, 0), sticky="w")
    
    def load_documents(self):
        """Load documents from database"""
        try:
            # Clear existing
            for widget in self.doc_scroll.winfo_children():
                widget.destroy()
            
            self.documents = []
            
            # Check for Qdrant
            if not hasattr(self.query_engine, 'client'):
                self.info_label.configure(text="⚠️ Database not available")
                return
            
            # Get all documents from Qdrant
            client = self.query_engine.client
            collection_name = self.query_engine.settings.get_collection_name()
            
            # Group by document name
            doc_map = {}
            offset = None
            
            while True:
                points, next_offset = client.scroll(
                    collection_name=collection_name,
                    limit=100,
                    offset=offset,
                    with_payload=True,
                    with_vectors=False
                )
                
                for point in points:
                    metadata = point.payload or {}
                    doc_name = metadata.get('document_name', metadata.get('file_name', ''))
                    if doc_name and doc_name != 'Unknown':
                        if doc_name not in doc_map:
                            doc_map[doc_name] = {
                                'name': doc_name,
                                'category': metadata.get('categories', ''),
                                'project': metadata.get('project_name', 'N/A'),
                                'standard_no': metadata.get('standard_no', ''),
                                'date': metadata.get('date', ''),
                                'description': metadata.get('description', ''),
                                'count': 0
                            }
                        doc_map[doc_name]['count'] += 1
                
                offset = next_offset
                if offset is None:
                    break
            
            self.documents = list(doc_map.values())
            self.doc_count_label.configure(text=f"{len(self.documents)} documents")
            
            # Create buttons
            for idx, doc in enumerate(sorted(self.documents, key=lambda x: x['name'])):
                btn = ctk.CTkButton(
                    self.doc_scroll,
                    text=f"📄 {doc['name']} ({doc['count']} nodes)",
                    command=lambda d=doc: self.select_document(d),
                    height=36,
                    anchor="w",
                    fg_color="transparent",
                    hover_color=COLORS['dark_bg'],
                    border_width=1,
                    font=ctk.CTkFont(size=FONT_SIZES['small'])
                )
                btn.grid(row=idx, column=0, pady=2, sticky="ew")
            
            self.info_label.configure(text=f"✅ Loaded {len(self.documents)} documents")
            
        except Exception as e:
            logger.error(f"Error loading documents: {e}")
            self.info_label.configure(text=f"❌ Error: {str(e)}")
    
    def select_document(self, doc):
        """Select a document for editing"""
        self.selected_doc = doc
        
        # Populate fields
        self.name_entry.delete(0, "end")
        self.name_entry.insert(0, doc['name'])
        self.category_var.set(doc['category'])
        self.project_var.set(doc['project'])
        
        self.standard_no_entry.delete(0, "end")
        self.standard_no_entry.insert(0, doc.get('standard_no', ''))
        
        self.date_entry.delete(0, "end")
        self.date_entry.insert(0, doc.get('date', ''))
        
        self.description_entry.delete(0, "end")
        self.description_entry.insert(0, doc.get('description', ''))
        
        # Enable buttons
        self.update_btn.configure(state="normal")
        self.delete_btn.configure(state="normal")
        
        self.info_label.configure(
            text=f"✏️ Editing: {doc['name']} | {doc['count']} nodes",
            text_color=COLORS['primary']
        )
    
    def update_document(self):
        """Update document metadata"""
        if not self.selected_doc:
            return
        
        new_name = self.name_entry.get().strip()
        new_category = self.category_var.get()
        new_project = self.project_var.get()
        new_standard_no = self.standard_no_entry.get().strip()
        new_date = self.date_entry.get().strip()
        new_description = self.description_entry.get().strip()
        
        if not new_name:
            messagebox.showwarning("Invalid Name", "Document name cannot be empty.")
            return
        
        # First confirmation
        result = messagebox.askyesno(
            "Update Document",
            f"Update all chunks of '{self.selected_doc['name']}'?\n\n"
            f"New name: {new_name}\n"
            f"New category: {new_category}\n"
            f"New project: {new_project}\n"
            f"Standard No: {new_standard_no}\n"
            f"Date: {new_date}\n"
            f"Description: {new_description}\n\n"
            f"Total nodes to update: {self.selected_doc['count']}",
            icon='question'
        )
        
        if not result:
            return
        
        # Second confirmation
        confirm = messagebox.askyesno(
            "⚠️ Final Confirmation",
            f"This will update {self.selected_doc['count']} database nodes.\n\n"
            f"Are you absolutely sure you want to proceed?",
            icon='warning'
        )
        
        if not confirm:
            return
        
        try:
            client = self.query_engine.client
            collection_name = self.query_engine.settings.get_collection_name()
            
            # Get all points for this document
            points_to_update = []
            offset = None
            
            while True:
                points, next_offset = client.scroll(
                    collection_name=collection_name,
                    limit=100,
                    offset=offset,
                    with_payload=True,
                    with_vectors=True,  # Need vectors to update
                    scroll_filter={
                        "must": [
                            {"key": "document_name", "match": {"value": self.selected_doc['name']}}
                        ]
                    }
                )
                
                for point in points:
                    # Update payload
                    new_payload = point.payload.copy() if point.payload else {}
                    new_payload['document_name'] = new_name
                    new_payload['categories'] = new_category
                    new_payload['project_name'] = new_project
                    if new_standard_no:
                        new_payload['standard_no'] = new_standard_no
                    if new_date:
                        new_payload['date'] = new_date
                    if new_description:
                        new_payload['description'] = new_description
                    
                    points_to_update.append({
                        'id': point.id,
                        'payload': new_payload
                    })
                
                offset = next_offset
                if offset is None:
                    break
            
            # Update points using set_payload
            from qdrant_client.models import PointIdsList
            for point_info in points_to_update:
                client.set_payload(
                    collection_name=collection_name,
                    payload=point_info['payload'],
                    points=[point_info['id']]
                )
            
            messagebox.showinfo(
                "Success",
                f"Updated {len(points_to_update)} nodes successfully!"
            )
            
            # Refresh
            self.load_documents()
            self.selected_doc = None
            self.name_entry.delete(0, "end")
            self.update_btn.configure(state="disabled")
            self.delete_btn.configure(state="disabled")
                
        except Exception as e:
            logger.error(f"Error updating document: {e}")
            messagebox.showerror("Error", f"Failed to update document:\n{str(e)}")
    
    def delete_document(self):
        """Delete document from database"""
        if not self.selected_doc:
            return
        
        # First confirmation
        result = messagebox.askyesno(
            "⚠️ Delete Document",
            f"Are you sure you want to delete '{self.selected_doc['name']}'?\n\n"
            f"This will remove all {self.selected_doc['count']} nodes from the database.\n"
            f"This action cannot be undone!",
            icon='warning'
        )
        
        if not result:
            return
        
        # Second confirmation
        final_confirm = messagebox.askyesno(
            "⛔ FINAL CONFIRMATION",
            f"Last chance to cancel!\n\n"
            f"Document: {self.selected_doc['name']}\n"
            f"Nodes to delete: {self.selected_doc['count']}\n\n"
            f"Are you absolutely certain you want to proceed?",
            icon='warning'
        )
        
        if not final_confirm:
            return
        
        try:
            client = self.query_engine.client
            collection_name = self.query_engine.settings.get_collection_name()
            
            # Get all point IDs for this document
            points_to_delete = []
            offset = None
            
            while True:
                points, next_offset = client.scroll(
                    collection_name=collection_name,
                    limit=100,
                    offset=offset,
                    with_payload=False,
                    with_vectors=False,
                    scroll_filter={
                        "must": [
                            {"key": "document_name", "match": {"value": self.selected_doc['name']}}
                        ]
                    }
                )
                
                for point in points:
                    points_to_delete.append(point.id)
                
                offset = next_offset
                if offset is None:
                    break
            
            if points_to_delete:
                # Delete all points
                from qdrant_client.models import PointIdsList
                client.delete(
                    collection_name=collection_name,
                    points_selector=PointIdsList(points=points_to_delete)
                )
                
                messagebox.showinfo(
                    "Success",
                    f"Deleted {len(points_to_delete)} nodes of '{self.selected_doc['name']}'!"
                )
                
                # Refresh
                self.load_documents()
                self.selected_doc = None
                self.name_entry.delete(0, "end")
                self.update_btn.configure(state="disabled")
                self.delete_btn.configure(state="disabled")
                
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            messagebox.showerror("Error", f"Failed to delete document:\n{str(e)}")

