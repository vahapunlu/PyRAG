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
import re
from datetime import datetime

from loguru import logger

from ..utils import get_settings, save_document_categories, load_app_settings
from ..ingestion import DocumentIngestion
from .constants import *


def extract_document_metadata(file_path: str) -> dict:
    """
    Automatically extract metadata from a PDF document.
    
    Extracts:
    - Standard number (IS, IEC, BS, EN, IEEE, ISO, ASTM, NFPA, etc.)
    - Publication date
    - Document description/title
    - Suggested category
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        Dict with standard_no, date, description, suggested_category
    """
    result = {
        "standard_no": "",
        "date": "",
        "description": "",
        "suggested_category": "Uncategorized"
    }
    
    try:
        path = Path(file_path)
        filename = path.stem  # Filename without extension
        
        # Try to extract from filename first (often most reliable)
        filename_metadata = _extract_from_filename(filename)
        result.update({k: v for k, v in filename_metadata.items() if v})
        
        # Then try PDF content/metadata
        if path.suffix.lower() == ".pdf":
            pdf_metadata = _extract_from_pdf(file_path)
            # Only fill in missing fields
            for key in ["standard_no", "date", "description"]:
                if not result[key] and pdf_metadata.get(key):
                    result[key] = pdf_metadata[key]
            if pdf_metadata.get("suggested_category"):
                result["suggested_category"] = pdf_metadata["suggested_category"]
        
        # Clean up and validate
        result = _validate_and_clean(result)
        
    except Exception as e:
        logger.warning(f"Metadata extraction failed for {file_path}: {e}")
    
    return result


