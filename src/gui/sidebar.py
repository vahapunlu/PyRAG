"""
Sidebar Component for PyRAG GUI

Contains all sidebar-related widgets and functionality.
"""

import customtkinter as ctk
from .constants import *


class Sidebar:
    """Sidebar component with filters and action buttons"""
    
    def __init__(self, parent, callbacks):
        """
        Initialize sidebar
        
        Args:
            parent: Parent window (PyRAGApp instance)
            callbacks: Dictionary of callback functions
        """
        self.parent = parent
        self.callbacks = callbacks
        
        # Create sidebar frame
        self.frame = ctk.CTkFrame(parent, width=SIDEBAR_WIDTH, corner_radius=0)
        self.frame.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.frame.grid_rowconfigure(10, weight=1)
        
        self._create_header()
        self._create_status_section()
        self._create_action_buttons()
        self._create_footer()
    
    def _create_header(self):
        """Create logo and title"""
        title_size = int(32 * PHI / 1.618)
        logo_label = ctk.CTkLabel(
            self.frame,
            text="⚡ PyRAG",
            font=ctk.CTkFont(size=title_size, weight="bold")
        )
        logo_label.grid(row=0, column=0, padx=20, pady=(int(20 * PHI), 10))
        
        subtitle_size = int(title_size / PHI)
        subtitle_label = ctk.CTkLabel(
            self.frame,
            text="Engineering Standards AI",
            font=ctk.CTkFont(size=subtitle_size)
        )
        subtitle_label.grid(row=1, column=0, padx=20, pady=(0, int(20 * PHI)))
    
    def _create_status_section(self):
        """Create API status indicators"""
        status_frame = ctk.CTkFrame(self.frame)
        status_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        status_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(
            status_frame,
            text="⚙️ API Status",
            font=ctk.CTkFont(size=FONT_SIZES['normal'], weight="bold")
        ).grid(row=0, column=0, padx=10, pady=(10, 5), columnspan=2, sticky="w")
        
        # Embedding status
        self.embedding_indicator = ctk.CTkLabel(
            status_frame,
            text=STATUS_ICONS['online'],
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=STATUS_COLORS['online'],
            width=10
        )
        self.embedding_indicator.grid(row=1, column=0, padx=(10, 2), pady=3, sticky="w")
        
        self.embedding_label = ctk.CTkLabel(
            status_frame,
            text="Embedding: OpenAI",
            font=ctk.CTkFont(size=FONT_SIZES['tiny']),
            anchor="w",
            text_color=COLORS['gray']
        )
        self.embedding_label.grid(row=1, column=1, padx=2, pady=3, sticky="w")
        
        # LLM status
        self.llm_indicator = ctk.CTkLabel(
            status_frame,
            text=STATUS_ICONS['online'],
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=STATUS_COLORS['online'],
            width=10
        )
        self.llm_indicator.grid(row=2, column=0, padx=(10, 2), pady=(0, 10), sticky="w")
        
        self.llm_label = ctk.CTkLabel(
            status_frame,
            text="LLM: DeepSeek",
            font=ctk.CTkFont(size=FONT_SIZES['tiny']),
            anchor="w",
            text_color=COLORS['gray']
        )
        self.llm_label.grid(row=2, column=1, padx=2, pady=(0, 10), sticky="w")
    
    def _create_action_buttons(self):
        """Create action buttons with golden ratio layout"""
        # Primary action
        ctk.CTkButton(
            self.frame,
            text="➕ New Document",
            command=self.callbacks.get('open_new_document'),
            height=BUTTON_HEIGHTS['primary'],
            font=ctk.CTkFont(size=FONT_SIZES['medium'], weight="bold"),
            fg_color=COLORS['primary'],
            hover_color=COLORS['primary_hover'],
            corner_radius=int(10 * PHI / 1.618)
        ).grid(row=3, column=0, padx=20, pady=(SPACING['major'], SPACING['minor']), sticky="ew")
        
        # Secondary actions
        ctk.CTkButton(
            self.frame,
            text="📊 View Statistics",
            command=self.callbacks.get('show_statistics'),
            height=BUTTON_HEIGHTS['secondary'],
            font=ctk.CTkFont(size=FONT_SIZES['normal']),
            fg_color="transparent",
            border_width=2,
            corner_radius=8
        ).grid(row=4, column=0, padx=20, pady=SPACING['minor'], sticky="ew")
        
        ctk.CTkButton(
            self.frame,
            text="🗑️ Clear Chat",
            command=self.callbacks.get('clear_chat'),
            height=BUTTON_HEIGHTS['secondary'],
            font=ctk.CTkFont(size=FONT_SIZES['normal']),
            fg_color="transparent",
            border_width=2,
            corner_radius=8
        ).grid(row=5, column=0, padx=20, pady=SPACING['minor'], sticky="ew")
        
        ctk.CTkButton(
            self.frame,
            text="⚡ Clear Cache",
            command=self.callbacks.get('clear_cache'),
            height=BUTTON_HEIGHTS['secondary'],
            font=ctk.CTkFont(size=FONT_SIZES['normal']),
            fg_color="transparent",
            border_width=2,
            corner_radius=8
        ).grid(row=6, column=0, padx=20, pady=SPACING['minor'], sticky="ew")
        
        ctk.CTkButton(
            self.frame,
            text="🔗 Cross-Reference",
            command=self.callbacks.get('open_cross_reference'),
            height=BUTTON_HEIGHTS['secondary'],
            font=ctk.CTkFont(size=FONT_SIZES['normal']),
            fg_color="transparent",
            border_width=2,
            corner_radius=8
        ).grid(row=7, column=0, padx=20, pady=SPACING['minor'], sticky="ew")
        
        ctk.CTkButton(
            self.frame,
            text="📄 Auto-Summary",
            command=self.callbacks.get('open_auto_summary'),
            height=BUTTON_HEIGHTS['secondary'],
            font=ctk.CTkFont(size=FONT_SIZES['normal']),
            fg_color="transparent",
            border_width=2,
            corner_radius=8
        ).grid(row=8, column=0, padx=20, pady=SPACING['minor'], sticky="ew")
        
        ctk.CTkButton(
            self.frame,
            text="⚙️ Settings",
            command=self.callbacks.get('open_settings'),
            height=BUTTON_HEIGHTS['secondary'],
            font=ctk.CTkFont(size=FONT_SIZES['normal']),
            fg_color="transparent",
            border_width=2,
            corner_radius=8
        ).grid(row=9, column=0, padx=20, pady=SPACING['minor'], sticky="ew")
        
        ctk.CTkButton(
            self.frame,
            text="🗄️ Database",
            command=self.callbacks.get('open_database'),
            height=BUTTON_HEIGHTS['secondary'],
            font=ctk.CTkFont(size=FONT_SIZES['normal']),
            fg_color="transparent",
            border_width=2,
            corner_radius=8
        ).grid(row=10, column=0, padx=20, pady=(SPACING['minor'], SPACING['major']), sticky="ew")
    
    def _create_footer(self):
        """Create version info"""
        ctk.CTkLabel(
            self.frame,
            text="v1.3.0 | Semantic Cache",
            font=ctk.CTkFont(size=FONT_SIZES['mini']),
            text_color="gray"
        ).grid(row=11, column=0, padx=20, pady=(int(10 / PHI), int(20 * PHI)), sticky="s")
    
    def update_status(self, embedding_status=True, llm_status=True):
        """Update API status indicators"""
        self.embedding_indicator.configure(
            text_color=STATUS_COLORS['online'] if embedding_status else STATUS_COLORS['offline']
        )
        self.llm_indicator.configure(
            text_color=STATUS_COLORS['online'] if llm_status else STATUS_COLORS['offline']
        )
