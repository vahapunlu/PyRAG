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
        
        # Create sidebar frame (Docker-style dark background)
        self.frame = ctk.CTkFrame(
            parent, 
            width=SIDEBAR_WIDTH, 
            corner_radius=0,
            fg_color=COLORS['darker_bg'],
            border_width=0
        )
        self.frame.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.frame.grid_rowconfigure(99, weight=1)  # Push footer to bottom
        
        self._create_header()
        self._create_status_section()
        self._create_action_buttons()
        self._create_footer()
    
    def _create_header(self):
        """Create logo and title"""
        logo_label = ctk.CTkLabel(
            self.frame,
            text="⚡ PyRAG",
            font=ctk.CTkFont(size=FONT_SIZES['title'], weight="bold")
        )
        logo_label.grid(row=0, column=0, padx=20, pady=(20, 5))
        
        subtitle_label = ctk.CTkLabel(
            self.frame,
            text="Engineering Standards AI",
            font=ctk.CTkFont(size=FONT_SIZES['small'])
        )
        subtitle_label.grid(row=1, column=0, padx=20, pady=(0, 16))
    
    def _create_status_section(self):
        """Create API status indicators"""
        status_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
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
            font=ctk.CTkFont(size=16, weight="bold"),  # Increased visibility
            text_color=STATUS_COLORS['online'],
            width=10
        )
        self.embedding_indicator.grid(row=1, column=0, padx=(10, 2), pady=3, sticky="w")
        
        self.embedding_label = ctk.CTkLabel(
            status_frame,
            text="Embedding: OpenAI",
            font=ctk.CTkFont(size=FONT_SIZES['small']),  # Increased from tiny
            anchor="w",
            text_color=COLORS['gray']
        )
        self.embedding_label.grid(row=1, column=1, padx=2, pady=3, sticky="w")
        
        # LLM status
        self.llm_indicator = ctk.CTkLabel(
            status_frame,
            text=STATUS_ICONS['online'],
            font=ctk.CTkFont(size=16, weight="bold"),  # Increased visibility
            text_color=STATUS_COLORS['online'],
            width=10
        )
        self.llm_indicator.grid(row=2, column=0, padx=(10, 2), pady=(0, 10), sticky="w")
        
        self.llm_label = ctk.CTkLabel(
            status_frame,
            text="LLM: DeepSeek",
            font=ctk.CTkFont(size=FONT_SIZES['small']),  # Increased from tiny
            anchor="w",
            text_color=COLORS['gray']
        )
        self.llm_label.grid(row=2, column=1, padx=2, pady=(0, 10), sticky="w")
    
    def _create_menu_button(self, text, icon, command, row):
        """
        Create a custom compound button with separate Icon and Text scaling.
        Uses a Frame + 2 Labels to achieve perfect alignment and sizing control.
        """
        # Container Frame (acts as the button background)
        btn_frame = ctk.CTkFrame(
            self.frame,
            corner_radius=6,
            fg_color="transparent",
            height=45,
            width=SIDEBAR_WIDTH - 30,
            cursor="hand2"
        )
        btn_frame.grid(row=row, column=0, padx=15, pady=2, sticky="ew")
        btn_frame.grid_propagate(False) # Force height
        
        # Grid layout for alignment
        btn_frame.grid_columnconfigure(0, weight=0)             # Icon column auto matches icon_frame
        btn_frame.grid_columnconfigure(1, weight=1)             # Text column expands

        # Icon Container (Fixed Size to normalize emoji widths)
        icon_frame = ctk.CTkFrame(btn_frame, fg_color="transparent", width=45, height=45)
        icon_frame.grid(row=0, column=0, sticky="nsew")
        icon_frame.grid_propagate(False) # Prevent expansion based on icon content
        
        # Icon Label (2x Size)
        # REVERT & FIX: 
        # 1. "East" anchor caused icons to disappear (likely clipped out of frame).
        # 2. "Center" anchor caused "floating" look for narrow icons.
        # SOLUTION: "West" (Left) anchor with fixed padding. 
        # This ensures all icons start at the EXACT same X-coordinate (10px).
        # Visually this creates a strong vertical line for the eye.
        icon_label = ctk.CTkLabel(
            icon_frame,
            text=icon,
            font=ctk.CTkFont(size=26),
            text_color="#e0e0e0",
            anchor="w" # Align text to left
        )
        # Place left edge of text at 8px from left edge of frame
        icon_label.place(relx=0.0, rely=0.5, anchor="w", x=8)

        # Text Label (1.5x Size & Bold) aligned with New Document style
        text_label = ctk.CTkLabel(
            btn_frame,
            text=text,
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#e0e0e0",
            anchor="w"
        )
        # Consistent padding from the icon frame
        text_label.grid(row=0, column=1, sticky="ew", padx=(5, 10))

        # HOVER PROXY
        # We need to bind events to all elements to simulate a single button
        
        def on_enter(e):
            btn_frame.configure(fg_color=COLORS['hover'])
        
        def on_leave(e):
            btn_frame.configure(fg_color="transparent")
            
        def on_click(e):
            if command:
                command()

        for widget in [btn_frame, icon_frame, icon_label, text_label]:
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
            widget.bind("<Button-1>", on_click)

        return btn_frame

    def _create_action_buttons(self):
        """Create organized action buttons with section-less layout"""
        row = 3
        
        # PRIMARY BUTTON (New Document)
        # Kept as standard button for "Primary" look but matched style
        ctk.CTkButton(
            self.frame,
            text="New Document",
            command=self.callbacks.get('open_new_document'),
            height=45,
            font=ctk.CTkFont(size=16, weight="bold"), # Matched size
            fg_color=COLORS['primary'],
            hover_color=COLORS['primary_hover'],
            corner_radius=6
        ).grid(row=row, column=0, padx=15, pady=(20, 20), sticky="ew")
        row += 1

        # LIST OF MENU ITEMS separated into Text and Icon
        items = [
            ("View Statistics", "📊", 'show_statistics'),
            ("Clear Chat", "🗑️", 'clear_chat'),
            ("Query History", "📜", 'show_history'),
            ("Cross-Reference", "🔗", 'open_cross_reference'),
            ("Rule Miner", "⛏️", 'open_rule_miner'),
            ("View Graph", "🎨", 'view_graph'),
            ("Clear Cache", "⚡", 'clear_cache'),
            ("Settings", "⚙️", 'open_settings'),
            ("Database", "🗄️", 'open_database')
        ]

        # Loop through items without any spacer checks
        for text, icon, callback_key in items:
            self._create_menu_button(text, icon, self.callbacks.get(callback_key), row)
            row += 1
    
    def _create_footer(self):
        """Create version info"""
        ctk.CTkLabel(
            self.frame,
            text="v2.0.0 | Phase 6 Complete",
            font=ctk.CTkFont(size=FONT_SIZES['mini']),
            text_color="gray"
        ).grid(row=99, column=0, padx=20, pady=(8, 16), sticky="s")
    
    def update_status(self, embedding_status=True, llm_status=True):
        """Update API status indicators"""
        self.embedding_indicator.configure(
            text_color=STATUS_COLORS['online'] if embedding_status else STATUS_COLORS['offline']
        )
        self.llm_indicator.configure(
            text_color=STATUS_COLORS['online'] if llm_status else STATUS_COLORS['offline']
        )
