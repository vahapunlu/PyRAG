"""
Dialog Windows for PyRAG GUI

Contains NewDocumentDialog and SettingsDialog classes.
Note: Full implementation imported from legacy app_gui.py
This file serves as a bridge during refactoring.
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
from pathlib import Path
import shutil

from loguru import logger

from ..utils import (
    get_settings,
    save_document_categories,
    load_app_settings,
    save_app_settings,
)
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
            
            for text, width in [("File Name", None), ("Project", 150), ("Category", 150), ("Size", 80)]:
                ctk.CTkLabel(
                    header_row,
                    text=text,
                    font=ctk.CTkFont(size=FONT_SIZES['tiny'], weight="bold"),
                    text_color="gray",
                    width=width,
                    anchor="w" if width is None else "center"
                ).pack(side="left", padx=10, fill="x" if width is None else None, expand=width is None)
            
            ctk.CTkLabel(header_row, text="", width=44).pack(side="right", padx=10)
            
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
                
                row = ctk.CTkFrame(self.file_list_frame, fg_color=COLORS['darker_bg'], corner_radius=6)
                row.pack(fill="x", pady=2, padx=5)
                
                # File name
                ctk.CTkLabel(
                    row,
                    text=f"📄 {path.name}",
                    font=ctk.CTkFont(size=FONT_SIZES['small']),
                    anchor="w"
                ).pack(side="left", padx=10, pady=8, fill="x", expand=True)
                
                # Project dropdown
                project_var = ctk.StringVar(value=item.get("project", "N/A"))
                
                def make_project_cb(idx, var):
                    def _update(*_):
                        self.selected_items[idx]["project"] = var.get()
                    return _update
                
                project_menu = ctk.CTkOptionMenu(
                    row,
                    variable=project_var,
                    values=projects,
                    width=150,
                    font=ctk.CTkFont(size=FONT_SIZES['tiny'])
                )
                project_menu.pack(side="left", padx=10)
                project_var.trace_add("write", make_project_cb(i, project_var))
                
                # Category dropdown
                category_var = ctk.StringVar(value=item.get("category", "Uncategorized"))
                
                def make_category_cb(idx, var):
                    def _update(*_):
                        self.selected_items[idx]["category"] = var.get()
                    return _update
                
                category_menu = ctk.CTkOptionMenu(
                    row,
                    variable=category_var,
                    values=categories,
                    width=150,
                    font=ctk.CTkFont(size=FONT_SIZES['tiny'])
                )
                category_menu.pack(side="left", padx=10)
                category_var.trace_add("write", make_category_cb(i, category_var))
                
                # Size
                ctk.CTkLabel(
                    row,
                    text=size_str,
                    font=ctk.CTkFont(size=FONT_SIZES['tiny']),
                    text_color="gray",
                    width=80
                ).pack(side="left", padx=10)
                
                # Status
                status_label = ctk.CTkLabel(row, text=STATUS_ICONS['waiting'], font=ctk.CTkFont(size=14), width=30)
                status_label.pack(side="right", padx=(5, 5))
                item["status_widget"] = status_label
                item["row_widget"] = row
                
                # Remove button
                remove_btn = ctk.CTkButton(
                    row,
                    text="✕",
                    width=24,
                    height=24,
                    font=ctk.CTkFont(size=10, weight="bold"),
                    fg_color=COLORS['danger'],
                    hover_color=COLORS['danger_hover'],
                    command=lambda p=file_path: self.remove_file(p)
                )
                remove_btn.pack(side="right", padx=10)
                item["remove_btn_widget"] = remove_btn
        
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
    
    def update_status(self, file_path, status):
        """Update file status indicator"""
        for item in self.selected_items:
            if item["path"] == file_path:
                if "status_widget" in item:
                    item["status_widget"].configure(
                        text=STATUS_ICONS.get(status, STATUS_ICONS['waiting']),
                        text_color=STATUS_COLORS.get(status, 'gray')
                    )
                
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
        
        # Copy files
        self.after(0, self.create_button.configure, {"text": "Copying files..."})
        
        for item in self.selected_items:
            file_path = item["path"]
            try:
                self.after(0, self.update_status, file_path, "copying")
                dest = data_dir / Path(file_path).name
                shutil.copy2(file_path, dest)
                
                file_name = Path(file_path).name
                mapping[file_name] = {
                    "category": item.get("category", "Uncategorized"),
                    "project": item.get("project", "N/A")
                }
                item["copied_path"] = str(dest)
                item["file_name"] = file_name
            except Exception as e:
                logger.error(f"Copy error {file_path}: {e}")
                self.after(0, self.update_status, file_path, "error")
                error_count += 1
        
        save_document_categories(mapping)
        
        # Index files
        self.after(0, self.create_button.configure, {"text": "Indexing..."})
        
        try:
            ingestion = DocumentIngestion()
            
            for idx, item in enumerate(self.selected_items):
                if "copied_path" not in item:
                    continue
                
                file_path = item["path"]
                
                try:
                    self.after(0, self.update_status, file_path, "indexing")
                    self.after(0, self.create_button.configure, {"text": f"Indexing {idx+1}/{len(self.selected_items)}..."})
                    
                    ingestion.process_and_load_documents([item["copied_path"]])
                    
                    self.after(0, self.update_status, file_path, "success")
                    success_count += 1
                except Exception as e:
                    logger.error(f"Index error {file_path}: {e}")
                    self.after(0, self.update_status, file_path, "error")
                    error_count += 1
            
            self.after(0, self.finalize, success_count, error_count)
        except Exception as e:
            logger.error(f"Indexing failed: {e}")
            self.after(0, messagebox.showerror, "Error", f"Indexing failed:\n{str(e)}")
    
    def finalize(self, success, error):
        """Finalize indexing"""
        self.success = True
        
        if error == 0:
            msg = f"✅ Successfully indexed {success} file(s)!"
            messagebox.showinfo("Success", msg)
        else:
            msg = f"⚠️ Indexed {success} file(s), {error} failed"
            messagebox.showwarning("Partial Success", msg)
        
        self.destroy()


class SettingsDialog(ctk.CTkToplevel):
    """Settings dialog for managing categories and projects"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.parent = parent
        self.title("Settings")
        self.geometry(f"{WINDOW_SIZES['dialog_width']}x{WINDOW_SIZES['dialog_height']}")
        self.resizable(False, False)
        
        self.transient(parent)
        self.grab_set()
        
        self.app_settings = load_app_settings()
        self.selected_category = None
        self.selected_project = None
        
        self.create_widgets()
    
    def create_widgets(self):
        """Create settings UI"""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header
        ctk.CTkLabel(
            self,
            text="⚙️ Application Settings",
            font=ctk.CTkFont(size=FONT_SIZES['subtitle'], weight="bold")
        ).grid(row=0, column=0, padx=25, pady=(25, 15), sticky="w")
        
        # Content
        content = ctk.CTkFrame(self)
        content.grid(row=1, column=0, padx=25, pady=10, sticky="nsew")
        content.grid_columnconfigure((0, 1), weight=1)
        content.grid_rowconfigure(0, weight=1)
        
        # Categories Panel
        self._create_categories_panel(content)
        
        # Projects Panel
        self._create_projects_panel(content)
        
        # Bottom buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=2, column=0, padx=25, pady=(0, 25), sticky="e")
        
        ctk.CTkButton(
            btn_frame,
            text="Close",
            command=self.destroy,
            width=100,
            height=36,
            font=ctk.CTkFont(size=FONT_SIZES['normal'])
        ).pack(side="right", padx=(5, 0))
    
    def _create_categories_panel(self, parent):
        """Create categories management panel"""
        cat_frame = ctk.CTkFrame(parent)
        cat_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        cat_frame.grid_columnconfigure(0, weight=1)
        cat_frame.grid_rowconfigure(1, weight=1)
        
        # Header with count
        cat_header = ctk.CTkFrame(cat_frame, fg_color="transparent")
        cat_header.grid(row=0, column=0, padx=12, pady=(12, 8), sticky="ew")
        cat_header.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            cat_header,
            text="📂 Categories",
            font=ctk.CTkFont(size=FONT_SIZES['large'], weight="bold")
        ).grid(row=0, column=0, sticky="w")
        
        self.cat_count_label = ctk.CTkLabel(
            cat_header,
            text=f"{len(self.app_settings.get('categories', []))} items",
            font=ctk.CTkFont(size=FONT_SIZES['tiny']),
            text_color="gray"
        )
        self.cat_count_label.grid(row=0, column=1, sticky="e")
        
        # Scrollable list
        self.cat_scroll_frame = ctk.CTkScrollableFrame(cat_frame, height=220)
        self.cat_scroll_frame.grid(row=1, column=0, padx=12, pady=5, sticky="nsew")
        self.cat_scroll_frame.grid_columnconfigure(0, weight=1)
        
        self.cat_buttons = []
        self.refresh_category_list()
        
        # Add new
        add_cat_frame = ctk.CTkFrame(cat_frame, fg_color="transparent")
        add_cat_frame.grid(row=2, column=0, padx=12, pady=(8, 5), sticky="ew")
        add_cat_frame.grid_columnconfigure(0, weight=1)
        
        self.new_cat_entry = ctk.CTkEntry(
            add_cat_frame,
            placeholder_text="➕ Add new category...",
            height=36
        )
        self.new_cat_entry.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        self.new_cat_entry.bind("<Return>", lambda e: self.add_category())
        
        ctk.CTkButton(
            add_cat_frame,
            text="Add",
            width=80,
            height=36,
            command=self.add_category,
            font=ctk.CTkFont(size=FONT_SIZES['small'], weight="bold")
        ).grid(row=0, column=1)
        
        # Delete selected
        self.del_cat_button = ctk.CTkButton(
            cat_frame,
            text="🗑️ Delete Selected",
            width=0,
            height=36,
            fg_color=COLORS['danger'],
            hover_color=COLORS['danger_hover'],
            command=self.delete_category,
            state="disabled",
            font=ctk.CTkFont(size=FONT_SIZES['small'])
        )
        self.del_cat_button.grid(row=3, column=0, padx=12, pady=(5, 12), sticky="ew")
    
    def _create_projects_panel(self, parent):
        """Create projects management panel"""
        proj_frame = ctk.CTkFrame(parent)
        proj_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        proj_frame.grid_columnconfigure(0, weight=1)
        proj_frame.grid_rowconfigure(1, weight=1)
        
        # Header with count
        proj_header = ctk.CTkFrame(proj_frame, fg_color="transparent")
        proj_header.grid(row=0, column=0, padx=12, pady=(12, 8), sticky="ew")
        proj_header.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            proj_header,
            text="📁 Projects",
            font=ctk.CTkFont(size=FONT_SIZES['large'], weight="bold")
        ).grid(row=0, column=0, sticky="w")
        
        self.proj_count_label = ctk.CTkLabel(
            proj_header,
            text=f"{len(self.app_settings.get('projects', []))} items",
            font=ctk.CTkFont(size=FONT_SIZES['tiny']),
            text_color="gray"
        )
        self.proj_count_label.grid(row=0, column=1, sticky="e")
        
        # Scrollable list
        self.proj_scroll_frame = ctk.CTkScrollableFrame(proj_frame, height=220)
        self.proj_scroll_frame.grid(row=1, column=0, padx=12, pady=5, sticky="nsew")
        self.proj_scroll_frame.grid_columnconfigure(0, weight=1)
        
        self.proj_buttons = []
        self.refresh_project_list()
        
        # Add new
        add_proj_frame = ctk.CTkFrame(proj_frame, fg_color="transparent")
        add_proj_frame.grid(row=2, column=0, padx=12, pady=(8, 5), sticky="ew")
        add_proj_frame.grid_columnconfigure(0, weight=1)
        
        self.new_proj_entry = ctk.CTkEntry(
            add_proj_frame,
            placeholder_text="➕ Add new project...",
            height=36
        )
        self.new_proj_entry.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        self.new_proj_entry.bind("<Return>", lambda e: self.add_project())
        
        ctk.CTkButton(
            add_proj_frame,
            text="Add",
            width=80,
            height=36,
            command=self.add_project,
            font=ctk.CTkFont(size=FONT_SIZES['small'], weight="bold")
        ).grid(row=0, column=1)
        
        # Delete selected
        self.del_proj_button = ctk.CTkButton(
            proj_frame,
            text="🗑️ Delete Selected",
            width=0,
            height=36,
            fg_color=COLORS['danger'],
            hover_color=COLORS['danger_hover'],
            command=self.delete_project,
            state="disabled",
            font=ctk.CTkFont(size=FONT_SIZES['small'])
        )
        self.del_proj_button.grid(row=3, column=0, padx=12, pady=(5, 12), sticky="ew")
    
    def select_category(self, cat_name):
        """Select a category"""
        self.selected_category = cat_name
        self.refresh_category_list()
        self.del_cat_button.configure(state="normal")
    
    def select_project(self, proj_name):
        """Select a project"""
        self.selected_project = proj_name
        self.refresh_project_list()
        self.del_proj_button.configure(state="normal")
    
    def add_category(self):
        """Add new category"""
        name = (self.new_cat_entry.get() or "").strip()
        if not name:
            messagebox.showwarning("Empty Name", "Please enter a category name.")
            return
        
        categories = self.app_settings.get("categories", [])
        if name in categories:
            messagebox.showinfo("Already Exists", f"Category '{name}' already exists.")
            return
        
        categories.append(name)
        self.app_settings["categories"] = categories
        save_app_settings(self.app_settings)
        self.refresh_category_list()
        self.new_cat_entry.delete(0, "end")
        self.cat_count_label.configure(text=f"{len(categories)} items")
    
    def refresh_category_list(self):
        """Refresh category list"""
        for btn in self.cat_buttons:
            btn.destroy()
        self.cat_buttons.clear()
        
        categories = self.app_settings.get("categories", [])
        for idx, cat in enumerate(categories):
            is_selected = (cat == self.selected_category)
            
            btn = ctk.CTkButton(
                self.cat_scroll_frame,
                text=f"{'✓ ' if is_selected else '  '}{cat}",
                command=lambda c=cat: self.select_category(c),
                height=32,
                anchor="w",
                fg_color=COLORS['primary'] if is_selected else "transparent",
                hover_color=COLORS['primary_hover'] if is_selected else COLORS['dark_bg'],
                border_width=1 if not is_selected else 0,
                font=ctk.CTkFont(size=FONT_SIZES['small'])
            )
            btn.grid(row=idx, column=0, pady=2, sticky="ew")
            self.cat_buttons.append(btn)
    
    def delete_category(self):
        """Delete selected category"""
        if not self.selected_category:
            messagebox.showwarning("No Selection", "Please select a category to delete.")
            return
        
        result = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete '{self.selected_category}'?"
        )
        
        if not result:
            return
        
        categories = self.app_settings.get("categories", [])
        categories = [c for c in categories if c != self.selected_category]
        self.app_settings["categories"] = categories
        save_app_settings(self.app_settings)
        
        self.selected_category = None
        self.del_cat_button.configure(state="disabled")
        self.refresh_category_list()
        self.cat_count_label.configure(text=f"{len(categories)} items")
    
    def add_project(self):
        """Add new project"""
        name = (self.new_proj_entry.get() or "").strip()
        if not name:
            messagebox.showwarning("Empty Name", "Please enter a project name.")
            return
        
        projects = self.app_settings.get("projects", [])
        if name in projects:
            messagebox.showinfo("Already Exists", f"Project '{name}' already exists.")
            return
        
        projects.append(name)
        self.app_settings["projects"] = projects
        save_app_settings(self.app_settings)
        self.refresh_project_list()
        self.new_proj_entry.delete(0, "end")
        self.proj_count_label.configure(text=f"{len(projects)} items")
    
    def refresh_project_list(self):
        """Refresh project list"""
        for btn in self.proj_buttons:
            btn.destroy()
        self.proj_buttons.clear()
        
        projects = self.app_settings.get("projects", [])
        for idx, proj in enumerate(projects):
            is_selected = (proj == self.selected_project)
            
            btn = ctk.CTkButton(
                self.proj_scroll_frame,
                text=f"{'✓ ' if is_selected else '  '}{proj}",
                command=lambda p=proj: self.select_project(p),
                height=32,
                anchor="w",
                fg_color=COLORS['primary'] if is_selected else "transparent",
                hover_color=COLORS['primary_hover'] if is_selected else COLORS['dark_bg'],
                border_width=1 if not is_selected else 0,
                font=ctk.CTkFont(size=FONT_SIZES['small'])
            )
            btn.grid(row=idx, column=0, pady=2, sticky="ew")
            self.proj_buttons.append(btn)
    
    def delete_project(self):
        """Delete selected project"""
        if not self.selected_project:
            messagebox.showwarning("No Selection", "Please select a project to delete.")
            return
        
        result = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete '{self.selected_project}'?"
        )
        
        if not result:
            return
        
        projects = self.app_settings.get("projects", [])
        projects = [p for p in projects if p != self.selected_project]
        self.app_settings["projects"] = projects
        save_app_settings(self.app_settings)
        
        self.selected_project = None
        self.del_proj_button.configure(state="disabled")
        self.refresh_project_list()
        self.proj_count_label.configure(text=f"{len(projects)} items")


