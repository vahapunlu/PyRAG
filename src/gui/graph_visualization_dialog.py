"""
Graph Visualization Dialog for PyRAG GUI

Display knowledge graph visualization from Neo4j.
"""

import customtkinter as ctk
from tkinter import messagebox
from PIL import Image, ImageTk
from pathlib import Path
from typing import Optional
import io
import subprocess
import sys

try:
    import webview
    WEBVIEW_AVAILABLE = True
except ImportError:
    WEBVIEW_AVAILABLE = False


class GraphVisualizationDialog(ctk.CTkToplevel):
    """Knowledge graph visualization viewer"""
    
    def __init__(self, parent, query_engine):
        super().__init__(parent)
        
        self.query_engine = query_engine
        self.graph_visualizer = query_engine.graph_visualizer
        self.current_image = None
        self.current_mode = "full"  # "full" or "context"
        
        # Window setup
        self.title("🎨 Knowledge Graph Visualization")
        
        # Get screen dimensions
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # Make window nearly full screen (with small margins)
        width = int(screen_width * 0.95)
        height = int(screen_height * 0.9)
        x = int(screen_width * 0.025)
        y = int(screen_height * 0.05)
        
        self.geometry(f"{width}x{height}+{x}+{y}")
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        self._setup_ui()
        # Open interactive view directly instead of static image
        self.after(100, self._open_interactive_on_load)
    
    def _open_interactive_on_load(self):
        """Open interactive view immediately on load"""
        self._open_interactive()
        # Close the dialog after opening interactive view
        self.after(500, self.destroy)
    
    def _setup_ui(self):
        """Setup UI components"""
        
        # Configure grid
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        header_frame.grid_columnconfigure(1, weight=1)
        
        header = ctk.CTkLabel(
            header_frame,
            text="🎨 Knowledge Graph",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        header.grid(row=0, column=0, sticky="w")
        
        # Statistics label
        self.stats_label = ctk.CTkLabel(
            header_frame,
            text="Loading...",
            font=ctk.CTkFont(size=12)
        )
        self.stats_label.grid(row=0, column=1, padx=20, sticky="e")
        
        # Control frame
        control_frame = ctk.CTkFrame(self, fg_color="transparent")
        control_frame.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")
        
        # Mode selection
        self.mode_var = ctk.StringVar(value="full")
        
        full_radio = ctk.CTkRadioButton(
            control_frame,
            text="📊 Full Graph",
            variable=self.mode_var,
            value="full",
            command=self._on_mode_change
        )
        full_radio.pack(side="left", padx=5)
        
        context_radio = ctk.CTkRadioButton(
            control_frame,
            text="🔍 Last Query Context",
            variable=self.mode_var,
            value="context",
            command=self._on_mode_change
        )
        context_radio.pack(side="left", padx=5)
        
        # Refresh button
        refresh_btn = ctk.CTkButton(
            control_frame,
            text="🔄 Refresh",
            command=self._load_graph,
            width=100
        )
        refresh_btn.pack(side="left", padx=20)
        
        # Interactive HTML button
        html_btn = ctk.CTkButton(
            control_frame,
            text="🌐 Interactive View",
            command=self._open_interactive,
            width=140,
            fg_color="#10B981"
        )
        html_btn.pack(side="left", padx=5)
        
        # Save button
        save_btn = ctk.CTkButton(
            control_frame,
            text="💾 Save Image",
            command=self._save_image,
            width=100
        )
        save_btn.pack(side="left", padx=5)
        
        # Image frame with scrollbar
        image_container = ctk.CTkFrame(self)
        image_container.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="nsew")
        image_container.grid_rowconfigure(0, weight=1)
        image_container.grid_columnconfigure(0, weight=1)
        
        # Scrollable frame for image
        self.image_frame = ctk.CTkScrollableFrame(image_container)
        self.image_frame.grid(row=0, column=0, sticky="nsew")
        self.image_frame.grid_columnconfigure(0, weight=1)
        
        # Image label
        self.image_label = ctk.CTkLabel(
            self.image_frame,
            text="Loading graph visualization...",
            font=ctk.CTkFont(size=14)
        )
        self.image_label.grid(row=0, column=0, padx=20, pady=20)
        
        # Info frame
        info_frame = ctk.CTkFrame(self)
        info_frame.grid(row=3, column=0, padx=20, pady=(0, 10), sticky="ew")
        info_frame.grid_columnconfigure(0, weight=1)
        
        self.info_label = ctk.CTkLabel(
            info_frame,
            text="",
            font=ctk.CTkFont(size=12),
            justify="left"
        )
        self.info_label.pack(padx=10, pady=10, anchor="w")
        
        # Close button
        close_btn = ctk.CTkButton(
            self,
            text="Close",
            command=self.destroy,
            width=100
        )
        close_btn.grid(row=4, column=0, padx=20, pady=(0, 20))
    
    def _load_graph(self):
        """Load and display graph visualization"""
        try:
            self.image_label.configure(text="⏳ Generating graph visualization...")
            self.update()
            
            # Get graph statistics
            stats = self.graph_visualizer.get_graph_statistics()
            
            # Update statistics label
            total_edges = stats.get('total_relationships', stats.get('total_edges', 0))
            stats_text = f"Nodes: {stats['total_nodes']} | Edges: {total_edges}"
            self.stats_label.configure(text=stats_text)
            
            # Generate visualization based on mode
            
            if self.mode_var.get() == "full":
                # Full graph - use larger figure size for better readability
                temp_path = self.graph_visualizer.visualize_graph(
                    limit=100,
                    show_labels=True,
                    figsize=(32, 24)  # Much larger for better visibility
                )
                
                total_edges = stats.get('total_relationships', stats.get('total_edges', 0))
                node_types = list(stats.get('nodes', {}).keys()) if 'nodes' in stats else stats.get('node_types', [])
                rel_types = list(stats.get('relationships', {}).keys()) if 'relationships' in stats else stats.get('relationship_types', [])
                
                info_text = (
                    f"📊 Full Knowledge Graph\n"
                    f"• Total Nodes: {stats['total_nodes']}\n"
                    f"• Total Edges: {total_edges}\n"
                    f"• Node Types: {', '.join(node_types)}\n"
                    f"• Relationship Types: {', '.join(rel_types)}"
                )
                
            else:
                # Last query context
                history = self.query_engine.query_history
                recent = history.get_recent(limit=1) if history else []
                
                if not recent:
                    messagebox.showinfo(
                        "No Context",
                        "No recent queries found. Please run a query first."
                    )
                    self.mode_var.set("full")
                    self._load_graph()
                    return
                
                last_query = recent[0]
                
                # Get sources from last query if available
                sources = []  # TODO: Get actual sources from query history
                temp_path = self.graph_visualizer.visualize_query_context(
                    query=last_query['query'],
                    sources=sources
                )
                
                info_text = (
                    f"🔍 Query Context: {last_query['query'][:60]}...\n"
                    f"• Showing relationships within 2 hops\n"
                    f"• Red nodes: Direct matches\n"
                    f"• Yellow/Green nodes: Related concepts"
                )
            
            # Load and display image
            if temp_path and Path(temp_path).exists():
                image = Image.open(temp_path)
                
                # Resize if too large
                max_width = 1100
                max_height = 600
                
                if image.width > max_width or image.height > max_height:
                    ratio = min(max_width / image.width, max_height / image.height)
                    new_width = int(image.width * ratio)
                    new_height = int(image.height * ratio)
                    image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Convert to PhotoImage
                self.current_image = ImageTk.PhotoImage(image)
                
                # Update label
                self.image_label.configure(
                    image=self.current_image,
                    text=""
                )
                
                # Update info
                self.info_label.configure(text=info_text)
                
                # Clean up temp file
                if temp_path:
                    Path(temp_path).unlink(missing_ok=True)
                
            else:
                self.image_label.configure(text="❌ Failed to generate visualization")
                
        except Exception as e:
            self.image_label.configure(text="❌ Error loading graph")
            messagebox.showerror(
                "Error",
                f"Failed to load graph visualization:\n{str(e)}\n\n"
                f"Make sure Neo4j is running and properly configured."
            )
    
    def _on_mode_change(self):
        """Handle mode change"""
        self._load_graph()
    
    def _open_interactive(self):
        """Open interactive HTML graph visualization in embedded viewer"""
        try:
            self.info_label.configure(text="⏳ Generating interactive visualization...")
            self.update()
            
            # Generate interactive HTML (don't auto-open in browser)
            html_path = self.graph_visualizer.visualize_graph_interactive(
                limit=200,  # More nodes for interactive view
                auto_open=False  # We'll open it embedded
            )
            
            if html_path:
                # Check if webview is available for embedded viewing
                if WEBVIEW_AVAILABLE:
                    self.info_label.configure(
                        text=f"✅ Opening interactive graph in embedded viewer...\n"
                             f"💡 Tip: Zoom with mouse wheel, drag nodes, hover for details"
                    )
                    self.update()
                    
                    # Open in embedded webview window
                    self._open_in_webview(html_path)
                else:
                    # Fallback to browser
                    import webbrowser
                    webbrowser.open(f"file:///{Path(html_path).absolute()}")
                    self.info_label.configure(
                        text=f"✅ Interactive graph opened in browser\n"
                             f"💡 Tip: Zoom with mouse wheel, drag nodes, hover for details"
                    )
                    messagebox.showinfo(
                        "Interactive View",
                        "Interactive graph opened in browser!\n\n"
                        "(Install 'pywebview' for embedded viewing:\n"
                        "pip install pywebview)"
                    )
            else:
                self.info_label.configure(text="❌ Failed to generate interactive view")
                messagebox.showerror(
                    "Error",
                    "Failed to generate interactive visualization.\n"
                    "Make sure 'pyvis' is installed:\n"
                    "pip install pyvis"
                )
                
        except Exception as e:
            self.info_label.configure(text="❌ Error generating interactive view")
            messagebox.showerror(
                "Error",
                f"Failed to generate interactive visualization:\n{str(e)}"
            )
    
    def _open_in_webview(self, html_path: str):
        """Open HTML file in embedded webview window (separate process)"""
        try:
            # Get screen dimensions for sizing
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()
            width = int(screen_width * 0.9)
            height = int(screen_height * 0.85)
            
            # Create a simple launcher script for webview
            launcher_code = f"""
import webview
from pathlib import Path

webview.create_window(
    title='🎨 Interactive Knowledge Graph',
    url=r'{Path(html_path).absolute()}',
    width={width},
    height={height},
    resizable=True,
    fullscreen=False,
    min_size=(800, 600)
)
webview.start(debug=False)
"""
            
            # Run webview in separate process (non-blocking)
            subprocess.Popen(
                [sys.executable, '-c', launcher_code],
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            self.info_label.configure(
                text=f"✅ Interactive graph opened in separate window\n"
                     f"💡 Tip: Zoom with mouse wheel, drag nodes, hover for details"
            )
            
        except Exception as e:
            messagebox.showerror(
                "Webview Error",
                f"Failed to open embedded viewer:\n{str(e)}\n\n"
                f"Falling back to browser..."
            )
            # Fallback to browser
            import webbrowser
            webbrowser.open(f"file:///{Path(html_path).absolute()}")
    
    def _save_image(self):
        """Save current graph image"""
        if not self.current_image:
            messagebox.showinfo("No Image", "No graph visualization to save.")
            return
        
        try:
            from tkinter import filedialog
            
            # Ask for save location
            filename = filedialog.asksaveasfilename(
                title="Save Graph Image",
                defaultextension=".png",
                filetypes=[
                    ("PNG Image", "*.png"),
                    ("JPEG Image", "*.jpg"),
                    ("All Files", "*.*")
                ]
            )
            
            if filename:
                # Regenerate at full resolution
                temp_path = Path("temp_graph_full.png")
                
                if self.mode_var.get() == "full":
                    self.graph_visualizer.visualize_graph(
                        output_path=str(temp_path),
                        layout="spring"
                    )
                else:
                    history = self.query_engine.query_history
                    recent = history.get_recent(limit=1)
                    if recent:
                        self.graph_visualizer.visualize_query_context(
                            query=recent[0]['query'],
                            output_path=str(temp_path),
                            max_depth=2
                        )
                
                # Copy to destination
                if temp_path.exists():
                    import shutil
                    shutil.copy(temp_path, filename)
                    temp_path.unlink()
                    
                    messagebox.showinfo(
                        "Success",
                        f"Graph image saved to:\n{filename}"
                    )
                    
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to save image:\n{str(e)}"
            )
