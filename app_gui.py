"""
PyRAG - Modern Windows Desktop Application

This is now a lightweight entry point that imports the modular GUI components.
The actual implementation has been refactored into src/gui/ module.

Legacy app_gui.py has been restructured into:
- src/gui/main_window.py  : Main application window
- src/gui/sidebar.py      : Sidebar component  
- src/gui/chat.py         : Chat area component
- src/gui/dialogs.py      : Dialog windows (NewDocument, Settings)
- src/gui/constants.py    : Constants and configuration
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

# Import from modular structure
from src.gui import main

if __name__ == "__main__":
    main()
