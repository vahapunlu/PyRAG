"""
PyRAG - Modern Windows Desktop Application

Professional GUI interface using CustomTkinter for Windows users.
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox, scrolledtext
import threading
import sys
from pathlib import Path
from datetime import datetime
import json

# Add src to path
sys.path.append(str(Path(__file__).parent))

from src.utils import get_settings, setup_logger, validate_pdf_files
from src.query_engine import QueryEngine
from src.ingestion import DocumentIngestion
from loguru import logger


# Set appearance and theme
ctk.set_appearance_mode("dark")  # Modes: "System" (default), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (default), "green", "dark-blue"


class PyRAGApp(ctk.CTk):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        # Window configuration
        self.title("PyRAG - Engineering Standards Assistant")
        self.geometry("1200x800")
        self.minsize(1000, 700)
        
        # Center window
        self.center_window()
        
        # Variables
        self.query_engine = None
        self.ingestion = None
        self.chat_history = []
        self.is_indexing = False
        
        # Setup logger
        setup_logger("INFO")
        
        # Create UI
        self.create_widgets()
        
        # Try to load existing index
        self.after(500, self.initialize_system)
    
    def center_window(self):
        """Center window on screen"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
    
    def create_widgets(self):
        """Create all UI widgets"""
        
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # ========== SIDEBAR ==========
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar.grid_rowconfigure(8, weight=1)
        
        # Logo/Title
        self.logo_label = ctk.CTkLabel(
            self.sidebar, 
            text="⚡ PyRAG",
            font=ctk.CTkFont(size=32, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        self.subtitle_label = ctk.CTkLabel(
            self.sidebar,
            text="Engineering Standards AI",
            font=ctk.CTkFont(size=12)
        )
        self.subtitle_label.grid(row=1, column=0, padx=20, pady=(0, 20))
        
        # System Status
        self.status_frame = ctk.CTkFrame(self.sidebar)
        self.status_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        
        self.status_frame.grid_columnconfigure(1, weight=1)
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="⚙️ API Status",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.status_label.grid(row=0, column=0, padx=10, pady=(10, 5), columnspan=2, sticky="w")
        
        # DeepSeek Status
        self.deepseek_label = ctk.CTkLabel(
            self.status_frame,
            text="🤖 DeepSeek",
            font=ctk.CTkFont(size=11),
            anchor="w"
        )
        self.deepseek_label.grid(row=1, column=0, padx=10, pady=2, sticky="w")
        
        self.deepseek_indicator = ctk.CTkLabel(
            self.status_frame,
            text="●",
            font=ctk.CTkFont(size=16),
            text_color="gray"
        )
        self.deepseek_indicator.grid(row=1, column=1, padx=10, pady=2, sticky="e")
        
        # OpenAI Status
        self.openai_label = ctk.CTkLabel(
            self.status_frame,
            text="🔷 OpenAI",
            font=ctk.CTkFont(size=11),
            anchor="w"
        )
        self.openai_label.grid(row=2, column=0, padx=10, pady=2, sticky="w")
        
        self.openai_indicator = ctk.CTkLabel(
            self.status_frame,
            text="●",
            font=ctk.CTkFont(size=16),
            text_color="gray"
        )
        self.openai_indicator.grid(row=2, column=1, padx=10, pady=2, sticky="e")
        
        self.status_text = ctk.CTkLabel(
            self.status_frame,
            text="Checking...",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        self.status_text.grid(row=3, column=0, padx=10, pady=(5, 10), columnspan=2, sticky="w")
        
        # Collection/Standard Selector
        self.collection_frame = ctk.CTkFrame(self.sidebar)
        self.collection_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        
        self.collection_label = ctk.CTkLabel(
            self.collection_frame,
            text="📚 Active Standard",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.collection_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")
        
        self.collection_var = ctk.StringVar(value="engineering_standards")
        self.collection_menu = ctk.CTkOptionMenu(
            self.collection_frame,
            variable=self.collection_var,
            values=["engineering_standards"],
            command=self.on_collection_change,
            font=ctk.CTkFont(size=12)
        )
        self.collection_menu.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")
        
        self.new_collection_button = ctk.CTkButton(
            self.collection_frame,
            text="➕ New Standard",
            command=self.create_new_collection,
            height=30,
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            border_width=1
        )
        self.new_collection_button.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="ew")
        
        # Buttons
        self.index_button = ctk.CTkButton(
            self.sidebar,
            text="📁 Index Documents",
            command=self.open_index_dialog,
            height=40,
            font=ctk.CTkFont(size=13)
        )
        self.index_button.grid(row=4, column=0, padx=20, pady=10)
        
        self.stats_button = ctk.CTkButton(
            self.sidebar,
            text="📊 View Statistics",
            command=self.show_statistics,
            height=40,
            font=ctk.CTkFont(size=13),
            fg_color="transparent",
            border_width=2
        )
        self.stats_button.grid(row=5, column=0, padx=20, pady=10)
        
        self.clear_button = ctk.CTkButton(
            self.sidebar,
            text="🗑️ Clear History",
            command=self.clear_chat,
            height=40,
            font=ctk.CTkFont(size=13),
            fg_color="transparent",
            border_width=2
        )
        self.clear_button.grid(row=6, column=0, padx=20, pady=10)
        
        # Settings
        self.settings_label = ctk.CTkLabel(
            self.sidebar,
            text="Settings",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.settings_label.grid(row=7, column=0, padx=20, pady=(20, 10))
        
        self.show_sources_var = ctk.BooleanVar(value=True)
        self.show_sources_check = ctk.CTkCheckBox(
            self.sidebar,
            text="📚 Show Sources",
            variable=self.show_sources_var,
            font=ctk.CTkFont(size=12)
        )
        self.show_sources_check.grid(row=8, column=0, padx=20, pady=5, sticky="w")
        
        # Tooltip explanation
        sources_info = ctk.CTkLabel(
            self.sidebar,
            text="(Displays source documents\nwith page & section info)",
            font=ctk.CTkFont(size=9),
            text_color="#888888"
        )
        sources_info.grid(row=9, column=0, padx=20, pady=0, sticky="w")
        
        # Version info
        self.version_label = ctk.CTkLabel(
            self.sidebar,
            text="v1.1.0 | DeepSeek AI",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        self.version_label.grid(row=10, column=0, padx=20, pady=(0, 20))
        
        # ========== MAIN CONTENT ==========
        self.main_frame = ctk.CTkFrame(self, corner_radius=0)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)
        
        # Header
        self.header_frame = ctk.CTkFrame(self.main_frame, height=60, corner_radius=0)
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        self.header_frame.grid_columnconfigure(0, weight=1)
        
        self.header_label = ctk.CTkLabel(
            self.header_frame,
            text="💬 Ask Your Questions",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.header_label.grid(row=0, column=0, padx=30, pady=15, sticky="w")
        
        # Chat area
        self.chat_frame = ctk.CTkFrame(self.main_frame)
        self.chat_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 10))
        self.chat_frame.grid_columnconfigure(0, weight=1)
        self.chat_frame.grid_rowconfigure(0, weight=1)
        
        self.chat_display = ctk.CTkTextbox(
            self.chat_frame,
            font=ctk.CTkFont(size=13),
            wrap="word",
            state="disabled"
        )
        self.chat_display.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Input area
        self.input_frame = ctk.CTkFrame(self.main_frame, corner_radius=0)
        self.input_frame.grid(row=2, column=0, sticky="ew", padx=0, pady=0)
        self.input_frame.grid_columnconfigure(0, weight=1)
        
        self.input_entry = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="Type your question here... (e.g., What is the current capacity for 2.5mm² cable?)",
            height=50,
            font=ctk.CTkFont(size=14)
        )
        self.input_entry.grid(row=0, column=0, padx=(20, 10), pady=20, sticky="ew")
        self.input_entry.bind("<Return>", lambda e: self.send_message())
        
        self.send_button = ctk.CTkButton(
            self.input_frame,
            text="Send ➤",
            command=self.send_message,
            height=50,
            width=120,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.send_button.grid(row=0, column=1, padx=(0, 20), pady=20)
        
        # Welcome message
        self.display_welcome_message()
    
    def display_welcome_message(self):
        """Display welcome message in chat"""
        welcome = """
════════════════════════════════════════════════════════════
        Welcome to PyRAG - Engineering Standards AI
════════════════════════════════════════════════════════════

🎯 This AI assistant helps you find information from technical 
   standards like IS10101, ETCI Rules, and more.

💡 Example Questions:
   • What is the current carrying capacity for 2.5mm² copper cable?
   • What are the temperature correction factors for PVC cables?
   • Show me the grounding resistance requirements

📁 Getting Started:
   1. Add your PDF files using "Add PDF Files" button
   2. Click "Index Documents" to process them
   3. Start asking questions!

⚡ System Status: Checking...
        """
        self.append_to_chat(welcome, "system")
    
    def append_to_chat(self, text, sender="user"):
        """Append message to chat display"""
        self.chat_display.configure(state="normal")
        
        if sender == "user":
            prefix = "\n\n❓ YOU:\n"
            self.chat_display.insert("end", prefix, "user_tag")
            self.chat_display.insert("end", text + "\n")
            
        elif sender == "assistant":
            prefix = "\n✅ ASSISTANT:\n"
            self.chat_display.insert("end", prefix, "assistant_tag")
            self.chat_display.insert("end", text + "\n")
            
        elif sender == "system":
            self.chat_display.insert("end", text + "\n", "system_tag")
            
        elif sender == "source":
            self.chat_display.insert("end", text + "\n", "source_tag")
        
        # Configure tags (font not supported in CTkTextbox tags)
        self.chat_display.tag_config("user_tag", foreground="#5DADE2")
        self.chat_display.tag_config("assistant_tag", foreground="#58D68D")
        self.chat_display.tag_config("system_tag", foreground="#BDC3C7")
        self.chat_display.tag_config("source_tag", foreground="#F4D03F")
        
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")
    
    def check_api_health(self):
        """Check API health in background"""
        import threading
        
        # Get settings once
        settings = get_settings()
        
        def check_deepseek():
            try:
                from llama_index.llms.deepseek import DeepSeek
                llm = DeepSeek(
                    model="deepseek-chat",
                    api_key=settings.deepseek_api_key
                )
                response = llm.complete("Hi")
                self.after(0, lambda: self.deepseek_indicator.configure(text_color="#00ff00"))
            except Exception as e:
                logger.warning(f"DeepSeek check failed: {e}")
                self.after(0, lambda: self.deepseek_indicator.configure(text_color="#ff0000"))
        
        def check_openai():
            try:
                from llama_index.embeddings.openai import OpenAIEmbedding
                embed = OpenAIEmbedding(
                    model="text-embedding-3-large",
                    api_key=settings.openai_api_key
                )
                embed.get_text_embedding("test")
                self.after(0, lambda: self.openai_indicator.configure(text_color="#00ff00"))
            except Exception as e:
                logger.warning(f"OpenAI check failed: {e}")
                self.after(0, lambda: self.openai_indicator.configure(text_color="#ff0000"))
        
        threading.Thread(target=check_deepseek, daemon=True).start()
        threading.Thread(target=check_openai, daemon=True).start()
    
    def initialize_system(self):
        """Initialize RAG system"""
        try:
            self.update_status("Initializing...", "gray")
            
            # Check API health
            self.check_api_health()
            
            # Load available collections first
            self.load_available_collections()
            
            # Try to load existing index for current collection
            self.ingestion = DocumentIngestion()
            stats = self.ingestion.get_index_stats()
            
            current_collection = self.collection_var.get()
            
            if stats.get('total_nodes', 0) > 0:
                self.query_engine = QueryEngine()
                self.update_status(f"Ready ({stats['total_nodes']} nodes)", "green")
                self.append_to_chat("\n✅ System initialized successfully!", "system")
                self.append_to_chat(f"📚 Standard: {current_collection}", "system")
                self.append_to_chat(f"📊 Database contains {stats['total_nodes']} indexed chunks", "system")
            else:
                self.update_status("No index found", "orange")
                self.append_to_chat("\n⚠️  No documents indexed yet.", "system")
                self.append_to_chat(f"📚 Standard: {current_collection}", "system")
                self.append_to_chat("Please add PDF files and click 'Index Documents'", "system")
                
        except Exception as e:
            self.update_status("Error", "red")
            self.append_to_chat(f"\n❌ Initialization error: {e}", "system")
            logger.error(f"Initialization error: {e}")
    
    def update_status(self, text, color="gray"):
        """Update status label"""
        self.status_text.configure(text=text, text_color=color)
    
    def send_message(self):
        """Send user message and get response"""
        question = self.input_entry.get().strip()
        
        if not question:
            return
        
        if not self.query_engine:
            messagebox.showwarning(
                "Not Ready",
                "System is not initialized yet.\n\nPlease index documents first."
            )
            return
        
        # Clear input
        self.input_entry.delete(0, "end")
        
        # Display user message
        self.append_to_chat(question, "user")
        
        # Disable send button
        self.send_button.configure(state="disabled", text="Thinking...")
        self.update_status("Processing query...", "orange")
        
        # Process in thread
        thread = threading.Thread(target=self.process_query, args=(question,))
        thread.daemon = True
        thread.start()
    
    def process_query(self, question):
        """Process query in background thread"""
        try:
            result = self.query_engine.query(
                question=question,
                return_sources=self.show_sources_var.get()
            )
            
            # Debug log answer
            answer = result.get('answer', '')
            logger.info(f"Answer received: '{answer}' (length: {len(answer)})")
            
            # Display answer (or fallback if empty)
            if answer and answer.strip():
                self.after(0, self.append_to_chat, answer, "assistant")
            else:
                logger.warning("Empty answer from query engine!")
                fallback_msg = "I found relevant documents but couldn't generate an answer. The information might be in the sources below."
                self.after(0, self.append_to_chat, fallback_msg, "assistant")
            
            # Display sources
            if result.get('sources') and self.show_sources_var.get():
                sources_text = f"\n📚 Sources ({len(result['sources'])} documents):\n"
                for source in result['sources'][:3]:
                    meta = source['metadata']
                    file_name = meta.get('file_name', 'Unknown')
                    page = meta.get('page_label', '?')
                    section_num = meta.get('section_number', '')
                    section_title = meta.get('section_title', '')
                    
                    # Build source line
                    sources_text += f"  • {file_name} (Page {page})"
                    
                    # Add section info if available
                    if section_num and section_title:
                        sources_text += f"\n    └─ Section {section_num}: {section_title}"
                    elif section_num:
                        sources_text += f"\n    └─ Section {section_num}"
                    
                    sources_text += "\n"
                
                self.after(0, self.append_to_chat, sources_text, "source")
            
            # Save to history
            self.chat_history.append({
                'question': question,
                'answer': result['answer'],
                'timestamp': datetime.now().isoformat()
            })
            
            self.after(0, self.update_status, "Ready", "green")
            
        except Exception as e:
            logger.error(f"Query error: {e}", exc_info=True)
            
            # User-friendly error messages
            error_type = type(e).__name__
            error_str = str(e).lower()
            
            if "api" in error_str or "401" in error_str or "403" in error_str:
                user_msg = (
                    "❌ API Authentication Error\n\n"
                    "Your API key might be invalid or expired.\n\n"
                    "🔧 Solutions:\n"
                    "  1. Check your API keys in .env file\n"
                    "  2. Verify DeepSeek API key at platform.deepseek.com\n"
                    "  3. Check OpenAI API key at platform.openai.com\n"
                    "  4. Restart the application after updating keys"
                )
            elif "timeout" in error_str or "timed out" in error_str:
                user_msg = (
                    "⏱️ Request Timeout\n\n"
                    "The AI service took too long to respond.\n\n"
                    "🔧 Solutions:\n"
                    "  1. Check your internet connection\n"
                    "  2. Try again - the service might be busy\n"
                    "  3. Try a shorter or simpler question"
                )
            elif "connection" in error_str or "network" in error_str:
                user_msg = (
                    "🌐 Network Error\n\n"
                    "Cannot connect to AI services.\n\n"
                    "🔧 Solutions:\n"
                    "  1. Check your internet connection\n"
                    "  2. Check if firewall is blocking the app\n"
                    "  3. Try again in a few moments"
                )
            elif "rate limit" in error_str or "429" in error_str:
                user_msg = (
                    "⚠️ Rate Limit Exceeded\n\n"
                    "Too many requests to the AI service.\n\n"
                    "🔧 Solutions:\n"
                    "  1. Wait a few minutes before trying again\n"
                    "  2. Check your API usage limits\n"
                    "  3. Consider upgrading your API plan"
                )
            elif "no documents indexed" in error_str or "index" in error_str:
                user_msg = (
                    "📁 No Documents Found\n\n"
                    "The system cannot find any indexed documents.\n\n"
                    "🔧 Solutions:\n"
                    "  1. Click '➕ New Standard' to add documents\n"
                    "  2. Select PDF files to index\n"
                    "  3. Wait for indexing to complete"
                )
            else:
                user_msg = (
                    f"❌ Unexpected Error\n\n"
                    f"Error type: {error_type}\n"
                    f"Message: {str(e)[:200]}\n\n"
                    "🔧 Solutions:\n"
                    "  1. Try rephrasing your question\n"
                    "  2. Check the terminal for detailed logs\n"
                    "  3. Restart the application if problem persists"
                )
            
            self.after(0, self.append_to_chat, user_msg, "system")
            self.after(0, self.update_status, "Error", "red")
        
        finally:
            # Always re-enable send button
            def reset_button():
                self.send_button.configure(state="normal", text="Send ➤")
            self.after(0, reset_button)
    
    def open_index_dialog(self):
        """Open indexing dialog"""
        if self.is_indexing:
            messagebox.showinfo("In Progress", "Indexing is already in progress.")
            return
        
        dialog = IndexDialog(self)
        self.wait_window(dialog)
        
        # Refresh after indexing
        if dialog.success:
            self.initialize_system()
    
    def show_statistics(self):
        """Show enhanced statistics dialog"""
        if not self.ingestion:
            messagebox.showinfo("Not Ready", "System not initialized yet.")
            return
        
        try:
            stats = self.ingestion.get_index_stats()
            pdf_files = validate_pdf_files()
            settings = get_settings()
            
            # Calculate total size of PDF files
            total_size = sum(pdf.stat().st_size for pdf in pdf_files) / (1024 * 1024)  # MB
            
            # Get collection info
            collection_name = stats.get('collection_name', 'N/A')
            total_nodes = stats.get('total_nodes', 0)
            
            stats_text = f"""
╔════════════════════════════════════════════╗
║        SYSTEM STATISTICS                  ║
╚════════════════════════════════════════════╝

📚 VECTOR DATABASE
   • Active Collection: {collection_name}
   • Total Chunks: {total_nodes:,} nodes
   • Storage: {stats.get('db_path', 'N/A')}

📄 DOCUMENT LIBRARY
   • PDF Files: {len(pdf_files)}
   • Total Size: {total_size:.2f} MB
"""
            
            if pdf_files:
                stats_text += "\n   Files in collection:\n"
                for pdf in pdf_files[:5]:
                    size_mb = pdf.stat().st_size / (1024 * 1024)
                    stats_text += f"   • {pdf.name} ({size_mb:.1f} MB)\n"
                if len(pdf_files) > 5:
                    stats_text += f"   ... and {len(pdf_files) - 5} more files\n"
            
            stats_text += f"""

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
            self.chat_display.configure(state="normal")
            self.chat_display.delete("1.0", "end")
            self.chat_display.configure(state="disabled")
            self.chat_history = []
            self.display_welcome_message()
            self.append_to_chat("\n🗑️  Chat history cleared", "system")
    
    def on_collection_change(self, choice):
        """Handle collection/standard change"""
        try:
            self.append_to_chat(f"\n🔄 Switching to: {choice}", "system")
            
            # Update settings with new collection
            import os
            os.environ['COLLECTION_NAME'] = choice
            
            # Reinitialize system with new collection
            self.initialize_system()
            
            self.append_to_chat(f"✅ Now using standard: {choice}", "system")
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not switch collection:\n{e}")
            logger.error(f"Collection switch error: {e}")
    
    def create_new_collection(self):
        """Create a new collection/standard with PDF upload workflow"""
        # Step 1: Get standard name
        dialog = ctk.CTkInputDialog(
            text="Enter new standard name (e.g., IS10101, IS3218, LDA):",
            title="Create New Standard"
        )
        name = dialog.get_input()
        
        if not name:
            return
        
        # Sanitize name
        name = name.strip().replace(" ", "_")
        
        if not name:
            messagebox.showwarning("Invalid Name", "Standard name cannot be empty")
            return
        
        # Check if already exists
        current_values = list(self.collection_menu.cget("values"))
        if name in current_values:
            messagebox.showinfo("Already Exists", f"Standard '{name}' already exists")
            return
        
        # Step 2: Select PDF files
        files = filedialog.askopenfilenames(
            title=f"Select PDF Files for {name}",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        
        if not files:
            self.append_to_chat(f"\n⚠️ No files selected for {name}", "system")
            return
        
        # Step 3: Copy files to data folder
        settings = get_settings()
        data_dir = Path(settings.data_dir)
        data_dir.mkdir(exist_ok=True)
        
        copied = 0
        copied_files = []
        for file in files:
            try:
                import shutil
                dest = data_dir / Path(file).name
                shutil.copy2(file, dest)
                copied += 1
                copied_files.append(Path(file).name)
            except Exception as e:
                logger.error(f"Error copying {file}: {e}")
        
        if copied == 0:
            messagebox.showerror("Error", "Failed to copy PDF files")
            return
        
        # Step 4: Add to dropdown
        current_values.append(name)
        self.collection_menu.configure(values=current_values)
        self.collection_var.set(name)
        
        self.append_to_chat(f"\n✅ New standard created: {name}", "system")
        self.append_to_chat(f"📄 Added {copied} PDF file(s):", "system")
        for fname in copied_files:
            self.append_to_chat(f"   • {fname}", "system")
        
        # Step 5: Ask to index now
        result = messagebox.askyesno(
            "Start Indexing?",
            f"Standard '{name}' created with {copied} file(s).\n\n"
            f"Would you like to index these documents now?\n\n"
            f"(This will take a few minutes)",
            icon='question'
        )
        
        if result:
            # Switch to new collection first
            import os
            os.environ['COLLECTION_NAME'] = name
            
            # Open indexing dialog
            self.open_index_dialog()
        else:
            self.append_to_chat(f"\n💡 Tip: Click 'Index Documents' when ready", "system")
    
    def load_available_collections(self):
        """Load available collections from ChromaDB"""
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings
            
            settings = get_settings()
            client = chromadb.PersistentClient(
                path=settings.chroma_db_path,
                settings=ChromaSettings(anonymized_telemetry=False)
            )
            
            collections = client.list_collections()
            names = [c.name for c in collections]
            
            if names:
                # Get current selection
                current = self.collection_var.get()
                
                # Update dropdown values
                self.collection_menu.configure(values=names)
                
                # Keep current selection if it exists, otherwise use first or env variable
                import os
                env_collection = os.getenv('COLLECTION_NAME', '')
                
                if current and current in names:
                    # Keep current selection
                    pass
                elif env_collection and env_collection in names:
                    # Use environment variable
                    self.collection_var.set(env_collection)
                elif names:
                    # Fallback to first
                    self.collection_var.set(names[0])
            
        except Exception as e:
            logger.error(f"Could not load collections: {e}")


class IndexDialog(ctk.CTkToplevel):
    """Dialog for indexing documents"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.parent = parent
        self.success = False
        
        # Window config
        self.title("Index Documents")
        self.geometry("600x500")
        self.resizable(False, False)
        
        # Center on parent
        self.transient(parent)
        self.grab_set()
        
        # Variables
        self.force_reindex = ctk.BooleanVar(value=False)
        self.collection_name = None
        
        self.create_widgets()
    
    def create_widgets(self):
        """Create dialog widgets"""
        
        # Title
        title = ctk.CTkLabel(
            self,
            text="📁 Index Documents",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(pady=(30, 10))
        
        # Description
        desc = ctk.CTkLabel(
            self,
            text="This will process PDF files and create a searchable index.\n"
                 "The process may take several minutes depending on file size.",
            font=ctk.CTkFont(size=12),
            justify="center"
        )
        desc.pack(pady=10)
        
        # Collection/Standard info display
        collection_frame = ctk.CTkFrame(self)
        collection_frame.pack(pady=10, padx=40, fill="x")
        
        # Get current collection from environment or parent
        import os
        current_collection = os.getenv('COLLECTION_NAME', 'engineering_standards')
        self.collection_name = current_collection
        
        info_text = ctk.CTkLabel(
            collection_frame,
            text=f"📚 Indexing for: {current_collection}",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#58D68D"
        )
        info_text.pack(pady=15)
        
        # Options
        options_frame = ctk.CTkFrame(self)
        options_frame.pack(pady=20, padx=40, fill="x")
        
        force_check = ctk.CTkCheckBox(
            options_frame,
            text="Force rebuild (delete existing index)",
            variable=self.force_reindex,
            font=ctk.CTkFont(size=13)
        )
        force_check.pack(pady=10, padx=20, anchor="w")
        
        # Info
        info_label = ctk.CTkLabel(
            options_frame,
            text="⚠️  Uses OpenAI embeddings (best quality, ~$0.01/100 pages) + DeepSeek LLM",
            font=ctk.CTkFont(size=11),
            text_color="orange"
        )
        info_label.pack(pady=5, padx=20)
        
        # Progress
        self.progress_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=12)
        )
        self.progress_label.pack(pady=10)
        
        self.progress_bar = ctk.CTkProgressBar(self, width=400)
        self.progress_bar.pack(pady=10)
        self.progress_bar.set(0)
        
        # Buttons
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=20)
        
        self.start_button = ctk.CTkButton(
            button_frame,
            text="Start Indexing",
            command=self.start_indexing,
            width=150,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.start_button.pack(side="left", padx=10)
        
        self.cancel_button = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.destroy,
            width=150,
            height=40,
            font=ctk.CTkFont(size=14),
            fg_color="gray",
            hover_color="darkgray"
        )
        self.cancel_button.pack(side="left", padx=10)
    
    def start_indexing(self):
        """Start indexing process"""
        self.start_button.configure(state="disabled")
        self.cancel_button.configure(state="disabled")
        self.parent.is_indexing = True
        
        # Run in thread
        thread = threading.Thread(target=self.run_indexing)
        thread.daemon = True
        thread.start()
    
    def run_indexing(self):
        """Run indexing in background"""
        try:
            self.update_progress("Initializing...", 0.1)
            
            # Use selected collection
            ingestion = DocumentIngestion(collection_name=self.collection_name)
            
            self.update_progress("Reading PDF files...", 0.3)
            
            index = ingestion.ingest_documents(
                force_reindex=self.force_reindex.get()
            )
            
            self.update_progress("Finalizing...", 0.9)
            
            if index:
                stats = ingestion.get_index_stats()
                self.update_progress(f"✅ Complete! ({stats['total_nodes']} nodes)", 1.0)
                self.success = True
                
                # Update parent's collection list and switch to new collection
                self.after(0, self.parent.load_available_collections)
                self.after(100, lambda: self.parent.collection_var.set(self.collection_name))
                
                self.after(1000, messagebox.showinfo, "Success", 
                          f"Indexing completed!\n\nStandard: {self.collection_name}\nTotal nodes: {stats['total_nodes']}")
                self.after(1500, self.destroy)
            else:
                self.update_progress("❌ Failed", 0)
                self.after(100, messagebox.showerror, "Error", "Indexing failed. Check logs.")
                
        except Exception as e:
            self.update_progress("❌ Error", 0)
            logger.error(f"Indexing error: {e}", exc_info=True)
            
            # User-friendly error messages for indexing
            error_str = str(e).lower()
            error_type = type(e).__name__
            
            if "pdf" in error_str and ("corrupt" in error_str or "invalid" in error_str or "damaged" in error_str):
                error_msg = (
                    "📄 PDF File Error\n\n"
                    "One or more PDF files cannot be read.\n\n"
                    "🔧 Solutions:\n"
                    "  1. Check if PDF files are corrupted\n"
                    "  2. Try opening PDFs in a PDF reader\n"
                    "  3. Re-download or obtain new copies\n"
                    "  4. Remove problematic PDFs and try again"
                )
            elif "permission" in error_str or "access" in error_str:
                error_msg = (
                    "🔒 Permission Error\n\n"
                    "Cannot access PDF files or database.\n\n"
                    "🔧 Solutions:\n"
                    "  1. Close any programs using the files\n"
                    "  2. Check file permissions\n"
                    "  3. Run application as administrator\n"
                    "  4. Move files to a different folder"
                )
            elif "memory" in error_str or "out of memory" in error_str:
                error_msg = (
                    "💾 Memory Error\n\n"
                    "Not enough memory to process documents.\n\n"
                    "🔧 Solutions:\n"
                    "  1. Close other applications\n"
                    "  2. Process fewer documents at once\n"
                    "  3. Restart your computer\n"
                    "  4. Add more RAM if this persists"
                )
            elif "api" in error_str or "401" in error_str or "403" in error_str:
                error_msg = (
                    "🔑 API Error\n\n"
                    "Cannot authenticate with AI services.\n\n"
                    "🔧 Solutions:\n"
                    "  1. Check your API keys in .env file\n"
                    "  2. Verify OpenAI API key (for embeddings)\n"
                    "  3. Check your API usage/credits\n"
                    "  4. Restart after updating keys"
                )
            elif "timeout" in error_str or "timed out" in error_str:
                error_msg = (
                    "⏱️ Timeout Error\n\n"
                    "Processing took too long.\n\n"
                    "🔧 Solutions:\n"
                    "  1. Check your internet connection\n"
                    "  2. Try with fewer/smaller PDF files\n"
                    "  3. Restart and try again"
                )
            elif "no such file" in error_str or "not found" in error_str:
                error_msg = (
                    "📁 File Not Found\n\n"
                    "Cannot find PDF files.\n\n"
                    "🔧 Solutions:\n"
                    "  1. Ensure PDF files are in data/ folder\n"
                    "  2. Check if files were moved/deleted\n"
                    "  3. Re-add PDF files using '➕ New Standard'"
                )
            else:
                error_msg = (
                    f"❌ Indexing Error\n\n"
                    f"Error type: {error_type}\n"
                    f"Message: {str(e)[:200]}\n\n"
                    "🔧 Solutions:\n"
                    "  1. Check terminal logs for details\n"
                    "  2. Try with different PDF files\n"
                    "  3. Restart the application\n"
                    "  4. Contact support if problem persists"
                )
            
            self.after(100, messagebox.showerror, "Indexing Error", error_msg)
        
        finally:
            self.parent.is_indexing = False
            self.after(0, self.start_button.configure, {"state": "normal"})
            self.after(0, self.cancel_button.configure, {"state": "normal"})
    
    def update_progress(self, text, value):
        """Update progress bar and label"""
        self.after(0, self.progress_label.configure, {"text": text})
        self.after(0, self.progress_bar.set, value)


def main():
    """Launch application"""
    try:
        app = PyRAGApp()
        app.mainloop()
    except Exception as e:
        logger.error(f"Application error: {e}")
        messagebox.showerror("Error", f"Application error:\n{e}")


if __name__ == "__main__":
    main()
