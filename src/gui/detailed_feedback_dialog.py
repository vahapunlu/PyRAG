"""
Detailed Feedback Dialog for PyRAG GUI

Allows users to provide granular feedback on sources and responses.
"""

import tkinter as tk
import customtkinter as ctk
from loguru import logger
from typing import List, Dict, Optional, Callable


class DetailedFeedbackDialog(ctk.CTkToplevel):
    """Dialog for collecting detailed feedback on responses"""
    
    def __init__(self, parent, query: str, response: str, sources: List[Dict], 
                 on_submit: Callable):
        """
        Initialize detailed feedback dialog
        
        Args:
            parent: Parent window
            query: User query
            response: AI response
            sources: List of source documents
            on_submit: Callback function(feedback_data)
        """
        super().__init__(parent)
        
        self.query = query
        self.response = response
        self.sources = sources or []
        self.on_submit = on_submit
        
        # Feedback data storage
        self.feedback_data = {
            'overall_rating': 0,
            'dimensions': {
                'relevance': 0,
                'clarity': 0,
                'completeness': 0
            },
            'source_feedbacks': [],
            'comment': ''
        }
        
        # Setup dialog
        self.title("📊 Detailed Feedback")
        self.geometry("800x700")
        self.resizable(False, False)
        
        # Center on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (800 // 2)
        y = (self.winfo_screenheight() // 2) - (700 // 2)
        self.geometry(f"800x700+{x}+{y}")
        
        self._create_widgets()
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        self.focus()
    
    def _create_widgets(self):
        """Create dialog widgets"""
        # Main container with scrollbar
        main_container = ctk.CTkFrame(self)
        main_container.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Scrollable frame
        self.scroll_frame = ctk.CTkScrollableFrame(
            main_container,
            width=760,
            height=640
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        header = ctk.CTkLabel(
            self.scroll_frame,
            text="📊 Detailed Feedback",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        header.pack(pady=(0, 20))
        
        # Overall rating
        self._create_overall_rating()
        
        # Multi-dimensional ratings
        self._create_dimension_ratings()
        
        # Source-level feedback
        if self.sources:
            self._create_source_feedback()
        
        # Overall comment
        self._create_comment_section()
        
        # Buttons
        self._create_buttons()
    
    def _create_overall_rating(self):
        """Create overall rating section"""
        section = ctk.CTkFrame(self.scroll_frame)
        section.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            section,
            text="Overall Rating",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(10, 5))
        
        ctk.CTkLabel(
            section,
            text="How would you rate this response overall?",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack()
        
        # Star buttons
        stars_frame = ctk.CTkFrame(section, fg_color="transparent")
        stars_frame.pack(pady=15)
        
        self.star_buttons = []
        for i in range(1, 6):
            btn = ctk.CTkButton(
                stars_frame,
                text="★",
                width=50,
                height=50,
                font=ctk.CTkFont(size=24),
                fg_color="gray30",
                hover_color="gray20",
                command=lambda rating=i: self._set_overall_rating(rating)
            )
            btn.pack(side="left", padx=5)
            self.star_buttons.append(btn)
        
        # Rating text
        self.rating_label = ctk.CTkLabel(
            section,
            text="",
            font=ctk.CTkFont(size=12)
        )
        self.rating_label.pack(pady=5)
    
    def _set_overall_rating(self, rating: int):
        """Set overall rating and update UI"""
        self.feedback_data['overall_rating'] = rating
        
        # Update button colors
        for i, btn in enumerate(self.star_buttons, 1):
            if i <= rating:
                btn.configure(fg_color="#ffc107", text_color="white")
            else:
                btn.configure(fg_color="gray30", text_color="gray70")
        
        # Update text
        labels = ["Very Poor", "Poor", "Average", "Good", "Excellent"]
        self.rating_label.configure(text=labels[rating - 1])
    
    def _create_dimension_ratings(self):
        """Create multi-dimensional ratings"""
        section = ctk.CTkFrame(self.scroll_frame)
        section.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            section,
            text="Detailed Evaluation",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(10, 15))
        
        dimensions = [
            ('relevance', '📌 Relevance', 'How relevant is the answer to your question?'),
            ('clarity', '💡 Clarity', 'How clear and understandable is the answer?'),
            ('completeness', '✅ Completeness', 'How complete and comprehensive is the answer?')
        ]
        
        self.dimension_sliders = {}
        
        for dim_key, dim_title, dim_desc in dimensions:
            dim_frame = ctk.CTkFrame(section, fg_color="transparent")
            dim_frame.pack(fill="x", padx=20, pady=10)
            
            ctk.CTkLabel(
                dim_frame,
                text=dim_title,
                font=ctk.CTkFont(size=13, weight="bold")
            ).pack(anchor="w")
            
            ctk.CTkLabel(
                dim_frame,
                text=dim_desc,
                font=ctk.CTkFont(size=11),
                text_color="gray"
            ).pack(anchor="w", pady=(0, 5))
            
            slider = ctk.CTkSlider(
                dim_frame,
                from_=0,
                to=5,
                number_of_steps=5,
                command=lambda val, key=dim_key: self._update_dimension(key, val)
            )
            slider.set(0)
            slider.pack(fill="x", pady=5)
            
            self.dimension_sliders[dim_key] = slider
    
    def _update_dimension(self, dimension: str, value: float):
        """Update dimension rating"""
        self.feedback_data['dimensions'][dimension] = int(value)
    
    def _create_source_feedback(self):
        """Create source-level feedback section"""
        section = ctk.CTkFrame(self.scroll_frame)
        section.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            section,
            text="📚 Rate Each Source",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(10, 15))
        
        self.source_feedback_widgets = []
        
        for i, source in enumerate(self.sources[:5]):  # Limit to 5 sources
            self._create_source_card(section, source, i)
    
    def _create_source_card(self, parent, source: Dict, index: int):
        """Create a feedback card for a source"""
        card = ctk.CTkFrame(parent)
        card.pack(fill="x", padx=20, pady=8)
        
        # Source info
        doc_name = source.get('document', source.get('metadata', {}).get('document_name', 'Unknown'))
        page = source.get('page', source.get('metadata', {}).get('page', 'N/A'))
        
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(
            info_frame,
            text=f"📄 {doc_name} - Page {page}",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w")
        
        # Preview text (if available)
        preview_text = source.get('text', '')[:100]
        if preview_text:
            ctk.CTkLabel(
                info_frame,
                text=f"» {preview_text}...",
                font=ctk.CTkFont(size=10),
                text_color="gray",
                wraplength=650
            ).pack(anchor="w", pady=(5, 10))
        
        # Rating buttons
        rating_frame = ctk.CTkFrame(card, fg_color="transparent")
        rating_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        rating_var = tk.StringVar(value="")
        stars_var = tk.IntVar(value=0)
        
        # Rating buttons
        btn_frame = ctk.CTkFrame(rating_frame, fg_color="transparent")
        btn_frame.pack(side="left")
        
        helpful_btn = ctk.CTkButton(
            btn_frame,
            text="👍 Helpful",
            width=100,
            height=30,
            font=ctk.CTkFont(size=11),
            fg_color="gray30",
            command=lambda: self._set_source_rating(index, "helpful", rating_var, 
                                                    [helpful_btn, not_helpful_btn, irrelevant_btn])
        )
        helpful_btn.pack(side="left", padx=3)
        
        not_helpful_btn = ctk.CTkButton(
            btn_frame,
            text="👎 Not Helpful",
            width=110,
            height=30,
            font=ctk.CTkFont(size=11),
            fg_color="gray30",
            command=lambda: self._set_source_rating(index, "not_helpful", rating_var,
                                                    [helpful_btn, not_helpful_btn, irrelevant_btn])
        )
        not_helpful_btn.pack(side="left", padx=3)
        
        irrelevant_btn = ctk.CTkButton(
            btn_frame,
            text="❌ Irrelevant",
            width=100,
            height=30,
            font=ctk.CTkFont(size=11),
            fg_color="gray30",
            command=lambda: self._set_source_rating(index, "irrelevant", rating_var,
                                                    [helpful_btn, not_helpful_btn, irrelevant_btn])
        )
        irrelevant_btn.pack(side="left", padx=3)
        
        # Star rating
        stars_label = ctk.CTkLabel(
            rating_frame,
            text="Stars:",
            font=ctk.CTkFont(size=11)
        )
        stars_label.pack(side="left", padx=(20, 5))
        
        star_btns = []
        for i in range(1, 6):
            star_btn = ctk.CTkButton(
                rating_frame,
                text="★",
                width=30,
                height=30,
                font=ctk.CTkFont(size=16),
                fg_color="gray30",
                command=lambda r=i, idx=index, sv=stars_var: self._set_source_stars(idx, r, sv, star_btns)
            )
            star_btn.pack(side="left", padx=2)
            star_btns.append(star_btn)
        
        # Store widgets for this source
        self.source_feedback_widgets.append({
            'source': source,
            'rating_var': rating_var,
            'stars_var': stars_var,
            'rating_buttons': [helpful_btn, not_helpful_btn, irrelevant_btn],
            'star_buttons': star_btns
        })
    
    def _set_source_rating(self, index: int, rating: str, rating_var: tk.StringVar, buttons: list):
        """Set source rating"""
        rating_var.set(rating)
        
        # Update button colors
        colors = {
            'helpful': '#28a745',
            'not_helpful': '#ffc107',
            'irrelevant': '#dc3545'
        }
        
        for i, btn in enumerate(buttons):
            btn_ratings = ['helpful', 'not_helpful', 'irrelevant']
            if btn_ratings[i] == rating:
                btn.configure(fg_color=colors[rating])
            else:
                btn.configure(fg_color="gray30")
    
    def _set_source_stars(self, index: int, rating: int, stars_var: tk.IntVar, star_buttons: list):
        """Set source star rating"""
        stars_var.set(rating)
        
        for i, btn in enumerate(star_buttons, 1):
            if i <= rating:
                btn.configure(fg_color="#ffc107")
            else:
                btn.configure(fg_color="gray30")
    
    def _create_comment_section(self):
        """Create overall comment section"""
        section = ctk.CTkFrame(self.scroll_frame)
        section.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            section,
            text="💬 Additional Comments (Optional)",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(10, 10))
        
        self.comment_textbox = ctk.CTkTextbox(
            section,
            height=100,
            font=ctk.CTkFont(size=12)
        )
        self.comment_textbox.pack(fill="x", padx=20, pady=10)
    
    def _create_buttons(self):
        """Create action buttons"""
        button_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=20)
        
        ctk.CTkButton(
            button_frame,
            text="Cancel",
            width=120,
            height=40,
            font=ctk.CTkFont(size=13),
            fg_color="gray30",
            hover_color="gray20",
            command=self.destroy
        ).pack(side="left", padx=(20, 10))
        
        ctk.CTkButton(
            button_frame,
            text="Submit Feedback",
            width=150,
            height=40,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#28a745",
            hover_color="#218838",
            command=self._submit
        ).pack(side="right", padx=(10, 20))
    
    def _submit(self):
        """Collect and submit feedback"""
        # Validate
        if self.feedback_data['overall_rating'] == 0:
            import tkinter.messagebox as messagebox
            messagebox.showwarning(
                "Missing Rating",
                "Please provide an overall rating before submitting.",
                parent=self
            )
            return
        
        # Collect source feedbacks
        source_feedbacks = []
        for widget_data in self.source_feedback_widgets:
            rating = widget_data['rating_var'].get()
            stars = widget_data['stars_var'].get()
            
            if rating:  # Only include if rated
                source = widget_data['source']
                source_feedbacks.append({
                    'document': source.get('document', source.get('metadata', {}).get('document_name', 'Unknown')),
                    'page': str(source.get('page', source.get('metadata', {}).get('page', 'N/A'))),
                    'text': source.get('text', '')[:500],
                    'rating': rating,
                    'stars': stars if stars > 0 else 3
                })
        
        self.feedback_data['source_feedbacks'] = source_feedbacks
        
        # Get comment
        self.feedback_data['comment'] = self.comment_textbox.get("1.0", "end-1c").strip()
        
        # Call submit callback
        try:
            self.on_submit(self.feedback_data)
            logger.info(f"✅ Detailed feedback submitted: {len(source_feedbacks)} sources rated")
            self.destroy()
        except Exception as e:
            logger.error(f"❌ Failed to submit feedback: {e}")
            import tkinter.messagebox as messagebox
            messagebox.showerror(
                "Submission Error",
                f"Failed to submit feedback: {str(e)}",
                parent=self
            )
