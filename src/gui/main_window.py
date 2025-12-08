"""
Main Window for PyRAG GUI

Simplified main window using modular components.
"""

import customtkinter as ctk
import threading
from tkinter import messagebox
from pathlib import Path

from loguru import logger

from ..utils import get_settings, setup_logger
from ..query_engine import QueryEngine
from ..ingestion import DocumentIngestion

from .constants import *
from .sidebar import Sidebar
from .chat import ChatArea
from .dialogs import NewDocumentDialog, SettingsDialog, DatabaseManagerDialog, CrossReferenceDialog, AutoSummaryDialog, AutoSummaryDialog


class PyRAGApp(ctk.CTk):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        # Window configuration
        self.title("PyRAG - Engineering Standards Assistant")
        self.after(0, lambda: self.state('zoomed'))
        self.minsize(WINDOW_SIZES['main_min_width'], WINDOW_SIZES['main_min_height'])
        
        # State variables
        self.query_engine = None
        self.ingestion = None
        self.is_indexing = False
        self.active_filters = {
            'document': None,
            'category': None
        }
        
        # Setup logger
        setup_logger("INFO")
        
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Create components
        self._create_components()
        
        # Initialize system
        self.after(500, self.initialize_system)
    
    def _create_components(self):
        """Create UI components"""
        # Sidebar
        self.sidebar = Sidebar(self, {
            'open_new_document': self.open_new_document_dialog,
            'show_statistics': self.show_statistics,
            'clear_chat': self.clear_chat,
            'open_settings': self.open_settings_dialog,
            'open_database': self.open_database_manager,
            'open_cross_reference': self.open_cross_reference_dialog,
            'open_auto_summary': self.open_auto_summary_dialog,
        })
        
        # Chat area with filter callback
        self.chat = ChatArea(self, self.send_message, self.on_quick_filter_change)
    
    def initialize_system(self):
        """Initialize query engine and load existing documents"""
        try:
            logger.info("🔧 Initializing system...")
            self.chat.append_message("\n⏳ Initializing AI system...", "system")
            
            # Initialize query engine
            self.query_engine = QueryEngine()
            
            # Check if index exists
            stats = self.query_engine.get_stats()
            total_nodes = stats.get('total_nodes', 0)
            
            if total_nodes > 0:
                self.chat.append_message(
                    f"✅ System ready! Loaded {total_nodes:,} document chunks.", 
                    "system"
                )
                logger.success(f"✅ System initialized with {total_nodes} nodes")
                
                # Load available documents and projects for filters
                self._load_filter_options()
            else:
                self.chat.append_message(
                    "⚠️ No documents found. Please add documents to get started.",
                    "system"
                )
                logger.warning("⚠️ No documents in vector store")
            
            # Update sidebar status
            self.sidebar.update_status(embedding_status=True, llm_status=True)
            
        except Exception as e:
            error_msg = f"❌ Failed to initialize: {str(e)}"
            self.chat.append_message(error_msg, "system")
            logger.error(f"Initialization error: {e}")
            self.sidebar.update_status(embedding_status=False, llm_status=False)
    
    def send_message(self):
        """Send user message and get response"""
        question = self.chat.get_input()
        
        if not question:
            return
        
        if not self.query_engine:
            messagebox.showwarning("Not Ready", "System is still initializing. Please wait.")
            return
        
        # Disable input
        self.chat.set_input_state(False)
        self.chat.clear_input()
        
        # Display user message
        self.chat.append_message(question, "user")
        self.chat.append_message("\n🔍 Searching documents...", "system")
        
        # Process in background
        thread = threading.Thread(
            target=self._process_query,
            args=(question,)
        )
        thread.daemon = True
        thread.start()
    
    def _process_query(self, question):
        """Process query in background thread"""
        try:
            # Get active filters from chat component
            active_filters = self.chat.get_active_filters()
            
            # Build filter dict for query engine
            filter_dict = {}
            if active_filters.get('document'):
                filter_dict['document'] = active_filters['document']
            if active_filters.get('category'):
                filter_dict['category'] = active_filters['category']
            if active_filters.get('project'):
                filter_dict['project'] = active_filters['project']
            
            # Get response
            response = self.query_engine.query(question, filters=filter_dict)
            
            # Display response on main thread
            self.after(0, self._display_response, response)
            
        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            self.after(0, self.chat.append_message, error_msg, "system")
            logger.error(f"Query error: {e}")
        finally:
            self.after(0, self.chat.set_input_state, True)
    
    def on_quick_filter_change(self, filters):
        """Handle quick filter changes from chat component"""
        logger.info(f"Quick filters updated: {filters}")
    
    def _load_filter_options(self):
        """Load available documents and projects for filter dropdowns"""
        try:
            from ..utils import load_app_settings
            app_settings = load_app_settings()
            
            # Get categories and projects from settings
            categories = app_settings.get("categories", [])
            projects = app_settings.get("projects", [])
            
            # Get document metadata directly from ChromaDB
            if self.query_engine and hasattr(self.query_engine, 'chroma_collection'):
                doc_metadata = {}
                
                # Get collection
                collection = self.query_engine.chroma_collection
                
                # Get all metadata (limit to first 10000 to avoid memory issues)
                results = collection.get(include=['metadatas'], limit=10000)
                
                # Process metadata
                for metadata in results.get('metadatas', []):
                    # Use file_name for consistency
                    doc_name = metadata.get('file_name', '')
                    if doc_name and doc_name != 'Unknown':
                        if doc_name not in doc_metadata:
                            doc_metadata[doc_name] = {
                                'name': doc_name,
                                'categories': set(),
                                'project': metadata.get('project_name', 'N/A')
                            }
                        
                        # Add categories
                        cats = metadata.get('categories', '')
                        if cats:
                            for cat in cats.split(','):
                                cat = cat.strip()
                                if cat:
                                    doc_metadata[doc_name]['categories'].add(cat)
                
                # Convert to list format with categories as lists
                documents = []
                for doc_name, doc_info in doc_metadata.items():
                    documents.append({
                        'name': doc_name,
                        'categories': list(doc_info['categories']),
                        'project': doc_info['project']
                    })
                
                # Update chat filter options
                self.chat.update_filter_options(
                    documents=documents,
                    categories=categories,
                    projects=projects
                )
                
                logger.info(f"Loaded {len(documents)} documents, {len(categories)} categories, {len(projects)} projects")
            else:
                # Fallback if no index
                self.chat.update_filter_options(
                    documents=[],
                    categories=categories,
                    projects=projects
                )
            
        except Exception as e:
            logger.error(f"Error loading filter options: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def _display_response(self, response):
        """Display query response"""
        # Check if response has error
        if 'error' in response:
            error_msg = f"❌ Error: {response['error']}"
            self.chat.append_message(error_msg, "system")
            return
        
        # Display normal response
        if 'response' in response:
            self.chat.append_message(response['response'], "assistant")
        
            if response.get('sources'):
                sources_text = "\n📚 Sources:\n"
                for i, source in enumerate(response['sources'][:3], 1):
                    doc_name = source.get('document', 'Unknown')
                    page = source.get('page', 'N/A')
                    sources_text += f"   {i}. {doc_name} (Page {page})\n"
                self.chat.append_message(sources_text, "source")
        else:
            # Fallback if response structure is unexpected
            self.chat.append_message("⚠️ Received unexpected response format.", "system")
    
    def open_new_document_dialog(self):
        """Open new document dialog"""
        dialog = NewDocumentDialog(self)
        self.wait_window(dialog)
        
        if hasattr(dialog, 'success') and dialog.success:
            # Reinitialize system after adding documents
            self.initialize_system()
    
    def open_settings_dialog(self):
        """Open settings dialog"""
        dialog = SettingsDialog(self)
        self.wait_window(dialog)
    
    def open_database_manager(self):
        """Open database manager dialog"""
        if not self.query_engine:
            messagebox.showwarning(
                "Not Ready",
                "System is still initializing. Please wait."
            )
            return
        
        dialog = DatabaseManagerDialog(self, self.query_engine)
        self.wait_window(dialog)
        
        # Reload filters after potential metadata changes
        self._load_filter_options()
    
    def open_cross_reference_dialog(self):
        """Open cross-reference analysis dialog"""
        if not self.query_engine:
            messagebox.showwarning(
                "Not Ready",
                "System is still initializing. Please wait."
            )
            return
        
        # Get available documents from the index
        try:
            stats = self.query_engine.get_stats()
            if stats.get('total_nodes', 0) == 0:
                messagebox.showinfo(
                    "No Documents",
                    "Please add documents before using cross-reference analysis."
                )
                return
            
            # Get unique document names from collection metadata
            documents = set()
            try:
                collection = self.query_engine.chroma_collection
                if collection:
                    # Get all metadata
                    result = collection.get(include=['metadatas'])
                    if result and result.get('metadatas'):
                        for metadata in result['metadatas']:
                            # Use file_name directly (with extension) - this is what query_engine expects
                            file_name = metadata.get('file_name', '')
                            if file_name and file_name != 'Unknown':
                                documents.add(file_name)
                        
                        logger.info(f"Found {len(documents)} unique documents: {documents}")
            except Exception as e:
                logger.error(f"Error extracting document names: {e}")
            
            if len(documents) < 2:
                messagebox.showinfo(
                    "Insufficient Documents",
                    "At least 2 documents are required for cross-reference analysis.\n"
                    f"Currently loaded: {len(documents)} document(s)"
                )
                return
            
            dialog = CrossReferenceDialog(self, self.query_engine, sorted(documents))
            
        except Exception as e:
            logger.error(f"Error opening cross-reference dialog: {e}")
            messagebox.showerror(
                "Error",
                f"Failed to open cross-reference dialog:\n{str(e)}"
            )
    
    def open_auto_summary_dialog(self):
        """Open auto-summary generator dialog"""
        if not self.query_engine:
            messagebox.showwarning(
                "Not Ready",
                "System is still initializing. Please wait."
            )
            return
        
        # Get available documents from the index
        try:
            stats = self.query_engine.get_stats()
            if stats.get('total_nodes', 0) == 0:
                messagebox.showinfo(
                    "No Documents",
                    "Please add documents before using auto-summary."
                )
                return
            
            # Get unique document names from collection metadata
            documents = set()
            try:
                collection = self.query_engine.chroma_collection
                if collection:
                    # Get all metadata
                    result = collection.get(include=['metadatas'])
                    if result and result.get('metadatas'):
                        for metadata in result['metadatas']:
                            file_name = metadata.get('file_name', '')
                            if file_name and file_name != 'Unknown':
                                documents.add(file_name)
                        
                        logger.info(f"Found {len(documents)} unique documents: {documents}")
            except Exception as e:
                logger.error(f"Error extracting document names: {e}")
            
            if len(documents) == 0:
                messagebox.showinfo(
                    "No Documents",
                    "No documents found. Please add documents before using auto-summary."
                )
                return
            
            dialog = AutoSummaryDialog(self, self.query_engine, sorted(documents))
            
        except Exception as e:
            logger.error(f"Error opening auto-summary dialog: {e}")
            messagebox.showerror(
                "Error",
                f"Failed to open auto-summary dialog:\n{str(e)}"
            )
    
    def show_statistics(self):
        """Show system statistics"""
        try:
            stats = self.query_engine.get_stats() if self.query_engine else {}
            settings = get_settings()
            
            total_nodes = stats.get('total_nodes', 0)
            collection_name = settings.get_collection_name()
            
            # Get data directory info
            data_dir = Path(settings.data_dir)
            files = list(data_dir.glob("*.pdf")) + list(data_dir.glob("*.txt"))
            total_size = sum(f.stat().st_size for f in files) / (1024 * 1024)
            
            stats_text = f"""
╔════════════════════════════════════════════╗
║        SYSTEM STATISTICS                  ║
╚════════════════════════════════════════════╝

📚 VECTOR DATABASE
   • Active Collection: {collection_name}
   • Total Chunks: {total_nodes:,} nodes
   • Storage: {stats.get('db_path', 'N/A')}

📄 DOCUMENT LIBRARY
   • Files: {len(files)}
   • Total Size: {total_size:.2f} MB

🤖 AI MODELS
   • LLM: {settings.llm_model}
   • Embedding: {settings.embedding_model}
   • Temperature: {settings.llm_temperature}

💰 ESTIMATED COST (per 1000 queries)
   • DeepSeek LLM: ~$0.27
   • OpenAI Embeddings: ~$0.13
   • Total: ~$0.40 for 1000 queries
"""
            messagebox.showinfo("📊 System Statistics", stats_text)
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not retrieve statistics:\n{e}")
    
    def clear_chat(self):
        """Clear chat history"""
        result = messagebox.askyesno(
            "Clear History",
            "Are you sure you want to clear chat history?"
        )
        
        if result:
            self.chat.clear_chat()
            self.chat.append_message("\n🗑️  Chat history cleared", "system")


def main():
    """Launch application"""
    try:
        # Set theme
        ctk.set_appearance_mode(APPEARANCE_MODE)
        ctk.set_default_color_theme(COLOR_THEME)
        
        # Launch app
        app = PyRAGApp()
        app.mainloop()
        
    except Exception as e:
        logger.error(f"Application error: {e}")
        messagebox.showerror("Error", f"Application error:\n{e}")


if __name__ == "__main__":
    main()
