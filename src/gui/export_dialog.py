"""
Export Dialog for PyRAG GUI

Export query results to multiple formats (Markdown, PDF, Word).
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict


class ExportDialog(ctk.CTkToplevel):
    """Export results to multiple formats"""
    
    def __init__(self, parent, query_engine, query_data: Optional[Dict] = None):
        super().__init__(parent)
        
        self.query_engine = query_engine
        self.query_data = query_data
        self.export_manager = query_engine.export_manager
        
        # Window setup
        self.title("📤 Export Results")
        self.geometry("600x500")
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.winfo_screenheight() // 2) - (500 // 2)
        self.geometry(f"600x500+{x}+{y}")
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup UI components"""
        
        # Configure grid
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Header
        header = ctk.CTkLabel(
            self,
            text="📤 Export Query Results",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        header.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        # Info label
        if self.query_data:
            timestamp = datetime.fromisoformat(self.query_data['timestamp']).strftime("%Y-%m-%d %H:%M")
            query_preview = self.query_data['query'][:60] + "..." if len(self.query_data['query']) > 60 else self.query_data['query']
            info_text = f"Query: {query_preview}\nTime: {timestamp}"
        else:
            info_text = "Export last query result"
        
        info_label = ctk.CTkLabel(
            self,
            text=info_text,
            font=ctk.CTkFont(size=12),
            justify="left"
        )
        info_label.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="w")
        
        # Main frame
        main_frame = ctk.CTkFrame(self)
        main_frame.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="nsew")
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Format selection
        format_label = ctk.CTkLabel(
            main_frame,
            text="Select Export Formats:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        format_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        # Checkboxes for formats
        self.markdown_var = ctk.BooleanVar(value=True)
        markdown_check = ctk.CTkCheckBox(
            main_frame,
            text="📝 Markdown (.md) - Always included",
            variable=self.markdown_var,
            state="disabled"  # Always enabled
        )
        markdown_check.grid(row=1, column=0, padx=40, pady=5, sticky="w")
        
        self.pdf_var = ctk.BooleanVar(value=True)
        pdf_check = ctk.CTkCheckBox(
            main_frame,
            text="📄 PDF (.pdf) - Portable Document Format",
            variable=self.pdf_var
        )
        pdf_check.grid(row=2, column=0, padx=40, pady=5, sticky="w")
        
        self.word_var = ctk.BooleanVar(value=True)
        word_check = ctk.CTkCheckBox(
            main_frame,
            text="📃 Word (.docx) - Microsoft Word Document",
            variable=self.word_var
        )
        word_check.grid(row=3, column=0, padx=40, pady=5, sticky="w")
        
        # Include options
        options_label = ctk.CTkLabel(
            main_frame,
            text="Include:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        options_label.grid(row=4, column=0, padx=20, pady=(20, 10), sticky="w")
        
        self.include_sources_var = ctk.BooleanVar(value=True)
        sources_check = ctk.CTkCheckBox(
            main_frame,
            text="📚 Source references",
            variable=self.include_sources_var
        )
        sources_check.grid(row=5, column=0, padx=40, pady=5, sticky="w")
        
        self.include_metadata_var = ctk.BooleanVar(value=True)
        metadata_check = ctk.CTkCheckBox(
            main_frame,
            text="ℹ️ Metadata (timestamp, duration)",
            variable=self.include_metadata_var
        )
        metadata_check.grid(row=6, column=0, padx=40, pady=5, sticky="w")
        
        # Output directory
        dir_label = ctk.CTkLabel(
            main_frame,
            text="Output Directory:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        dir_label.grid(row=7, column=0, padx=20, pady=(20, 10), sticky="w")
        
        dir_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        dir_frame.grid(row=8, column=0, padx=20, pady=(0, 20), sticky="ew")
        dir_frame.grid_columnconfigure(0, weight=1)
        
        self.dir_entry = ctk.CTkEntry(
            dir_frame,
            placeholder_text="Select output directory..."
        )
        self.dir_entry.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        
        # Set default directory to exports/
        default_dir = Path("exports")
        default_dir.mkdir(exist_ok=True)
        self.dir_entry.insert(0, str(default_dir.absolute()))
        
        browse_btn = ctk.CTkButton(
            dir_frame,
            text="Browse",
            command=self._browse_directory,
            width=100
        )
        browse_btn.grid(row=0, column=1)
        
        # Button frame
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=3, column=0, padx=20, pady=(0, 20), sticky="ew")
        
        self.export_btn = ctk.CTkButton(
            button_frame,
            text="Export",
            command=self._export,
            width=120,
            height=40
        )
        self.export_btn.pack(side="left", padx=5)
        
        self.export_all_btn = ctk.CTkButton(
            button_frame,
            text="Export All Formats",
            command=self._export_all,
            width=150,
            height=40
        )
        self.export_all_btn.pack(side="left", padx=5)
        
        self.cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.destroy,
            width=100,
            height=40,
            fg_color="gray"
        )
        self.cancel_btn.pack(side="right", padx=5)
    
    def _browse_directory(self):
        """Browse for output directory"""
        directory = filedialog.askdirectory(
            title="Select Output Directory",
            initialdir=self.dir_entry.get()
        )
        
        if directory:
            self.dir_entry.delete(0, 'end')
            self.dir_entry.insert(0, directory)
    
    def _get_query_data(self) -> Optional[Dict]:
        """Get query data to export"""
        if self.query_data:
            return self.query_data
        
        # Get last query from history
        try:
            history = self.query_engine.query_history
            recent = history.get_recent_queries(limit=1)
            
            if not recent:
                messagebox.showerror("Error", "No query results to export.")
                return None
            
            return recent[0]
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to get query data:\n{str(e)}")
            return None
    
    def _export(self):
        """Export to selected formats"""
        query_data = self._get_query_data()
        if not query_data:
            return
        
        output_dir = Path(self.dir_entry.get())
        if not output_dir.exists():
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create output directory:\n{str(e)}")
                return
        
        # Generate filename base
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        query_preview = query_data['query'][:30].replace(" ", "_").replace("/", "_")
        filename_base = f"query_{timestamp}_{query_preview}"
        
        exported_files = []
        errors = []
        
        try:
            # Prepare result data
            result = {
                'response': query_data.get('response', ''),
                'sources': query_data.get('sources', []) if self.include_sources_var.get() else [],
                'metadata': {
                    'query': query_data['query'],
                    'timestamp': query_data['timestamp'],
                    'duration': query_data.get('duration', 0)
                } if self.include_metadata_var.get() else {}
            }
            
            # Export Markdown (always)
            try:
                md_path = self.export_manager.export_to_markdown(
                    result,
                    output_dir / f"{filename_base}.md"
                )
                exported_files.append(str(md_path))
            except Exception as e:
                errors.append(f"Markdown: {str(e)}")
            
            # Export PDF
            if self.pdf_var.get():
                try:
                    pdf_path = self.export_manager.export_to_pdf(
                        result,
                        output_dir / f"{filename_base}.pdf"
                    )
                    exported_files.append(str(pdf_path))
                except Exception as e:
                    errors.append(f"PDF: {str(e)}")
            
            # Export Word
            if self.word_var.get():
                try:
                    word_path = self.export_manager.export_to_word(
                        result,
                        output_dir / f"{filename_base}.docx"
                    )
                    exported_files.append(str(word_path))
                except Exception as e:
                    errors.append(f"Word: {str(e)}")
            
            # Show results
            if exported_files:
                success_msg = "✅ Export Successful!\n\n"
                success_msg += f"Exported {len(exported_files)} file(s):\n"
                for file in exported_files:
                    success_msg += f"\n• {Path(file).name}"
                
                if errors:
                    success_msg += "\n\n⚠️ Some exports failed:\n"
                    for error in errors:
                        success_msg += f"\n• {error}"
                
                messagebox.showinfo("Export Complete", success_msg)
                self.destroy()
            else:
                messagebox.showerror("Export Failed", "All exports failed:\n" + "\n".join(errors))
                
        except Exception as e:
            messagebox.showerror("Error", f"Export failed:\n{str(e)}")
    
    def _export_all(self):
        """Export to all formats"""
        # Enable all checkboxes
        self.pdf_var.set(True)
        self.word_var.set(True)
        
        # Export
        self._export()
