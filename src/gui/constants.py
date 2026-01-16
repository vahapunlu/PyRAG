"""
GUI Constants and Configuration

Contains all constants, colors, sizes, and configuration values used across the GUI.
"""

# Golden Ratio
PHI = 1.618

# Theme Configuration
APPEARANCE_MODE = "dark"
COLOR_THEME = "blue"

# Colors (Ultra-Modern Docker Dark Theme)
COLORS = {
    'primary': '#0090FF',           # Docker Desktop Bright Blue
    'primary_hover': '#0078C8',     # Darker Blue
    'success': '#2EA043',           # Docker Green
    'success_hover': '#238636',
    'danger': '#F85149',            # Error Red
    'danger_hover': '#DA3633',
    'warning': '#D29922',           # Warning Yellow
    'info': '#58A6FF',              # Info Blue
    'gray': '#8B949E',              # Subtext Gray
    'dark_bg': '#191919',           # Main Background (Docker Dark Grey)
    'darker_bg': '#000000',         # Sidebar Background (Pure Black)
    'hover': '#2D333B',             # Hover State
    'success_tint': '#1A4D2E',
    'error_tint': '#4D1A1A',
    'border': '#30363D',            # Separator Borders
    'input_bg': '#252526',          # Input Field Background
}

# Font Sizes (Optimized for readability)
FONT_SIZES = {
    'title': 28,
    'subtitle': 18,
    'header': 16,
    'large': 15,
    'medium': 14,
    'normal': 14,
    'small': 13,
    'tiny': 12,
    'mini': 11,
}

# Button Heights (optimized for compact layout)
BUTTON_HEIGHTS = {
    'primary': 40,                  # Primary action button
    'secondary': 34,                # Secondary buttons
    'tertiary': 32,                 # Tertiary buttons
    'small': 28,
    'tiny': 24,
}

# Spacing (optimized for visual balance)
SPACING = {
    'major': 20,                    # Major section spacing
    'minor': 8,                     # Minor spacing between buttons
    'section': 16,                  # Section header spacing
    'standard': 12,
    'small': 6,
    'tiny': 4,
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
  ⚡ PyRAG - Engineering Standards AI
════════════════════════════════════════════════════

🚀 Getting Started:
   1. Add documents using "New Document" button (Ctrl+N)
   2. Ask questions about your engineering standards
   3. Get instant, accurate answers with source references

💡 Pro Tips:
   • Use Templates dropdown for common question formats
   • Filter by category/document for focused searches
   • Click follow-up suggestions for deeper exploration
   • Copy or Export answers with quick action buttons

⌨️ Keyboard Shortcuts:
   Ctrl+Enter → Send  |  Ctrl+H → History  |  F1 → Help

🌐 Language: Ask in Turkish or English - I'll respond in the same language!

Ready to help! Ask me anything about your standards.
""",
    'no_files': 'No files selected',
    'no_files_subtitle': 'Click \'Add Files\' to get started',
}
