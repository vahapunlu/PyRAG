"""
Settings Dialog

Dialog for managing categories and projects configuration.
"""

import customtkinter as ctk
from tkinter import messagebox

from ..utils import load_app_settings, save_app_settings
from .constants import *


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
