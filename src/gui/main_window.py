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
from .dialogs import NewDocumentDialog, SettingsDialog, DatabaseManagerDialog, CrossReferenceDialog, AutoSummaryDialog


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
        
        # Setup keyboard shortcuts
        self._setup_keyboard_shortcuts()
        
        # Initialize system
        self.after(500, self.initialize_system)
    
    def _setup_keyboard_shortcuts(self):
        """Setup global keyboard shortcuts"""
        # Ctrl+Enter: Send message (alternative)
        self.bind("<Control-Return>", lambda e: self.send_message())
        
        # Ctrl+K: Focus on filter dropdown
        self.bind("<Control-k>", lambda e: self._focus_filter())
        self.bind("<Control-K>", lambda e: self._focus_filter())
        
        # Ctrl+H: Show query history
        self.bind("<Control-h>", lambda e: self.show_history())
        self.bind("<Control-H>", lambda e: self.show_history())
        
        # Ctrl+E: Export results
        self.bind("<Control-e>", lambda e: self.export_results())
        self.bind("<Control-E>", lambda e: self.export_results())
        
        # Ctrl+N: New document
        self.bind("<Control-n>", lambda e: self.open_new_document_dialog())
        self.bind("<Control-N>", lambda e: self.open_new_document_dialog())
        
        # Ctrl+D: Database manager
        self.bind("<Control-d>", lambda e: self.open_database_manager())
        self.bind("<Control-D>", lambda e: self.open_database_manager())
        
        # Ctrl+L: Clear chat
        self.bind("<Control-l>", lambda e: self.clear_chat())
        self.bind("<Control-L>", lambda e: self.clear_chat())
        
        # Ctrl+/: Focus on input
        self.bind("<Control-slash>", lambda e: self._focus_input())
        
        # F1: Show shortcuts help
        self.bind("<F1>", lambda e: self._show_shortcuts_help())
        
        logger.info("⌨️ Keyboard shortcuts enabled")
    
    def _focus_filter(self):
        """Focus on the category filter dropdown"""
        try:
            self.chat.cat_filter.focus_set()
        except:
            pass
    
    def _focus_input(self):
        """Focus on the input entry"""
        try:
            self.chat.input_entry.focus_set()
        except:
            pass
    
    def _show_shortcuts_help(self):
        """Show keyboard shortcuts help dialog"""
        shortcuts = """
⌨️ KEYBOARD SHORTCUTS

📨 Input & Navigation:
  Enter           Send message
  Ctrl + Enter    Send message (alternative)
  Ctrl + /        Focus on input field
  Ctrl + K        Focus on filter dropdown
  Ctrl + L        Clear chat

📁 Documents & Tools:
  Ctrl + N        New document
  Ctrl + D        Database manager
  Ctrl + H        Query history
  Ctrl + E        Export results

❓ Help:
  F1              Show this help
  Esc             Close dialog (in dialogs)
"""
        messagebox.showinfo("Keyboard Shortcuts", shortcuts)
    
    def _create_components(self):
        """Create UI components"""
        # Sidebar
        self.sidebar = Sidebar(self, {
            'open_new_document': self.open_new_document_dialog,
            'show_statistics': self.show_statistics,
            'clear_chat': self.clear_chat,
            'clear_cache': self.clear_cache,
            'open_settings': self.open_settings_dialog,
            'open_database': self.open_database_manager,
            'open_cross_reference': self.open_cross_reference_dialog,
            'open_auto_summary': self.open_auto_summary_dialog,
            'show_history': self.show_history,
            'export_results': self.export_results,
            'view_graph': self.view_graph,
        })
        
        # Chat area with filter callback
        self.chat = ChatArea(self, self.send_message, self.on_quick_filter_change, self.on_feedback)
    
    def initialize_system(self):
        """Initialize query engine and load existing documents"""
        try:
            logger.info("🔧 Initializing system...")
            self.chat.append_message("\n⏳ Initializing AI system...", "system")
            
            # Close existing query engine if any
            if self.query_engine:
                try:
                    self.query_engine.close()
                except:
                    pass
            
            # Initialize query engine
            try:
                self.query_engine = QueryEngine()
            except Exception as e:
                if "already accessed" in str(e):
                    self.chat.append_message("⚠️ Database locked. Please restart application.", "error")
                    logger.error(f"Database lock error: {e}")
                    return
                raise e
            
            # Check if index exists
            stats = self.query_engine.get_stats()
            total_nodes = stats.get('total_nodes', 0)
            
            if total_nodes > 0:
                self.chat.append_message(
                    f"✅ System ready! Loaded {total_nodes:,} document chunks.", 
                    "system"
                )
                logger.success(f"✅ System initialized with {total_nodes} nodes")
            else:
                self.chat.append_message(
                    "⚠️ No documents found. Please add documents to get started.",
                    "system"
                )
                logger.warning("⚠️ No documents in vector store")
            
            # Always load filter options (categories/projects from settings)
            self._load_filter_options()
            
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
        
        # Clear input BEFORE disabling
        self.chat.clear_input()
        
        # Disable input
        self.chat.set_input_state(False)
        
        # Display user message
        self.chat.append_message(question, "user")
        
        # Start dynamic status updates
        self._status_message_id = None
        self._update_status("📊 Analyzing query...")
        
        # Process in background
        thread = threading.Thread(
            target=self._process_query,
            args=(question,)
        )
        thread.daemon = True
        thread.start()
    
    def _update_status(self, message):
        """Update status message in chat (replace previous status)"""
        self.chat.update_status_message(message)
    
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
            
            # Status: Searching
            self.after(0, self._update_status, "🔍 Searching documents...")
            
            # Status: Collecting context
            self.after(500, self._update_status, "📚 Collecting relevant context...")
            
            # Get response
            response = self.query_engine.query(question, filters=filter_dict)
            
            # Status: Generating
            self.after(0, self._update_status, "🧠 Generating answer...")
            
            # Extract query analysis from metadata
            query_analysis = None
            if 'metadata' in response:
                metadata = response['metadata']
                query_analysis = {
                    'intent': metadata.get('query_intent', 'general'),
                    'weights': metadata.get('query_weights', {}),
                    'retrieval_info': metadata.get('retrieval_info', {}),
                    'graph_info': metadata.get('graph_info')
                }
            
            # Display response on main thread
            self.after(0, self._display_response, response, query_analysis)
            
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
            
            # Get document metadata from Qdrant
            doc_metadata = {}
            
            if self.query_engine and hasattr(self.query_engine, 'client'):
                try:
                    collection_name = self.query_engine.settings.get_collection_name()
                    
                    # Check if collection exists first
                    collections = self.query_engine.client.get_collections().collections
                    collection_exists = any(c.name == collection_name for c in collections)
                    
                    if not collection_exists:
                        logger.warning(f"Collection '{collection_name}' does not exist yet")
                        # Still update filter options with empty documents
                        self.chat.update_filter_options(
                            documents=[],
                            categories=categories,
                            projects=projects
                        )
                        return
                    
                    offset = None
                    while True:
                        points, next_offset = self.query_engine.client.scroll(
                            collection_name=collection_name,
                            limit=100,
                            offset=offset,
                            with_payload=True,
                            with_vectors=False
                        )
                        
                        for point in points:
                            metadata = point.payload or {}
                            doc_name = metadata.get('document_name', metadata.get('file_name', ''))
                            file_name = metadata.get('file_name', doc_name)
                            
                            if doc_name and doc_name != 'Unknown':
                                if doc_name not in doc_metadata:
                                    standard_no = metadata.get('standard_no', '')
                                    display_name = standard_no if standard_no else doc_name
                                    
                                    doc_metadata[doc_name] = {
                                        'name': doc_name,
                                        'file_name': file_name,
                                        'display_name': display_name,
                                        'standard_no': standard_no,
                                        'categories': set(),
                                        'project': metadata.get('project_name', 'N/A')
                                    }
                                
                                cats = metadata.get('categories', '')
                                if cats:
                                    for cat in cats.split(','):
                                        cat = cat.strip()
                                        if cat and cat != 'Uncategorized':
                                            doc_metadata[doc_name]['categories'].add(cat)
                                
                                if not doc_metadata[doc_name]['categories']:
                                    doc_metadata[doc_name]['categories'].add('Uncategorized')
                        
                        offset = next_offset
                        if offset is None:
                            break
                except Exception as e:
                    logger.error(f"Error fetching Qdrant metadata: {e}")
                    # Still update filter options with categories/projects even if Qdrant fails
                    self.chat.update_filter_options(
                        documents=[],
                        categories=categories,
                        projects=projects
                    )
                    return
                
                # Convert to list format with categories as lists
                documents = []
                for doc_name, doc_info in doc_metadata.items():
                    documents.append({
                        'name': doc_info['file_name'],  # Use file_name for search filter
                        'display_name': doc_info['display_name'],  # Use display_name for UI
                        'standard_no': doc_info.get('standard_no', ''),  # Add standard_no
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
    
    def _display_response(self, response, query_analysis=None):
        """Display query response
        
        Args:
            response: Query response dict
            query_analysis: Optional query analysis data
        """
        # Clear status message first
        self.chat.clear_status_message()
        
        # Store query analysis in chat
        if query_analysis:
            self.chat.set_query_analysis(query_analysis)
        
        # Check if response has error
        if 'error' in response:
            error_msg = f"❌ Error: {response['error']}"
            self.chat.append_message(error_msg, "system")
            return
        
        # Display normal response
        if 'response' in response:
            self.chat.append_message(response['response'], "assistant")
            
            # Calculate and display confidence score
            sources = response.get('sources', [])
            if sources:
                scores = [s.get('score', 0) for s in sources[:3] if s.get('score')]
                if scores:
                    avg_score = sum(scores) / len(scores)
                    confidence_text = self._format_confidence(avg_score, len(sources))
                    self.chat.append_message(confidence_text, "system")
        
                sources_text = "\n📚 Sources:\n"
                for i, source in enumerate(response['sources'][:3], 1):
                    doc_name = source.get('document', 'Unknown')
                    page = source.get('page', 'N/A')
                    standard_no = source.get('standard_no', '')
                    date = source.get('date', '')
                    # Use actual text snippet, not description metadata
                    text_snippet = source.get('text', '')
                    
                    # Build source line with metadata
                    source_line = f"   {i}. {doc_name}"
                    
                    # Add standard_no if available
                    if standard_no:
                        source_line += f" | {standard_no}"
                    
                    # Add date if available
                    if date:
                        source_line += f" | {date}"
                    
                    # Add page
                    source_line += f" (Page {page})"
                    
                    sources_text += source_line + "\n"
                    
                    # Add text snippet on separate line (first 150 chars)
                    if text_snippet:
                        snippet = text_snippet[:150].replace('\n', ' ').strip()
                        if snippet:
                            sources_text += f"      💬 \"{snippet}...\"\n"
                
                self.chat.append_message(sources_text, "source")
            
            # Generate and display follow-up suggestions
            follow_ups = self._generate_follow_ups(response, query_analysis)
            if follow_ups:
                self.chat.display_follow_ups(follow_ups, self._on_follow_up_click)
        else:
            # Fallback if response structure is unexpected
            self.chat.append_message("⚠️ Received unexpected response format.", "system")
    
    def _format_confidence(self, score, source_count):
        """Format confidence score display
        
        Args:
            score: Average similarity score (0-1)
            source_count: Number of sources found
        """
        percentage = int(score * 100)
        
        if percentage >= 85:
            emoji = "🎯"
            level = "High"
            color_hint = ""
        elif percentage >= 70:
            emoji = "✅"
            level = "Good"
            color_hint = ""
        elif percentage >= 50:
            emoji = "⚠️"
            level = "Moderate"
            color_hint = " - verify manually"
        else:
            emoji = "❗"
            level = "Low"
            color_hint = " - limited sources found"
        
        return f"\n{emoji} Confidence: {percentage}% ({level}{color_hint}) | Based on {source_count} source(s)"
    
    def _generate_follow_ups(self, response, query_analysis):
        """Generate follow-up question suggestions
        
        Args:
            response: Query response
            query_analysis: Query analysis data
            
        Returns:
            List of follow-up question strings
        """
        follow_ups = []
        
        # Get sources to extract topics
        sources = response.get('sources', [])
        if not sources:
            return []
        
        # Extract key topics from response and sources
        response_text = response.get('response', '').lower()
        
        # Common engineering follow-up patterns
        patterns = {
            'cable': ['What is the installation method?', 'What are the derating factors?', 'What is the minimum bending radius?'],
            'lighting': ['What is the color temperature?', 'What are the IP ratings required?', 'What is the warranty period?'],
            'ups': ['What is the battery backup time?', 'What are the maintenance requirements?', 'What is the efficiency rating?'],
            'fire': ['What are the compartmentation requirements?', 'What is the detection coverage?', 'What are the testing intervals?'],
            'electrical': ['What is the earthing system?', 'What are the protection devices?', 'What is the voltage drop limit?'],
            'generator': ['What is the fuel consumption?', 'What are the noise levels?', 'What is the startup time?'],
        }
        
        # Find matching patterns
        for keyword, questions in patterns.items():
            if keyword in response_text:
                # Add 1-2 relevant questions
                for q in questions[:2]:
                    if q not in follow_ups:
                        follow_ups.append(q)
                break
        
        # Add a generic "more details" follow-up if we have sources
        if sources and len(follow_ups) < 3:
            doc_name = sources[0].get('document', '')
            if doc_name:
                follow_ups.append(f"What else does {doc_name[:30]} say about this?")
        
        return follow_ups[:3]  # Max 3 suggestions
    
    def _on_follow_up_click(self, question):
        """Handle follow-up question click
        
        Args:
            question: The follow-up question text
        """
        # Set the question in input and send
        self.chat.input_entry.delete(0, "end")
        self.chat.input_entry.insert(0, question)
        self.send_message()
    
    def on_feedback(self, query, response, sources, feedback_type, comment=None):
        """
        Handle user feedback
        
        Args:
            query: User query
            response: AI response
            sources: Source documents
            feedback_type: 'positive' or 'negative'
            comment: Optional user comment
        """
        if not self.query_engine:
            return
        
        try:
            feedback_id = self.query_engine.add_feedback(
                query=query,
                response=response,
                feedback_type=feedback_type,
                sources=sources,
                comment=comment
            )
            logger.info(f"✅ Feedback recorded (ID: {feedback_id}, Type: {feedback_type})")
        except Exception as e:
            logger.error(f"Failed to record feedback: {e}")
    
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
                # Qdrant Support
                if hasattr(self.query_engine, 'client') and "qdrant" in str(type(self.query_engine.client)).lower():
                    collection_name = self.query_engine.settings.get_collection_name()
                    offset = None
                    while True:
                        points, next_offset = self.query_engine.client.scroll(
                            collection_name=collection_name,
                            limit=100,
                            offset=offset,
                            with_payload=True,
                            with_vectors=False
                        )
                        
                        for point in points:
                            metadata = point.payload or {}
                            file_name = metadata.get('file_name', '')
                            if file_name and file_name != 'Unknown':
                                documents.add(file_name)
                        
                        offset = next_offset
                        if offset is None:
                            break
                        
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
            
            # Get unique document names from Qdrant
            documents = set()
            try:
                if hasattr(self.query_engine, 'client'):
                    collection_name = self.query_engine.settings.get_collection_name()
                    offset = None
                    while True:
                        points, next_offset = self.query_engine.client.scroll(
                            collection_name=collection_name,
                            limit=100,
                            offset=offset,
                            with_payload=True,
                            with_vectors=False
                        )
                        
                        for point in points:
                            metadata = point.payload or {}
                            file_name = metadata.get('file_name', '')
                            if file_name and file_name != 'Unknown':
                                documents.add(file_name)
                        
                        offset = next_offset
                        if offset is None:
                            break
                        
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
            
            # Get cache statistics
            cache_stats = self.query_engine.get_cache_stats() if self.query_engine else {}
            cache_enabled = "error" not in cache_stats
            
            if cache_enabled:
                cache_info = f"""
⚡ SEMANTIC CACHE
   • Status: Enabled ✅
   • Cached Queries: {cache_stats.get('total_entries', 0)}
   • Total Queries: {cache_stats.get('total_queries', 0)}
   • Cache Hits: {cache_stats.get('cache_hits', 0)} ({cache_stats.get('hit_rate_percent', 0):.1f}%)
   • Cache Misses: {cache_stats.get('cache_misses', 0)}
   • Avg Hits/Entry: {cache_stats.get('avg_hits_per_entry', 0):.1f}
   • Similarity Threshold: {cache_stats.get('similarity_threshold', 0.92):.2f}
   • TTL: {cache_stats.get('ttl_days', 7):.0f} days
"""
            else:
                cache_info = """
⚡ SEMANTIC CACHE
   • Status: Disabled ❌
"""
            
            # Get feedback statistics
            feedback_stats = self.query_engine.get_feedback_stats() if self.query_engine else {}
            total_feedback = feedback_stats.get('total_feedback', 0)
            
            if total_feedback > 0:
                satisfaction = feedback_stats.get('satisfaction_rate', 0)
                feedback_info = f"""
💬 USER FEEDBACK (Active Learning)
   • Total Feedback: {total_feedback}
   • Positive: {feedback_stats.get('positive_count', 0)} 👍
   • Negative: {feedback_stats.get('negative_count', 0)} 👎
   • Satisfaction Rate: {satisfaction:.1f}%
   • Status: Learning from feedback ✅
"""
            else:
                feedback_info = """
💬 USER FEEDBACK (Active Learning)
   • No feedback yet
   • Use 👍/👎 buttons to help improve answers
"""
            
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
{cache_info}{feedback_info}
💰 ESTIMATED COST (per 1000 queries)
   • DeepSeek LLM: ~$0.27
   • OpenAI Embeddings: ~$0.13
   • Cache savings: ~{cache_stats.get('hit_rate_percent', 0):.0f}% reduction
   • Total: ~${0.40 * (1 - cache_stats.get('hit_rate_percent', 0)/100):.2f} for 1000 queries
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
    
    def clear_cache(self):
        """Clear semantic cache"""
        if not self.query_engine:
            messagebox.showwarning("Warning", "System not initialized yet")
            return
        
        # Get cache stats before clearing
        cache_stats = self.query_engine.get_cache_stats()
        total_entries = cache_stats.get('total_entries', 0)
        
        if total_entries == 0:
            messagebox.showinfo("Cache Empty", "Cache is already empty. Nothing to clear.")
            return
        
        result = messagebox.askyesno(
            "Clear Cache",
            f"Are you sure you want to clear the semantic cache?\n\n"
            f"• Cached queries: {total_entries}\n"
            f"• Cache hits: {cache_stats.get('cache_hits', 0)}\n"
            f"• Hit rate: {cache_stats.get('hit_rate_percent', 0):.1f}%\n\n"
            f"This will force all future queries to regenerate answers."
        )
        
        if result:
            self.query_engine.clear_cache()
            self.chat.append_message("\n⚡ Semantic cache cleared successfully", "system")
            messagebox.showinfo("Success", f"Cache cleared!\n\n{total_entries} cached queries removed.")
    
    def show_history(self):
        """Show query history dialog"""
        if not self.query_engine:
            messagebox.showwarning(
                "Not Ready",
                "System is still initializing. Please wait."
            )
            return
        
        try:
            from .dialogs import QueryHistoryDialog
            dialog = QueryHistoryDialog(self, self.query_engine)
        except Exception as e:
            logger.error(f"Error opening query history dialog: {e}")
            messagebox.showerror(
                "Error",
                f"Failed to open query history:\n{str(e)}"
            )
    
    def export_results(self):
        """Export last query result"""
        if not self.query_engine:
            messagebox.showwarning(
                "Not Ready",
                "System is still initializing. Please wait."
            )
            return
        
        try:
            # Get last query from history
            history = self.query_engine.query_history
            recent = history.get_recent(limit=1)
            
            if not recent:
                messagebox.showinfo(
                    "No Data",
                    "No query results to export. Please run a query first."
                )
                return
            
            last_query = recent[0]
            
            # Open export dialog
            from .dialogs import ExportDialog
            dialog = ExportDialog(self, self.query_engine, last_query)
            
        except Exception as e:
            logger.error(f"Error opening export dialog: {e}")
            messagebox.showerror(
                "Error",
                f"Failed to open export dialog:\n{str(e)}"
            )
    
    def view_graph(self):
        """View knowledge graph visualization"""
        if not self.query_engine:
            messagebox.showwarning(
                "Not Ready",
                "System is still initializing. Please wait."
            )
            return
        
        try:
            # Check if Neo4j/graph is available
            has_neo4j = False
            if hasattr(self.query_engine, 'graph_retriever') and self.query_engine.graph_retriever:
                if hasattr(self.query_engine.graph_retriever, 'graph_manager') and self.query_engine.graph_retriever.graph_manager:
                    has_neo4j = True
            
            if not has_neo4j:
                messagebox.showinfo(
                    "Feature Unavailable",
                    "Graph visualization requires Neo4j to be configured.\n\n"
                    "This feature shows relationships between documents and concepts."
                )
                return
            
            # Initialize graph visualizer if not already done
            if not hasattr(self.query_engine, 'graph_visualizer') or not self.query_engine.graph_visualizer:
                try:
                    # Get Neo4j credentials from graph_retriever
                    graph_manager = self.query_engine.graph_retriever.graph_manager
                    from src.graph_visualizer import get_graph_visualizer
                    self.query_engine.graph_visualizer = get_graph_visualizer(
                        neo4j_uri=graph_manager.uri,
                        neo4j_user=graph_manager.user,
                        neo4j_password=graph_manager.password
                    )
                    
                    if not self.query_engine.graph_visualizer:
                        raise Exception("Failed to create graph visualizer")
                        
                except Exception as e:
                    logger.error(f"Failed to initialize graph visualizer: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    messagebox.showerror(
                        "Feature Unavailable",
                        "Graph visualization requires Neo4j to be configured.\n\n"
                        f"Error: {str(e)}"
                    )
                    return
            
            # Open graph visualization dialog
            from .dialogs import GraphVisualizationDialog
            dialog = GraphVisualizationDialog(self, self.query_engine)
            
        except Exception as e:
            logger.error(f"Error opening graph visualization: {e}")
            messagebox.showerror(
                "Error",
                f"Failed to open graph visualization:\n{str(e)}"
            )


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
        import traceback
        logger.error(f"Application error: {e}")
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        messagebox.showerror("Error", f"Application error:\n{e}")


if __name__ == "__main__":
    main()