class DatabaseManagerDialog(ctk.CTkToplevel):
    """Database management dialog for editing document metadata"""
    
    def __init__(self, parent, query_engine):
        super().__init__(parent)
        
        self.parent = parent
        self.query_engine = query_engine
        self.title("Database Manager")
        
        # Window size
        width = 900
        height = 600
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        pos_x = (screen_w - width) // 2
        pos_y = (screen_h - height) // 2
        self.geometry(f"{width}x{height}+{pos_x}+{pos_y}")
        self.resizable(False, False)
        
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
        edit_frame = ctk.CTkFrame(parent)
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
        self.project_menu.grid(row=6, column=0, padx=15, pady=(0, 25), sticky="ew")
        
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
        self.update_btn.grid(row=7, column=0, padx=15, pady=(0, 10), sticky="ew")
        
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
        self.delete_btn.grid(row=8, column=0, padx=15, pady=(0, 15), sticky="ew")
        
        # Info label
        self.info_label = ctk.CTkLabel(
            edit_frame,
            text="← Select a document to edit",
            font=ctk.CTkFont(size=FONT_SIZES['tiny']),
            text_color="gray"
        )
        self.info_label.grid(row=9, column=0, padx=15, pady=(10, 0), sticky="w")
    
    def load_documents(self):
        """Load documents from database"""
        try:
            # Clear existing
            for widget in self.doc_scroll.winfo_children():
                widget.destroy()
            
            self.documents = []
            
            if not self.query_engine or not hasattr(self.query_engine, 'chroma_collection'):
                self.info_label.configure(text="⚠️ Database not available")
                return
            
            # Get all documents
            collection = self.query_engine.chroma_collection
            results = collection.get(include=['metadatas'], limit=10000)
            
            # Group by document name
            doc_map = {}
            for metadata in results.get('metadatas', []):
                doc_name = metadata.get('document_name')
                if doc_name and doc_name != 'Unknown':
                    if doc_name not in doc_map:
                        doc_map[doc_name] = {
                            'name': doc_name,
                            'category': metadata.get('categories', ''),
                            'project': metadata.get('project_name', 'N/A'),
                            'count': 0
                        }
                    doc_map[doc_name]['count'] += 1
            
            self.documents = list(doc_map.values())
            self.doc_count_label.configure(text=f"{len(self.documents)} documents")
            
            # Create buttons
            for idx, doc in enumerate(sorted(self.documents, key=lambda x: x['name'])):
                btn = ctk.CTkButton(
                    self.doc_scroll,
                    text=f"📄 {doc['name']} ({doc['count']} chunks)",
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
        
        # Enable buttons
        self.update_btn.configure(state="normal")
        self.delete_btn.configure(state="normal")
        
        self.info_label.configure(
            text=f"✏️ Editing: {doc['name']} | {doc['count']} chunks",
            text_color=COLORS['primary']
        )
    
    def update_document(self):
        """Update document metadata"""
        if not self.selected_doc:
            return
        
        new_name = self.name_entry.get().strip()
        new_category = self.category_var.get()
        new_project = self.project_var.get()
        
        if not new_name:
            messagebox.showwarning("Invalid Name", "Document name cannot be empty.")
            return
        
        # First confirmation
        result = messagebox.askyesno(
            "Update Document",
            f"Update all chunks of '{self.selected_doc['name']}'?\n\n"
            f"New name: {new_name}\n"
            f"New category: {new_category}\n"
            f"New project: {new_project}\n\n"
            f"Total chunks to update: {self.selected_doc['count']}",
            icon='question'
        )
        
        if not result:
            return
        
        # Second confirmation
        confirm = messagebox.askyesno(
            "⚠️ Final Confirmation",
            f"This will update {self.selected_doc['count']} database entries.\n\n"
            f"Are you absolutely sure you want to proceed?",
            icon='warning'
        )
        
        if not confirm:
            return
        
        try:
            collection = self.query_engine.chroma_collection
            
            # Get all chunks for this document
            results = collection.get(
                where={"document_name": self.selected_doc['name']},
                include=['metadatas']
            )
            
            if results['ids']:
                # Update metadata
                updated_metadatas = []
                for meta in results['metadatas']:
                    new_meta = meta.copy()
                    new_meta['document_name'] = new_name
                    new_meta['categories'] = new_category
                    new_meta['project_name'] = new_project
                    updated_metadatas.append(new_meta)
                
                # Batch update
                collection.update(
                    ids=results['ids'],
                    metadatas=updated_metadatas
                )
                
                messagebox.showinfo(
                    "Success",
                    f"Updated {len(results['ids'])} chunks successfully!"
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
            f"This will remove all {self.selected_doc['count']} chunks from the database.\n"
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
            f"Chunks to delete: {self.selected_doc['count']}\n\n"
            f"Are you absolutely certain you want to proceed?",
            icon='warning'
        )
        
        if not final_confirm:
            return
        
        try:
            collection = self.query_engine.chroma_collection
            
            # Get all chunks for this document
            results = collection.get(
                where={"document_name": self.selected_doc['name']},
                include=['metadatas']
            )
            
            if results['ids']:
                # Delete all chunks
                collection.delete(ids=results['ids'])
                
                messagebox.showinfo(
                    "Success",
                    f"Deleted {len(results['ids'])} chunks of '{self.selected_doc['name']}'!"
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
