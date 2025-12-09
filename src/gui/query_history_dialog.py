"""
Query History Dialog for PyRAG GUI

Display and manage query history with search functionality.
"""

import customtkinter as ctk
from tkinter import messagebox, ttk
from datetime import datetime
from typing import Optional


class QueryHistoryDialog(ctk.CTkToplevel):
    """Query history viewer with search"""
    
    def __init__(self, parent, query_engine):
        super().__init__(parent)
        
        self.query_engine = query_engine
        self.history = query_engine.query_history
        
        # Window setup
        self.title("📜 Query History")
        self.geometry("1000x700")
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (1000 // 2)
        y = (self.winfo_screenheight() // 2) - (700 // 2)
        self.geometry(f"1000x700+{x}+{y}")
        
        self._setup_ui()
        self._load_history()
    
    def _setup_ui(self):
        """Setup UI components"""
        
        # Configure grid
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Header
        header = ctk.CTkLabel(
            self,
            text="📜 Query History",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        header.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        # Search frame
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")
        search_frame.grid_columnconfigure(0, weight=1)
        
        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="🔍 Search queries...",
            height=40
        )
        self.search_entry.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        self.search_entry.bind("<KeyRelease>", self._on_search)
        
        self.search_btn = ctk.CTkButton(
            search_frame,
            text="Search",
            width=100,
            height=40,
            command=self._search_history
        )
        self.search_btn.grid(row=0, column=1)
        
        self.clear_search_btn = ctk.CTkButton(
            search_frame,
            text="Clear",
            width=80,
            height=40,
            command=self._clear_search
        )
        self.clear_search_btn.grid(row=0, column=2, padx=(10, 0))
        
        # History frame (with scrollbar)
        history_frame = ctk.CTkFrame(self)
        history_frame.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="nsew")
        history_frame.grid_rowconfigure(0, weight=1)
        history_frame.grid_columnconfigure(0, weight=1)
        
        # Create Treeview for history
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", 
                       background="#2b2b2b",
                       foreground="white",
                       fieldbackground="#2b2b2b",
                       borderwidth=0,
                       font=('Segoe UI', 10))
        style.configure("Treeview.Heading",
                       background="#1f1f1f",
                       foreground="white",
                       font=('Segoe UI', 10, 'bold'))
        style.map('Treeview', background=[('selected', '#1f6aa5')])
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(history_frame)
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Treeview
        self.tree = ttk.Treeview(
            history_frame,
            columns=("timestamp", "query", "duration", "sources"),
            show="headings",
            yscrollcommand=scrollbar.set,
            selectmode="browse"
        )
        
        scrollbar.config(command=self.tree.yview)
        
        # Configure columns
        self.tree.heading("timestamp", text="Time")
        self.tree.heading("query", text="Query")
        self.tree.heading("duration", text="Duration")
        self.tree.heading("sources", text="Sources")
        
        self.tree.column("timestamp", width=150, minwidth=150)
        self.tree.column("query", width=500, minwidth=300)
        self.tree.column("duration", width=100, minwidth=80)
        self.tree.column("sources", width=100, minwidth=80)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        
        # Bind double-click to view details
        self.tree.bind("<Double-Button-1>", self._on_double_click)
        
        # Statistics frame
        stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        stats_frame.grid(row=3, column=0, padx=20, pady=(0, 10), sticky="ew")
        
        self.stats_label = ctk.CTkLabel(
            stats_frame,
            text="",
            font=ctk.CTkFont(size=12)
        )
        self.stats_label.pack(side="left", padx=5)
        
        # Button frame
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=4, column=0, padx=20, pady=(0, 20), sticky="ew")
        
        self.view_btn = ctk.CTkButton(
            button_frame,
            text="View Details",
            command=self._view_details,
            width=120
        )
        self.view_btn.pack(side="left", padx=5)
        
        self.export_btn = ctk.CTkButton(
            button_frame,
            text="Export Selected",
            command=self._export_selected,
            width=120
        )
        self.export_btn.pack(side="left", padx=5)
        
        self.close_btn = ctk.CTkButton(
            button_frame,
            text="Close",
            command=self.destroy,
            width=100
        )
        self.close_btn.pack(side="right", padx=5)
    
    def _load_history(self, search_term: Optional[str] = None):
        """Load query history"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        try:
            # Get history
            if search_term:
                queries = self.history.search_queries(search_term)
            else:
                queries = self.history.get_recent_queries(limit=100)
            
            # Populate tree
            for query in queries:
                timestamp = datetime.fromisoformat(query['timestamp']).strftime("%Y-%m-%d %H:%M:%S")
                query_text = query['query'][:100] + "..." if len(query['query']) > 100 else query['query']
                duration = f"{query.get('duration', 0):.2f}s"
                sources = str(len(query.get('sources', [])))
                
                self.tree.insert("", "end", values=(timestamp, query_text, duration, sources), tags=(query['id'],))
            
            # Update statistics
            stats = self.history.get_statistics()
            stats_text = f"Total Queries: {stats['total_queries']} | "
            stats_text += f"Avg Duration: {stats['avg_duration']:.2f}s | "
            stats_text += f"Avg Sources: {stats['avg_sources_per_query']:.1f}"
            self.stats_label.configure(text=stats_text)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load history:\n{str(e)}")
    
    def _on_search(self, event):
        """Handle search on key release"""
        # Only search if user pauses typing (debounce)
        if hasattr(self, '_search_timer'):
            self.after_cancel(self._search_timer)
        self._search_timer = self.after(500, self._search_history)
    
    def _search_history(self):
        """Search query history"""
        search_term = self.search_entry.get().strip()
        if search_term:
            self._load_history(search_term)
        else:
            self._load_history()
    
    def _clear_search(self):
        """Clear search"""
        self.search_entry.delete(0, 'end')
        self._load_history()
    
    def _on_double_click(self, event):
        """Handle double-click on item"""
        self._view_details()
    
    def _view_details(self):
        """View details of selected query"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select a query to view details.")
            return
        
        # Get query ID from tags
        item = selection[0]
        query_id = int(self.tree.item(item, 'tags')[0])
        
        # Get full query details
        try:
            query = self.history.get_query_by_id(query_id)
            if not query:
                messagebox.showerror("Error", "Query not found.")
                return
            
            # Create details dialog
            DetailsDialog(self, query)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load query details:\n{str(e)}")
    
    def _export_selected(self):
        """Export selected query"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select a query to export.")
            return
        
        # Get query ID
        item = selection[0]
        query_id = int(self.tree.item(item, 'tags')[0])
        
        try:
            query = self.history.get_query_by_id(query_id)
            if not query:
                messagebox.showerror("Error", "Query not found.")
                return
            
            # Open export dialog
            from .export_dialog import ExportDialog
            ExportDialog(self, self.query_engine, query)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export query:\n{str(e)}")


class DetailsDialog(ctk.CTkToplevel):
    """Query details viewer"""
    
    def __init__(self, parent, query_data):
        super().__init__(parent)
        
        self.query_data = query_data
        
        # Window setup
        self.title("Query Details")
        self.geometry("800x600")
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (800 // 2)
        y = (self.winfo_screenheight() // 2) - (600 // 2)
        self.geometry(f"800x600+{x}+{y}")
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup UI"""
        
        # Configure grid
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Header
        header = ctk.CTkLabel(
            self,
            text="🔍 Query Details",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        header.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        # Content frame with scrollbar
        content_frame = ctk.CTkScrollableFrame(self)
        content_frame.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="nsew")
        content_frame.grid_columnconfigure(0, weight=1)
        
        # Timestamp
        timestamp = datetime.fromisoformat(self.query_data['timestamp']).strftime("%Y-%m-%d %H:%M:%S")
        ctk.CTkLabel(
            content_frame,
            text=f"⏰ Time: {timestamp}",
            font=ctk.CTkFont(size=12)
        ).grid(row=0, column=0, sticky="w", pady=5)
        
        # Duration
        duration = self.query_data.get('duration', 0)
        ctk.CTkLabel(
            content_frame,
            text=f"⚡ Duration: {duration:.2f}s",
            font=ctk.CTkFont(size=12)
        ).grid(row=1, column=0, sticky="w", pady=5)
        
        # Query
        ctk.CTkLabel(
            content_frame,
            text="❓ Query:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=2, column=0, sticky="w", pady=(10, 5))
        
        query_text = ctk.CTkTextbox(content_frame, height=80, wrap="word")
        query_text.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        query_text.insert("1.0", self.query_data['query'])
        query_text.configure(state="disabled")
        
        # Response
        ctk.CTkLabel(
            content_frame,
            text="💬 Response:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=4, column=0, sticky="w", pady=(10, 5))
        
        response_text = ctk.CTkTextbox(content_frame, height=200, wrap="word")
        response_text.grid(row=5, column=0, sticky="ew", pady=(0, 10))
        response_text.insert("1.0", self.query_data.get('response', 'N/A'))
        response_text.configure(state="disabled")
        
        # Sources
        sources = self.query_data.get('sources', [])
        if sources:
            ctk.CTkLabel(
                content_frame,
                text=f"📚 Sources ({len(sources)}):",
                font=ctk.CTkFont(size=14, weight="bold")
            ).grid(row=6, column=0, sticky="w", pady=(10, 5))
            
            sources_text = ctk.CTkTextbox(content_frame, height=100, wrap="word")
            sources_text.grid(row=7, column=0, sticky="ew", pady=(0, 10))
            
            for i, source in enumerate(sources, 1):
                sources_text.insert("end", f"{i}. {source.get('file_name', 'Unknown')} (Score: {source.get('score', 0):.3f})\n")
            
            sources_text.configure(state="disabled")
        
        # Close button
        close_btn = ctk.CTkButton(
            self,
            text="Close",
            command=self.destroy,
            width=100
        )
        close_btn.grid(row=2, column=0, padx=20, pady=(0, 20))
