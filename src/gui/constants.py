"""
GUI Constants and Configuration

Contains all constants, colors, sizes, and configuration values used across the GUI.
"""

# Golden Ratio
PHI = 1.618

# Theme Configuration
APPEARANCE_MODE = "dark"
COLOR_THEME = "blue"

# Colors
COLORS = {
    'primary': '#1f6aa5',
    'primary_hover': '#164e7e',
    'success': '#2ecc71',
    'success_hover': '#27ae60',
    'danger': '#e74c3c',
    'danger_hover': '#c0392b',
    'warning': '#f39c12',
    'info': '#3498db',
    'gray': '#cccccc',
    'dark_bg': '#2b2b2b',
    'darker_bg': '#333333',
    'success_tint': '#1a4d2e',
    'error_tint': '#4d1a1a',
}

# Font Sizes (based on golden ratio)
FONT_SIZES = {
    'title': 32,
    'subtitle': 20,
    'header': 18,
    'large': 16,
    'medium': 14,
    'normal': 13,
    'small': 12,
    'tiny': 11,
    'mini': 10,
}

# Button Heights (based on golden ratio)
BUTTON_HEIGHTS = {
    'primary': int(40 * PHI),      # ~65px
    'secondary': 40,                # 40px
    'tertiary': int(40 / PHI),     # ~25px
    'small': 32,
    'tiny': 24,
}

# Spacing (based on golden ratio)
SPACING = {
    'major': int(20 * PHI),        # ~32px
    'minor': int(20 / PHI),        # ~12px
    'standard': 20,
    'small': 10,
    'tiny': 5,
}

# Window Sizes
WINDOW_SIZES = {
    'main_min_width': 1000,
    'main_min_height': 700,
    'dialog_width': 700,
    'dialog_height': 550,
    'large_dialog_width': 1100,
    'large_dialog_height': 700,
}

# Sidebar Configuration
SIDEBAR_WIDTH = int(250 * PHI / 1.5)

# Status Indicators
STATUS_ICONS = {
    'waiting': '⏳',
    'copying': '📋',
    'indexing': '⚡',
    'success': '✅',
    'error': '❌',
    'online': '●',
}

STATUS_COLORS = {
    'online': '#00ff00',
    'offline': '#ff0000',
    'warning': 'orange',
    'processing': 'yellow',
    'success': 'green',
    'error': 'red',
}

# File Types
SUPPORTED_FILE_TYPES = [
    ("Supported files", "*.pdf;*.txt;*.md"),
    ("PDF files", "*.pdf"),
    ("Text files", "*.txt"),
    ("Markdown files", "*.md"),
    ("All files", "*.*")
]

# Default Categories
DEFAULT_CATEGORIES = [
    "Standard",
    "Employee Requirements",
    "Internal Document",
    "Government",
    "Technical Guidance",
    "Uncategorized"
]

# Default Projects
DEFAULT_PROJECTS = ["N/A"]

# Messages
MESSAGES = {
    'welcome': """
════════════════════════════════════════════════════
  Welcome to PyRAG - Engineering Standards AI
════════════════════════════════════════════════════

🚀 Getting Started:
   1. Add documents using the "New Document" button
   2. Ask questions about your engineering standards
   3. Get instant, accurate answers with source references

💡 Tips:
   • Use specific questions for better results
   • Filter by category or document for focused searches
   • View statistics to see your document library

Ready to help! Ask me anything about your standards.
""",
    'no_files': 'No files selected',
    'no_files_subtitle': 'Click \'Add Files\' to get started',
}