def _extract_from_filename(filename: str) -> dict:
    """Extract metadata from filename patterns"""
    result = {"standard_no": "", "date": "", "description": "", "suggested_category": ""}
    
    # Common standard patterns
    # IS 10101, IEC 60364-5-52, BS 7671, EN 50174, IEEE 1584, ISO 9001, ASTM D1765, NFPA 70
    standard_patterns = [
        # Indian Standards: IS 10101, IS10101, IS-10101, IS_10101
        r'(IS[\s\-_]?\d{3,6}(?:[\-_:]\d+)*)',
        # IEC: IEC 60364, IEC60364, IEC 60364-5-52, IEC_60364_5_52
        r'(IEC[\s\-_]?\d{4,5}(?:[\s\-_:]\d+)*)',
        # BS: BS 7671, BS7671, BS_7671
        r'(BS[\s\-_]?\d{3,5}(?:[\-_:]\d+)*)',
        # EN: EN 50174, EN50174-1, EN_50174_1
        r'(EN[\s\-_]?\d{4,5}(?:[\s\-_:]\d+)*)',
        # IEEE: IEEE 1584, IEEE 802.3
        r'(IEEE[\s\-_]?\d{3,4}(?:\.\d+)?(?:[\-_:]\d+)*)',
        # ISO: ISO 9001, ISO/IEC 27001
        r'(ISO(?:/IEC)?[\s\-_]?\d{4,5}(?:[\-_:]\d+)*)',
        # ASTM: ASTM D1765, ASTM A36
        r'(ASTM[\s\-_]?[A-Z]?\d{2,5}(?:[\-_:]\d+)*)',
        # NFPA: NFPA 70, NFPA 72, NFPA_72, NFPA72
        r'(NFPA[\s\-_]?\d{2,4})',
        # NEC (National Electrical Code)
        r'(NEC[\s\-_]?\d{2,4})',
        # DIN: DIN EN 50173
        r'(DIN(?:[\s_]+EN)?[\s\-_]?\d{4,5}(?:[\-_:]\d+)*)',
    ]
    
    for pattern in standard_patterns:
        match = re.search(pattern, filename, re.IGNORECASE)
        if match:
            std = match.group(1).upper()
            # Normalize: replace underscores and multiple spaces/dashes with single space
            std = re.sub(r'[\s\-_]+', ' ', std).strip()
            # Don't add space between letters and numbers for part numbers
            # Add space only between standard prefix and first number
            std = re.sub(r'^([A-Z]+)\s*(\d)', r'\1 \2', std)
            # Replace multiple spaces with dash for part numbers (e.g., 60364 5 52 -> 60364-5-52)
            parts = std.split()
            if len(parts) > 2:
                # Keep prefix with main number, join parts with dash
                std = f"{parts[0]} {parts[1]}" + "".join(f"-{p}" for p in parts[2:])
            # Remove duplicate spaces
            std = re.sub(r'\s+', ' ', std).strip()
            
            # Check if standard ends with a year (e.g., IEC 60364-5-52-2009)
            # Move year to date field
            year_match = re.search(r'[-\s]((?:19[89]|20[0-2])\d)$', std)
            if year_match:
                result["date"] = year_match.group(1)
                std = std[:year_match.start()].strip()
            
            result["standard_no"] = std
            break
    
    # Extract year/date from filename (if not already found from standard)
    if not result["date"]:
        # Patterns: 2024, 2023-05, Mar2024, Edition 2024
        date_patterns = [
            r'Edition[\s_]*(20[0-2]\d)',            # Edition 2024
            r'(20[0-2]\d)[\-_]?(0[1-9]|1[0-2])?',  # 2024, 2024-05
            r'(19[89]\d)[\-_]?(0[1-9]|1[0-2])?',   # 1990s dates
            r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[\s_]*(20[0-2]\d)',  # Mar2024
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                if len(match.groups()) >= 2 and match.group(2):
                    # Has month
                    year = match.group(1) if match.group(1).isdigit() else match.group(2)
                    month = match.group(2) if match.group(1).isdigit() else ""
                    if month and month.isdigit():
                        result["date"] = f"{year}-{month}"
                    else:
                        result["date"] = year
                else:
                    result["date"] = match.group(1) if match.group(1).isdigit() else ""
                break
    
    # Date patterns for removal from description
    date_patterns_for_removal = [
        r'Edition[\s_]*(20[0-2]\d)',
        r'(20[0-2]\d)[\-_]?(0[1-9]|1[0-2])?',
        r'(19[89]\d)[\-_]?(0[1-9]|1[0-2])?',
    ]
    
    # Try to get description from filename (after removing standard and date)
    desc = filename
    # Remove standard number - try multiple variations
    if result["standard_no"]:
        # Create flexible pattern that matches the standard with various separators
        std_parts = result["standard_no"].split()
        if len(std_parts) >= 2:
            # Match prefix + number with flexible separators
            prefix = std_parts[0]
            number_part = '-'.join(std_parts[1:])
            # Pattern: IEC 60364-5-52 matches IEC_60364_5_52, IEC60364-5-52, etc.
            flex_pattern = prefix + r'[\s\-_]*' + number_part.replace('-', r'[\s\-_]*')
            desc = re.sub(flex_pattern, '', desc, flags=re.IGNORECASE)
        
        # Also try removing the original standard string
        std_pattern = re.escape(result["standard_no"])
        std_pattern = std_pattern.replace(r'\ ', r'[\s\-_]*')
        std_pattern = std_pattern.replace(r'\-', r'[\s\-_]*')
        desc = re.sub(std_pattern, '', desc, flags=re.IGNORECASE)
        
    # Remove date
    for pattern in date_patterns_for_removal:
        desc = re.sub(pattern, '', desc, flags=re.IGNORECASE)
    
    # Remove common standard prefixes that might remain
    desc = re.sub(r'\b(IS|IEC|BS|EN|IEEE|ISO|NFPA|NEC|ASTM|DIN)\d*\b', '', desc, flags=re.IGNORECASE)
    
    # Clean up
    desc = re.sub(r'[\-_]+', ' ', desc)
    desc = re.sub(r'\s+', ' ', desc).strip()
    # Remove leading/trailing punctuation
    desc = re.sub(r'^[\s\-_\.]+|[\s\-_\.]+$', '', desc)
    
    if len(desc) > 5:  # Only use if meaningful
        result["description"] = desc.title()
    
    # Suggest category based on standard type
    std_lower = result["standard_no"].lower() if result["standard_no"] else filename.lower()
    if any(x in std_lower for x in ['cable', 'wire', 'conductor']):
        result["suggested_category"] = "Cable & Wiring"
    elif any(x in std_lower for x in ['fire', 'smoke', 'alarm', 'nfpa']):
        result["suggested_category"] = "Fire Safety"
    elif any(x in std_lower for x in ['electric', 'power', 'iec 60', 'bs 767', 'nec']):
        result["suggested_category"] = "Electrical"
    elif any(x in std_lower for x in ['data', 'network', 'ethernet', 'lan', 'en 501']):
        result["suggested_category"] = "Data & Network"
    elif any(x in std_lower for x in ['safety', 'protection', 'hazard']):
        result["suggested_category"] = "Safety"
    elif any(x in std_lower for x in ['install', 'construct', 'build']):
        result["suggested_category"] = "Installation"
    
    return result


def _extract_from_pdf(file_path: str) -> dict:
    """Extract metadata from PDF content and properties"""
    result = {"standard_no": "", "date": "", "description": "", "suggested_category": ""}
    
    try:
        doc = pymupdf.open(file_path)
        
        # 1. Check PDF metadata
        metadata = doc.metadata
        if metadata:
            # Title often contains standard name
            title = metadata.get("title", "") or ""
            if title and len(title) > 3:
                result["description"] = title[:200]  # Limit length
            
            # Creation/modification date
            for date_key in ["creationDate", "modDate"]:
                date_val = metadata.get(date_key, "")
                if date_val:
                    # PDF date format: D:20240315... or just year
                    year_match = re.search(r'D?:?(20[0-2]\d)(0[1-9]|1[0-2])?', str(date_val))
                    if year_match:
                        year = year_match.group(1)
                        month = year_match.group(2) if year_match.group(2) else ""
                        result["date"] = f"{year}-{month}" if month else year
                        break
            
            # Subject sometimes has useful info
            subject = metadata.get("subject", "") or ""
            if subject and not result["description"]:
                result["description"] = subject[:200]
        
        # 2. Extract from first page content (usually has title/standard info)
        if doc.page_count > 0:
            first_page = doc[0]
            text = first_page.get_text("text")[:3000]  # First 3000 chars
            
            # Look for standard numbers in content
            standard_patterns = [
                r'\b(IS[\s\-]?\d{3,6}(?:[\-:]\d+)*)\b',
                r'\b(IEC[\s\-]?\d{4,5}(?:[\-:]\d+)*)\b',
                r'\b(BS[\s\-]?\d{3,5}(?:[\-:]\d+)*)\b',
                r'\b(EN[\s\-]?\d{4,5}(?:[\-:]\d+)*)\b',
                r'\b(IEEE[\s\-]?\d{3,4})\b',
                r'\b(ISO(?:/IEC)?[\s\-]?\d{4,5})\b',
                r'\b(NFPA[\s\-]?\d{2,4})\b',
            ]
            
            for pattern in standard_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    std = match.group(1).upper()
                    std = re.sub(r'\s+', ' ', std).strip()
                    result["standard_no"] = std
                    break
            
            # Look for title patterns
            title_patterns = [
                r'(?:^|\n)([A-Z][A-Za-z\s\-]+(?:Standard|Code|Specification|Guide|Requirements)[^\n]*)',
                r'(?:^|\n)((?:Low|High|Medium)[\s\-]?[Vv]oltage[^\n]{10,100})',
                r'(?:^|\n)((?:Cable|Wiring|Electrical|Fire)[^\n]{10,100})',
            ]
            
            if not result["description"]:
                for pattern in title_patterns:
                    match = re.search(pattern, text)
                    if match:
                        title = match.group(1).strip()
                        if 10 < len(title) < 200:
                            result["description"] = title
                            break
            
            # Category suggestion based on content
            text_lower = text.lower()
            if any(x in text_lower for x in ['fire alarm', 'fire detection', 'smoke']):
                result["suggested_category"] = "Fire Safety"
            elif any(x in text_lower for x in ['low voltage', 'electrical installation', 'wiring']):
                result["suggested_category"] = "Electrical"
            elif any(x in text_lower for x in ['cable', 'conductor', 'current carrying']):
                result["suggested_category"] = "Cable & Wiring"
            elif any(x in text_lower for x in ['data', 'network', 'ethernet', 'structured cabling']):
                result["suggested_category"] = "Data & Network"
        
        doc.close()
        
    except Exception as e:
        logger.debug(f"PDF extraction error: {e}")
    
    return result


def _validate_and_clean(metadata: dict) -> dict:
    """Validate and clean extracted metadata"""
    
    # Clean standard number
    if metadata.get("standard_no"):
        std = metadata["standard_no"]
        # Remove common artifacts
        std = re.sub(r'[,;.]+$', '', std)  # Trailing punctuation
        std = std.strip()
        # Validate format (should have letters and numbers)
        if re.match(r'^[A-Z]+[\s\-]?\d', std):
            metadata["standard_no"] = std
        else:
            metadata["standard_no"] = ""
    
    # Clean date
    if metadata.get("date"):
        date = metadata["date"]
        # Ensure valid year range
        year_match = re.search(r'(19[89]\d|20[0-2]\d)', date)
        if year_match:
            year = year_match.group(1)
            month_match = re.search(r'[\-/]?(0[1-9]|1[0-2])', date)
            if month_match:
                metadata["date"] = f"{year}-{month_match.group(1)}"
            else:
                metadata["date"] = year
        else:
            metadata["date"] = ""
    
    # Clean description
    if metadata.get("description"):
        desc = metadata["description"]
        # Remove excessive whitespace
        desc = re.sub(r'\s+', ' ', desc).strip()
        # Remove very short or meaningless descriptions
        if len(desc) < 5 or desc.lower() in ['untitled', 'document', 'pdf']:
            desc = ""
        # Limit length
        if len(desc) > 150:
            desc = desc[:147] + "..."
        metadata["description"] = desc
    
    return metadata


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
        
        # Re-scan metadata button
        ctk.CTkButton(
            toolbar,
            text="🔍 Re-scan Metadata",
            command=self.rescan_all_metadata,
            width=140,
            height=32,
            font=ctk.CTkFont(size=FONT_SIZES['small']),
            fg_color=COLORS['dark_bg'],
            border_width=1,
            text_color=COLORS['primary']
        ).pack(side="left", padx=10)
        
        self.stats_label = ctk.CTkLabel(
            toolbar,
            text="0 files (0.0 MB)",
            text_color="gray",
            font=ctk.CTkFont(size=FONT_SIZES['small'])
        )
        self.stats_label.pack(side="left", padx=15)
        
        # Auto-detection status
        self.auto_detect_label = ctk.CTkLabel(
            toolbar,
            text="",
            text_color=COLORS['success'],
            font=ctk.CTkFont(size=FONT_SIZES['tiny'])
        )
        self.auto_detect_label.pack(side="right", padx=10)
        
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
        """Add files to list with automatic metadata extraction"""
        files = filedialog.askopenfilenames(
            title="Select Documents",
            filetypes=SUPPORTED_FILE_TYPES
        )
        
        if files:
            current_paths = {item["path"] for item in self.selected_items}
            new_files_count = 0
            
            for f in files:
                if f not in current_paths:
                    # Extract metadata automatically
                    logger.info(f"🔍 Extracting metadata from: {Path(f).name}")
                    extracted = extract_document_metadata(f)
                    
                    self.selected_items.append({
                        "path": f,
                        "category": extracted.get("suggested_category", "Uncategorized"),
                        "project": "N/A",
                        "standard_no": extracted.get("standard_no", ""),
                        "date": extracted.get("date", ""),
                        "description": extracted.get("description", ""),
                    })
                    new_files_count += 1
                    
                    # Log extraction result
                    if extracted.get("standard_no"):
                        logger.success(f"   ✅ Standard: {extracted['standard_no']}")
                    if extracted.get("date"):
                        logger.info(f"   📅 Date: {extracted['date']}")
                    if extracted.get("description"):
                        logger.info(f"   📝 Description: {extracted['description'][:50]}...")
            
            if new_files_count > 0:
                logger.success(f"✅ Added {new_files_count} files with auto-extracted metadata")
                self._update_auto_detect_status()
            
            self.refresh_file_list()
    
    def remove_file(self, file_path):
        """Remove file from list"""
        self.selected_items = [item for item in self.selected_items if item["path"] != file_path]
        self.refresh_file_list()
        self._update_auto_detect_status()
    
    def rescan_all_metadata(self):
        """Re-scan metadata for all files"""
        if not self.selected_items:
            return
        
        logger.info("🔍 Re-scanning metadata for all files...")
        detected_count = 0
        
        for item in self.selected_items:
            extracted = extract_document_metadata(item["path"])
            
            # Update with extracted values
            if extracted.get("standard_no"):
                item["standard_no"] = extracted["standard_no"]
                detected_count += 1
            if extracted.get("date"):
                item["date"] = extracted["date"]
            if extracted.get("description"):
                item["description"] = extracted["description"]
            if extracted.get("suggested_category") and extracted["suggested_category"] != "Uncategorized":
                item["category"] = extracted["suggested_category"]
        
        logger.success(f"✅ Re-scanned {len(self.selected_items)} files, detected metadata for {detected_count}")
        self._update_auto_detect_status()
        self.refresh_file_list()
    
    def rescan_single_file(self, file_path: str, item_index: int):
        """Re-scan metadata for a single file"""
        extracted = extract_document_metadata(file_path)
        
        # Update the item
        if 0 <= item_index < len(self.selected_items):
            item = self.selected_items[item_index]
            if extracted.get("standard_no"):
                item["standard_no"] = extracted["standard_no"]
            if extracted.get("date"):
                item["date"] = extracted["date"]
            if extracted.get("description"):
                item["description"] = extracted["description"]
            if extracted.get("suggested_category") and extracted["suggested_category"] != "Uncategorized":
                item["category"] = extracted["suggested_category"]
        
        self._update_auto_detect_status()
        self.refresh_file_list()
    
    def _update_auto_detect_status(self):
        """Update the auto-detection status label"""
        if not self.selected_items:
            self.auto_detect_label.configure(text="")
            return
        
        detected_count = sum(1 for item in self.selected_items if item.get("standard_no"))
        total = len(self.selected_items)
        
        if detected_count == total:
            self.auto_detect_label.configure(
                text=f"✅ All {total} documents auto-detected",
                text_color=COLORS['success']
            )
        elif detected_count > 0:
            self.auto_detect_label.configure(
                text=f"🔍 {detected_count}/{total} standards auto-detected",
                text_color=COLORS['warning']
            )
        else:
            self.auto_detect_label.configure(
                text=f"⚠️ No standards detected - please fill manually",
                text_color="gray"
            )
    
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
                
                # Re-scan button for this file
                def make_rescan_cb(fp, idx):
                    def _rescan():
                        self.rescan_single_file(fp, idx)
                    return _rescan
                
                rescan_btn = ctk.CTkButton(
                    row1,
                    text="🔍",
                    width=28,
                    height=28,
                    font=ctk.CTkFont(size=12),
                    fg_color=COLORS['darker_bg'],
                    hover_color=COLORS['hover'],
                    command=make_rescan_cb(file_path, i)
                )
                rescan_btn.pack(side="right", padx=2)
                
                # === ROW 1.5: Metadata fields (Standard No, Date, Description) ===
                metadata_row = ctk.CTkFrame(container, fg_color="transparent")
                metadata_row.pack(fill="x", padx=5, pady=(5, 2))
                
                # Auto-detect indicator
                has_auto_data = bool(item.get("standard_no"))
                auto_indicator = "✨" if has_auto_data else "📝"
                auto_color = COLORS['success'] if has_auto_data else "gray"
                
                ctk.CTkLabel(
                    metadata_row, 
                    text=auto_indicator,
                    font=ctk.CTkFont(size=12),
                    text_color=auto_color,
                    width=20
                ).pack(side="left", padx=(5, 0))
                
                # Standard No
                ctk.CTkLabel(metadata_row, text="Standard:", 
                           font=ctk.CTkFont(size=FONT_SIZES['tiny']),
                           text_color="gray", width=60, anchor="e").pack(side="left", padx=(5, 3))
                
                standard_no_var = ctk.StringVar(value=item.get("standard_no", ""))
                
                def make_standard_cb(idx, var):
                    def _update(*_):
                        self.selected_items[idx]["standard_no"] = var.get()
                    return _update
                
                # Create standard entry - highlight if auto-detected
                standard_entry_kwargs = {
                    "master": metadata_row,
                    "textvariable": standard_no_var,
                    "width": 140,
                    "height": 26,
                    "font": ctk.CTkFont(size=FONT_SIZES['tiny']),
                    "placeholder_text": "e.g., IEC 60364-5-52"
                }
                if item.get("standard_no"):
                    standard_entry_kwargs["border_color"] = COLORS['success']
                
                standard_entry = ctk.CTkEntry(**standard_entry_kwargs)
                standard_entry.pack(side="left", padx=3)
                standard_no_var.trace_add("write", make_standard_cb(i, standard_no_var))
                
                # Date
                ctk.CTkLabel(metadata_row, text="Date:", 
                           font=ctk.CTkFont(size=FONT_SIZES['tiny']),
                           text_color="gray", width=35, anchor="e").pack(side="left", padx=(8, 3))
                
                date_var = ctk.StringVar(value=item.get("date", ""))
                
                def make_date_cb(idx, var):
                    def _update(*_):
                        self.selected_items[idx]["date"] = var.get()
                    return _update
                
                # Create date entry - highlight if auto-detected
                date_entry_kwargs = {
                    "master": metadata_row,
                    "textvariable": date_var,
                    "width": 90,
                    "height": 26,
                    "font": ctk.CTkFont(size=FONT_SIZES['tiny']),
                    "placeholder_text": "e.g., 2024"
                }
                if item.get("date"):
                    date_entry_kwargs["border_color"] = COLORS['success']
                
                date_entry = ctk.CTkEntry(**date_entry_kwargs)
                date_entry.pack(side="left", padx=3)
                date_var.trace_add("write", make_date_cb(i, date_var))
                
                # Description
                ctk.CTkLabel(metadata_row, text="Description:", 
                           font=ctk.CTkFont(size=FONT_SIZES['tiny']),
                           text_color="gray", width=70, anchor="e").pack(side="left", padx=(8, 3))
                
                desc_var = ctk.StringVar(value=item.get("description", ""))
                
                def make_desc_cb(idx, var):
                    def _update(*_):
                        self.selected_items[idx]["description"] = var.get()
                    return _update
                
                # Create description entry - highlight if auto-detected
                desc_entry_kwargs = {
                    "master": metadata_row,
                    "textvariable": desc_var,
                    "width": 220,
                    "height": 26,
                    "font": ctk.CTkFont(size=FONT_SIZES['tiny']),
                    "placeholder_text": "Brief description"
                }
                if item.get("description"):
                    desc_entry_kwargs["border_color"] = COLORS['success']
                
                desc_entry = ctk.CTkEntry(**desc_entry_kwargs)
                desc_entry.pack(side="left", padx=3, fill="x", expand=True)
                desc_var.trace_add("write", make_desc_cb(i, desc_var))
                
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
                
                # Info label (for chunk count and progress percentage)
                info_label = ctk.CTkLabel(
                    row2,
                    text="",
                    font=ctk.CTkFont(size=FONT_SIZES['tiny'], weight="bold"),
                    text_color="#00aaff",
                    width=100
                )
                info_label.pack(side="right", padx=(5, 5))
                item["info_widget"] = info_label
                
                # Progress bar (hidden initially, larger size)
                progress_bar = ctk.CTkProgressBar(row2, width=180, height=12, mode="indeterminate")
                progress_bar.pack(side="right", padx=(10, 5))
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
    
    def update_status(self, file_path, status, info_text="", progress_percent=None):
        """Update file status indicator"""
        for item in self.selected_items:
            if item["path"] == file_path:
                # Update info label (chunk count, progress percent, etc.)
                if "info_widget" in item:
                    if progress_percent is not None:
                        # Show percentage during indexing
                        item["info_widget"].configure(text=f"{progress_percent}%")
                    elif info_text:
                        item["info_widget"].configure(text=info_text)
                
                # Update progress bar
                if "progress_widget" in item:
                    if status in ["copying", "indexing"]:
                        if progress_percent is not None:
                            # Switch to determinate mode
                            item["progress_widget"].configure(mode="determinate")
                            item["progress_widget"].set(progress_percent / 100.0)
                        else:
                            # Indeterminate mode
                            item["progress_widget"].configure(mode="indeterminate")
                            item["progress_widget"].start()
                        
                        if not item["progress_widget"].winfo_ismapped():
                            item["progress_widget"].pack(side="right", padx=(5, 5))
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
                    "project": item.get("project", "N/A"),
                    "standard_no": item.get("standard_no", ""),
                    "date": item.get("date", ""),
                    "description": item.get("description", "")
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
            # Try to reuse existing client from query engine to avoid lock issues
            existing_client = None
            if hasattr(self.parent, 'query_engine') and self.parent.query_engine:
                if hasattr(self.parent.query_engine, 'client'):
                    existing_client = self.parent.query_engine.client
                    logger.info("Using existing Qdrant client from QueryEngine")
            
            ingestion = DocumentIngestion(client=existing_client)
            
            for idx, item in enumerate(self.selected_items, 1):
                if "copied_path" not in item:
                    continue
                
                file_path = item["path"]
                file_name = item["file_name"]
                
                try:
                    self.after(0, self.update_status, file_path, "indexing", "parsing...")
                    self.after(0, update_button, f"Indexing {idx}/{total_files}: {file_name}")
                    
                    # Progress callback to update UI
                    def make_progress_callback(fp):
                        def callback(stage, percent):
                            stage_labels = {
                                'parsing': '📖 Parsing',
                                'chunking': '✂️ Chunking',
                                'indexing': '🔍 Indexing',
                                'syncing': '🔄 Syncing',
                                'complete': '✅ Complete'
                            }
                            stage_text = stage_labels.get(stage, stage)
                            self.after(0, self.update_status, fp, "indexing", stage_text, percent)
                        return callback
                    
                    # Use ingest_single_file method with progress callback
                    result = ingestion.ingest_single_file(
                        file_path=item["copied_path"],
                        category=item.get("category", "Uncategorized"),
                        project=item.get("project", "N/A"),
                        standard_no=item.get("standard_no", ""),
                        date=item.get("date", ""),
                        description=item.get("description", ""),
                        progress_callback=make_progress_callback(file_path)
                    )
                    
                    if result["success"]:
                        # Show leaf chunks (actual indexed count)
                        leaf_count = result.get('leaf_chunks', result['chunks'])
                        chunk_info = f"{leaf_count} chunks"
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
            import traceback
            error_trace = traceback.format_exc()
            logger.error(f"Indexing failed: {e}\n{error_trace}")
            self.after(0, lambda: messagebox.showerror("Error", f"Indexing failed:\n{str(e)}\n\nCheck logs for details."))
    
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
