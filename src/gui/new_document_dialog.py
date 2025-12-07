"""
New Document Dialog

Dialog for adding and indexing new documents into the RAG system.
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
from pathlib import Path
import shutil
import pymupdf

from loguru import logger

from ..utils import get_settings, save_document_categories, load_app_settings
from ..ingestion import DocumentIngestion
from .constants import *


class NewDocumentDialog(ctk.CTkToplevel):
    """Dialog for adding and indexing new documents"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.parent = parent
        self.success = False
        self.selected_items = []
        
        # Window config
        self.title("Add New Documents")
        self.resizable(True, True)
        
        # Center and size
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        
        win_w = min(WINDOW_SIZES['large_dialog_width'], int(screen_w * 0.85))
        win_h = min(WINDOW_SIZES['large_dialog_height'], int(screen_h * 0.8))
        pos_x = (screen_w - win_w) // 2
        pos_y = max(20, (screen_h - win_h) // 2)
        self.geometry(f"{win_w}x{win_h}+{pos_x}+{pos_y}")
        
        self.transient(parent)
        self.grab_set()
        
        self.create_widgets()
    
    def create_widgets(self):
        """Create dialog UI"""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header
        header = ctk.CTkFrame(self, height=70, corner_radius=0, fg_color=COLORS['primary'])
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            header,
            text="Add New Documents",
            font=ctk.CTkFont(size=FONT_SIZES['subtitle'], weight="bold"),
            text_color="white"
        ).grid(row=0, column=0, padx=20, pady=(15, 2), sticky="w")
        
        ctk.CTkLabel(
            header,
            text="Import documents and organize them into your searchable collection.",
            font=ctk.CTkFont(size=FONT_SIZES['small']),
            text_color="#e0e0e0"
        ).grid(row=1, column=0, padx=20, pady=(0, 15), sticky="w")
        
        # Content
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(1, weight=1)
        
        # Toolbar
        toolbar = ctk.CTkFrame(content, fg_color="transparent", height=40)
        toolbar.pack(fill="x", pady=(5, 5))
        
        ctk.CTkButton(
            toolbar,
            text="📂 Add Files...",
            command=self.add_files,
            width=120,
            height=32,
            font=ctk.CTkFont(size=FONT_SIZES['small'])
        ).pack(side="left")
        
        self.stats_label = ctk.CTkLabel(
            toolbar,
            text="0 files (0.0 MB)",
            text_color="gray",
            font=ctk.CTkFont(size=FONT_SIZES['small'])
        )
        self.stats_label.pack(side="left", padx=15)
        
        # File list
        self.file_list_frame = ctk.CTkScrollableFrame(
            content,
            fg_color=COLORS['dark_bg'],
            height=300
        )
        self.file_list_frame.pack(fill="both", expand=True, pady=(0, 10))
        self.file_list_frame.grid_columnconfigure(0, weight=1)
        
        self.refresh_file_list()
        
        # Footer
        footer = ctk.CTkFrame(self, height=60, corner_radius=0)
        footer.grid(row=2, column=0, sticky="ew")
        
        self.create_button = ctk.CTkButton(
            footer,
            text="Start Indexing",
            command=self.start_indexing,
            width=180,
            height=40,
            font=ctk.CTkFont(size=FONT_SIZES['normal'], weight="bold"),
            fg_color=COLORS['success'],
            hover_color=COLORS['success_hover']
        )
        self.create_button.pack(side="right", padx=20, pady=10)
        
        ctk.CTkButton(
            footer,
            text="Cancel",
            command=self.destroy,
            width=90,
            height=40,
            font=ctk.CTkFont(size=FONT_SIZES['normal']),
            fg_color="transparent",
            border_width=1
        ).pack(side="right", padx=(0, 10), pady=10)
    
    def add_files(self):
        """Add files to list"""
        files = filedialog.askopenfilenames(
            title="Select Documents",
            filetypes=SUPPORTED_FILE_TYPES
        )
        
        if files:
            current_paths = {item["path"] for item in self.selected_items}
            for f in files:
                if f not in current_paths:
                    self.selected_items.append({
                        "path": f,
                        "category": "Uncategorized",
                        "project": "N/A",
                    })
            self.refresh_file_list()
    
    def remove_file(self, file_path):
        """Remove file from list"""
        self.selected_items = [item for item in self.selected_items if item["path"] != file_path]
        self.refresh_file_list()
    
    def refresh_file_list(self):
        """Refresh file list display"""
        # Clear existing
        for widget in self.file_list_frame.winfo_children():
            widget.destroy()
        
        total_size = 0
        
        if not self.selected_items:
            # Empty state
            empty = ctk.CTkFrame(self.file_list_frame, fg_color="transparent")
            empty.pack(expand=True, fill="both", pady=40)
            
            ctk.CTkLabel(empty, text="📂", font=ctk.CTkFont(size=40)).pack()
            ctk.CTkLabel(
                empty,
                text=MESSAGES['no_files'],
                font=ctk.CTkFont(size=FONT_SIZES['medium'], weight="bold"),
                text_color="gray"
            ).pack(pady=(10, 0))
            ctk.CTkLabel(
                empty,
                text=MESSAGES['no_files_subtitle'],
                font=ctk.CTkFont(size=FONT_SIZES['small']),
                text_color="gray"
            ).pack()
        else:
            # File list with headers
            app_settings = load_app_settings()
            categories = app_settings.get("categories", DEFAULT_CATEGORIES)
            projects = app_settings.get("projects", DEFAULT_PROJECTS)
            
            # Headers
            header_row = ctk.CTkFrame(self.file_list_frame, fg_color="transparent")
            header_row.pack(fill="x", pady=(5, 8), padx=5)
            
            # File Name header (expandable)
            ctk.CTkLabel(
                header_row,
                text="Documents",
                font=ctk.CTkFont(size=FONT_SIZES['tiny'], weight="bold"),
                text_color="gray",
                anchor="w"
            ).pack(side="left", padx=10, fill="x", expand=True)
            
            # Spacer for remove button
            ctk.CTkLabel(header_row, text="Actions", width=80, 
                        font=ctk.CTkFont(size=FONT_SIZES['tiny'], weight="bold"),
                        text_color="gray").pack(side="right", padx=10)
            
            # File rows
            for i, item in enumerate(self.selected_items):
                file_path = item["path"]
                path = Path(file_path)
                
                try:
                    size = path.stat().st_size
                    total_size += size
                    size_str = f"{size / (1024 * 1024):.1f} MB"
                except:
                    size_str = "Unknown"
                
                # Get page count for PDFs
                page_count = ""
                if path.suffix.lower() == ".pdf":
                    try:
                        doc = pymupdf.open(file_path)
                        page_count = f"{len(doc)} pages"
                        doc.close()
                    except:
                        page_count = "? pages"
                
                # Container for this file (two rows)
                container = ctk.CTkFrame(self.file_list_frame, fg_color=COLORS['darker_bg'], corner_radius=6)
                container.pack(fill="x", pady=3, padx=5)
                item["row_widget"] = container
                
                # === ROW 1: File name + dropdowns + remove button ===
                row1 = ctk.CTkFrame(container, fg_color="transparent")
                row1.pack(fill="x", padx=5, pady=(5, 2))
                
                # File name with icon
                name_frame = ctk.CTkFrame(row1, fg_color="transparent")
                name_frame.pack(side="left", fill="x", expand=True)
                
                ctk.CTkLabel(
                    name_frame,
                    text=f"📄 {path.name}",
                    font=ctk.CTkFont(size=FONT_SIZES['small'], weight="bold"),
                    anchor="w"
                ).pack(side="left", padx=5)
                
                # Category dropdown
                category_var = ctk.StringVar(value=item.get("category", "Uncategorized"))
                
                def make_category_cb(idx, var):
                    def _update(*_):
                        self.selected_items[idx]["category"] = var.get()
                    return _update
                
                ctk.CTkLabel(row1, text="Category:", font=ctk.CTkFont(size=FONT_SIZES['tiny']),
                           text_color="gray").pack(side="left", padx=(10, 5))
                
                category_menu = ctk.CTkOptionMenu(
                    row1,
                    variable=category_var,
                    values=categories,
                    width=130,
                    height=28,
                    font=ctk.CTkFont(size=FONT_SIZES['tiny'])
                )
                category_menu.pack(side="left", padx=5)
                category_var.trace_add("write", make_category_cb(i, category_var))
                
                # Project dropdown
                project_var = ctk.StringVar(value=item.get("project", "N/A"))
                
                def make_project_cb(idx, var):
                    def _update(*_):
                        self.selected_items[idx]["project"] = var.get()
                    return _update
                
                ctk.CTkLabel(row1, text="Project:", font=ctk.CTkFont(size=FONT_SIZES['tiny']),
                           text_color="gray").pack(side="left", padx=(10, 5))
                
                project_menu = ctk.CTkOptionMenu(
                    row1,
                    variable=project_var,
                    values=projects,
                    width=130,
                    height=28,
                    font=ctk.CTkFont(size=FONT_SIZES['tiny'])
                )
                project_menu.pack(side="left", padx=5)
                project_var.trace_add("write", make_project_cb(i, project_var))
                
                # Remove button
                remove_btn = ctk.CTkButton(
                    row1,
                    text="✕",
                    width=28,
                    height=28,
                    font=ctk.CTkFont(size=10, weight="bold"),
                    fg_color=COLORS['danger'],
                    hover_color=COLORS['danger_hover'],
                    command=lambda p=file_path: self.remove_file(p)
                )
                remove_btn.pack(side="right", padx=5)
                item["remove_btn_widget"] = remove_btn
                
                # === ROW 2: Info, status, progress ===
                row2 = ctk.CTkFrame(container, fg_color="transparent")
                row2.pack(fill="x", padx=5, pady=(0, 5))
                
                # Size and page info
                info_text = f"📊 {size_str}" + (f" • {page_count}" if page_count else "")
                ctk.CTkLabel(
                    row2,
                    text=info_text,
                    font=ctk.CTkFont(size=FONT_SIZES['tiny']),
                    text_color="#888888",
                    anchor="w"
                ).pack(side="left", padx=10)
                
                # Status icon
                status_label = ctk.CTkLabel(row2, text=STATUS_ICONS['waiting'], 
                                           font=ctk.CTkFont(size=14), width=30)
                status_label.pack(side="right", padx=(5, 5))
                item["status_widget"] = status_label
                
                # Info label (for chunk count)
                info_label = ctk.CTkLabel(
                    row2,
                    text="",
                    font=ctk.CTkFont(size=FONT_SIZES['tiny']),
                    text_color="#00aaff",
                    width=80
                )
                info_label.pack(side="right", padx=(5, 5))
                item["info_widget"] = info_label
                
                # Progress bar (hidden initially)
                progress_bar = ctk.CTkProgressBar(row2, width=120, height=8, mode="indeterminate")
                progress_bar.pack(side="right", padx=(5, 5))
                progress_bar.pack_forget()  # Hide initially
                item["progress_widget"] = progress_bar
        
        # Update stats
        count = len(self.selected_items)
        size_mb = total_size / (1024 * 1024)
        self.stats_label.configure(text=f"{count} files ({size_mb:.1f} MB)")
    
    def start_indexing(self):
        """Start indexing process"""
        if not self.selected_items:
            messagebox.showwarning("No Files", "Please select at least one file")
            return
        
        self.create_button.configure(state="disabled", text="Processing...")
        
        for item in self.selected_items:
            if "remove_btn_widget" in item:
                item["remove_btn_widget"].configure(state="disabled")
        
        thread = threading.Thread(target=self.run_indexing)
        thread.daemon = True
        thread.start()
    
    def update_status(self, file_path, status, info_text=""):
        """Update file status indicator"""
        for item in self.selected_items:
            if item["path"] == file_path:
                # Update info label (chunk count, etc.)
                if "info_widget" in item and info_text:
                    item["info_widget"].configure(text=info_text)
                
                # Update progress bar visibility
                if "progress_widget" in item:
                    if status in ["copying", "indexing"]:
                        item["progress_widget"].pack(side="right", padx=(5, 5))
                        item["progress_widget"].start()
                    else:
                        item["progress_widget"].stop()
                        item["progress_widget"].pack_forget()
                
                # Update status icon
                if "status_widget" in item:
                    item["status_widget"].configure(
                        text=STATUS_ICONS.get(status, STATUS_ICONS['waiting']),
                        text_color=STATUS_COLORS.get(status, 'gray')
                    )
                
                # Update row color
                if "row_widget" in item:
                    if status == "success":
                        item["row_widget"].configure(fg_color=COLORS['success_tint'])
                    elif status == "error":
                        item["row_widget"].configure(fg_color=COLORS['error_tint'])
                break
    
    def run_indexing(self):
        """Run indexing in background"""
        settings = get_settings()
        data_dir = Path(settings.data_dir)
        data_dir.mkdir(exist_ok=True)
        
        success_count = 0
        error_count = 0
        mapping = {}
        total_files = len(self.selected_items)
        
        # Copy files
        def update_button(text):
            self.create_button.configure(text=text)
        
        self.after(0, update_button, "Copying files...")
        
        for idx, item in enumerate(self.selected_items, 1):
            file_path = item["path"]
            file_name = Path(file_path).name
            
            try:
                self.after(0, self.update_status, file_path, "copying")
                self.after(0, update_button, f"Copying {idx}/{total_files}: {file_name}")
                
                dest = data_dir / file_name
                shutil.copy2(file_path, dest)
                
                mapping[file_name] = {
                    "category": item.get("category", "Uncategorized"),
                    "project": item.get("project", "N/A")
                }
                item["copied_path"] = str(dest)
                item["file_name"] = file_name
                
                # Show copied status briefly
                self.after(0, self.update_status, file_path, "waiting")
                
            except Exception as e:
                logger.error(f"Copy error {file_path}: {e}")
                self.after(0, self.update_status, file_path, "error")
                error_count += 1
        
        save_document_categories(mapping)
        
        # Index files
        self.after(0, update_button, "Initializing indexer...")
        
        try:
            ingestion = DocumentIngestion()
            
            for idx, item in enumerate(self.selected_items, 1):
                if "copied_path" not in item:
                    continue
                
                file_path = item["path"]
                file_name = item["file_name"]
                
                try:
                    self.after(0, self.update_status, file_path, "indexing", "parsing...")
                    self.after(0, update_button, f"Indexing {idx}/{total_files}: {file_name}")
                    
                    # Use ingest_single_file method
                    result = ingestion.ingest_single_file(
                        file_path=item["copied_path"],
                        category=item.get("category", "Uncategorized"),
                        project=item.get("project", "N/A")
                    )
                    
                    if result["success"]:
                        chunk_info = f"{result['chunks']} chunks"
                        self.after(0, self.update_status, file_path, "success", chunk_info)
                        success_count += 1
                    else:
                        self.after(0, self.update_status, file_path, "error", "failed")
                        error_count += 1
                        
                except Exception as e:
                    logger.error(f"Index error {file_path}: {e}")
                    self.after(0, self.update_status, file_path, "error", "error")
                    error_count += 1
            
            self.after(0, self.finalize, success_count, error_count)
        except Exception as e:
            logger.error(f"Indexing failed: {e}")
            self.after(0, lambda: messagebox.showerror("Error", f"Indexing failed:\n{str(e)}"))
    
    def finalize(self, success, error):
        """Finalize indexing"""
        self.success = True
        
        # Update button to Close
        self.create_button.configure(
            state="normal",
            text="Close",
            fg_color=COLORS['primary'],
            hover_color=COLORS['primary_hover'],
            command=self.destroy
        )
        
        if error == 0:
            self.create_button.configure(text="Close ✓")
        else:
            self.create_button.configure(text=f"Close ({error} errors)")
