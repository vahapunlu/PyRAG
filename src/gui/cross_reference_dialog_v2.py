"""
Cross-Reference Analysis Dialog V2 - Compliance & Gap Analysis

Modern GUI for engineering document compliance checking.
"""

import customtkinter as ctk
from typing import Optional, Dict, List
from threading import Thread
from tkinter import messagebox
import logging

from ..cross_reference_v2 import (
    CrossReferenceEngineV2,
    AnalysisMode,
    IssueSeverity,
    ComplianceReport,
    ComplianceIssue,
    GapItem,
    ValueComparison
)

logger = logging.getLogger(__name__)

# Colors
COLORS = {
    'critical': '#dc3545',
    'high': '#fd7e14',
    'medium': '#ffc107',
    'low': '#28a745',
    'info': '#17a2b8',
    'dark_bg': '#2b2b2b',
    'card_bg': '#363636',
    'text': '#ffffff',
    'text_muted': '#aaaaaa'
}


class CrossReferenceDialogV2(ctk.CTkToplevel):
    """
    Modern Cross-Reference Dialog for Compliance Analysis
    
    Use Case:
    - Compare your specification against standards/requirements
    - Find non-compliant values and missing requirements
    """
    
    def __init__(self, parent, query_engine, available_documents: List[str]):
        super().__init__(parent)
        
        self.query_engine = query_engine
        self.available_documents = sorted(available_documents)
        self.engine = CrossReferenceEngineV2(query_engine)
        
        # Window settings
        self.title("📋 Compliance & Gap Analysis")
        self.geometry("900x800")
        self.minsize(800, 750)
        
        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - 450
        y = (self.winfo_screenheight() // 2) - 400
        self.geometry(f"900x800+{x}+{y}")
        
        # Modal
        self.transient(parent)
        self.grab_set()
        
        # State
        self.analysis_mode = ctk.StringVar(value="full")
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create all widgets"""
        
        # Main container with padding
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=25, pady=20)
        
        # Scrollable content area
        scroll_frame = ctk.CTkScrollableFrame(main, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True)
        
        # Header
        self._create_header(scroll_frame)
        
        # Document Selection Section
        self._create_document_section(scroll_frame)
        
        # Analysis Mode Section
        self._create_mode_section(scroll_frame)
        
        # Focus Area Section  
        self._create_focus_section(scroll_frame)
        
        # Action Buttons - at bottom, always visible
        self._create_buttons(main)
    
    def _create_header(self, parent):
        """Create header with title and description"""
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        
        title = ctk.CTkLabel(
            header,
            text="📋 Compliance & Gap Analysis",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(anchor="w")
        
        desc = ctk.CTkLabel(
            header,
            text="Compare your specification against standards, government requirements, or employer specs.\n"
                 "Find non-compliant values, missing requirements, and coverage gaps.",
            font=ctk.CTkFont(size=12),
            text_color=COLORS['text_muted'],
            justify="left"
        )
        desc.pack(anchor="w", pady=(5, 0))
    
    def _create_document_section(self, parent):
        """Create document selection section"""
        doc_frame = ctk.CTkFrame(parent)
        doc_frame.pack(fill="x", pady=(0, 15))
        
        # Your Specification (Source) - THE DOCUMENT TO CHECK
        source_frame = ctk.CTkFrame(doc_frame, fg_color="transparent")
        source_frame.pack(fill="x", padx=15, pady=(15, 10))
        
        source_label = ctk.CTkLabel(
            source_frame,
            text="📄 YOUR SPEC (Document to Check):",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#4CAF50"  # Green to highlight
        )
        source_label.pack(anchor="w")
        
        source_hint = ctk.CTkLabel(
            source_frame,
            text="⬇️ Select YOUR company's specification document (e.g., EDC, your tender spec)",
            font=ctk.CTkFont(size=11),
            text_color=COLORS['text_muted']
        )
        source_hint.pack(anchor="w")
        
        self.source_var = ctk.StringVar(value="Select YOUR specification...")
        self.source_dropdown = ctk.CTkOptionMenu(
            source_frame,
            variable=self.source_var,
            values=self.available_documents,
            command=self._on_source_changed,
            width=400,
            fg_color=COLORS['card_bg']
        )
        self.source_dropdown.pack(anchor="w", pady=(8, 0))
        
        # Reference Documents - STANDARDS/REQUIREMENTS TO COMPARE AGAINST
        ref_frame = ctk.CTkFrame(doc_frame, fg_color="transparent")
        ref_frame.pack(fill="x", padx=15, pady=(10, 15))
        
        ref_label = ctk.CTkLabel(
            ref_frame,
            text="📚 Reference Documents (to compare against):",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        ref_label.pack(anchor="w")
        
        ref_hint = ctk.CTkLabel(
            ref_frame,
            text="Select standards, LDA, employer requirements to check compliance against",
            font=ctk.CTkFont(size=11),
            text_color=COLORS['text_muted']
        )
        ref_hint.pack(anchor="w")
        
        # Scrollable checkboxes for references
        self.ref_scroll = ctk.CTkScrollableFrame(ref_frame, height=120)
        self.ref_scroll.pack(fill="x", pady=(8, 0))
        
        self.ref_vars: Dict[str, ctk.BooleanVar] = {}
        self.ref_checkboxes: Dict[str, ctk.CTkCheckBox] = {}
        
        for doc in self.available_documents:
            var = ctk.BooleanVar(value=False)
            cb = ctk.CTkCheckBox(
                self.ref_scroll,
                text=doc,
                variable=var,
                command=self._update_status
            )
            cb.pack(anchor="w", pady=2)
            self.ref_vars[doc] = var
            self.ref_checkboxes[doc] = cb
        
        # Selection status
        self.status_label = ctk.CTkLabel(
            doc_frame,
            text="⚠️ Select your spec and at least 1 reference document",
            font=ctk.CTkFont(size=12),
            text_color=COLORS['medium']
        )
        self.status_label.pack(anchor="w", padx=15, pady=(0, 10))
    
    def _create_mode_section(self, parent):
        """Create analysis mode section"""
        mode_frame = ctk.CTkFrame(parent)
        mode_frame.pack(fill="x", pady=(0, 15))
        
        mode_label = ctk.CTkLabel(
            mode_frame,
            text="🎯 Analysis Type:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        mode_label.pack(anchor="w", padx=15, pady=(15, 10))
        
        # Radio buttons in a grid
        radio_frame = ctk.CTkFrame(mode_frame, fg_color="transparent")
        radio_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        modes = [
            ("full", "🔍 Full Audit", "Check everything: values, requirements, standards coverage"),
            ("compliance", "⚖️ Compliance Check", "Find non-compliant values and conflicting specifications"),
            ("gaps", "📋 Gap Analysis", "Find missing requirements from your spec"),
            ("values", "📐 Value Comparison", "Compare numerical values (voltage, current, etc.)"),
            ("standards", "📚 Standard Coverage", "Check which standards are referenced")
        ]
        
        for i, (value, text, desc) in enumerate(modes):
            row_frame = ctk.CTkFrame(radio_frame, fg_color="transparent")
            row_frame.pack(fill="x", pady=3)
            
            rb = ctk.CTkRadioButton(
                row_frame,
                text=text,
                variable=self.analysis_mode,
                value=value,
                font=ctk.CTkFont(size=13)
            )
            rb.pack(side="left")
            
            desc_label = ctk.CTkLabel(
                row_frame,
                text=f"  - {desc}",
                font=ctk.CTkFont(size=11),
                text_color=COLORS['text_muted']
            )
            desc_label.pack(side="left", padx=(10, 0))
    
    def _create_focus_section(self, parent):
        """Create focus area section with quick buttons"""
        focus_frame = ctk.CTkFrame(parent)
        focus_frame.pack(fill="x", pady=(0, 15))
        
        focus_label = ctk.CTkLabel(
            focus_frame,
            text="🔍 Focus Area (optional):",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        focus_label.pack(anchor="w", padx=15, pady=(15, 5))
        
        focus_hint = ctk.CTkLabel(
            focus_frame,
            text="Leave empty for full document analysis, or focus on specific topics",
            font=ctk.CTkFont(size=11),
            text_color=COLORS['text_muted']
        )
        focus_hint.pack(anchor="w", padx=15)
        
        # Entry
        self.focus_entry = ctk.CTkEntry(
            focus_frame,
            placeholder_text="e.g., cable sizing, fire safety, earthing...",
            width=400
        )
        self.focus_entry.pack(anchor="w", padx=15, pady=(8, 10))
        
        # Quick topic buttons
        quick_frame = ctk.CTkFrame(focus_frame, fg_color="transparent")
        quick_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        quick_label = ctk.CTkLabel(
            quick_frame,
            text="Quick Topics:",
            font=ctk.CTkFont(size=11),
            text_color=COLORS['text_muted']
        )
        quick_label.pack(side="left", padx=(0, 10))
        
        topics = [
            ("⚡ Electrical", "electrical installation wiring"),
            ("🔥 Fire Safety", "fire safety smoke detection"),
            ("🔌 Cable", "cable sizing cross section"),
            ("⏚ Earthing", "earthing grounding"),
            ("🔋 UPS", "UPS uninterruptible power"),
            ("💡 Lighting", "lighting illumination lux"),
            ("❄️ HVAC", "HVAC ventilation cooling"),
            ("🔒 Security", "security access control CCTV")
        ]
        
        for text, value in topics:
            btn = ctk.CTkButton(
                quick_frame,
                text=text,
                width=90,
                height=28,
                font=ctk.CTkFont(size=11),
                fg_color=COLORS['card_bg'],
                hover_color=COLORS['dark_bg'],
                command=lambda v=value: self._set_focus(v)
            )
            btn.pack(side="left", padx=2)
    
    def _create_buttons(self, parent):
        """Create action buttons - always visible at bottom"""
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(15, 5), side="bottom")
        
        self.cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=self.destroy,
            width=150,
            fg_color=COLORS['card_bg'],
            hover_color=COLORS['dark_bg']
        )
        self.cancel_btn.pack(side="left")
        
        self.analyze_btn = ctk.CTkButton(
            btn_frame,
            text="🚀 Start Analysis",
            command=self._start_analysis,
            width=200,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            state="disabled",
            fg_color="#1f6aa5"
        )
        self.analyze_btn.pack(side="right")
    
    def _on_source_changed(self, value):
        """Handle source document selection"""
        source = self.source_var.get()
        
        # Disable checkbox for selected source
        for doc, cb in self.ref_checkboxes.items():
            if doc == source:
                cb.configure(state="disabled")
                self.ref_vars[doc].set(False)
            else:
                cb.configure(state="normal")
        
        self._update_status()
    
    def _update_status(self):
        """Update status and button state"""
        source = self.source_var.get()
        has_source = source != "Select your specification..."
        
        ref_count = sum(1 for v in self.ref_vars.values() if v.get())
        
        if not has_source:
            self.status_label.configure(
                text="⚠️ Select your specification document",
                text_color=COLORS['medium']
            )
            self.analyze_btn.configure(state="disabled")
        elif ref_count == 0:
            self.status_label.configure(
                text="⚠️ Select at least 1 reference document",
                text_color=COLORS['medium']
            )
            self.analyze_btn.configure(state="disabled")
        else:
            self.status_label.configure(
                text=f"✅ Ready: Your spec vs {ref_count} reference(s)",
                text_color=COLORS['low']
            )
            self.analyze_btn.configure(state="normal")
    
    def _set_focus(self, value: str):
        """Set focus area from quick button"""
        self.focus_entry.delete(0, "end")
        self.focus_entry.insert(0, value)
    
    def _start_analysis(self):
        """Start the compliance analysis"""
        # Get selections
        source_doc = self.source_var.get()
        if source_doc == "Select your specification...":
            messagebox.showwarning("Selection Required", "Please select your specification")
            return
        
        ref_docs = [doc for doc, var in self.ref_vars.items() if var.get()]
        if not ref_docs:
            messagebox.showwarning("Selection Required", "Please select at least one reference document")
            return
        
        # Get mode
        mode_map = {
            'full': AnalysisMode.FULL_AUDIT,
            'compliance': AnalysisMode.COMPLIANCE_CHECK,
            'gaps': AnalysisMode.GAP_ANALYSIS,
            'values': AnalysisMode.VALUE_COMPARISON,
            'standards': AnalysisMode.STANDARD_COVERAGE
        }
        mode = mode_map[self.analysis_mode.get()]
        
        # Get focus
        focus = self.focus_entry.get().strip() or None
        
        # Show progress
        self.progress = ComplianceProgressDialog(self, source_doc, ref_docs)
        
        # Disable UI
        self.analyze_btn.configure(state="disabled", text="Analyzing...")
        self.cancel_btn.configure(state="disabled")
        
        # Run in background
        thread = Thread(
            target=self._run_analysis,
            args=(source_doc, ref_docs, mode, focus),
            daemon=True
        )
        thread.start()
    
    def _run_analysis(self, source_doc, ref_docs, mode, focus):
        """Run analysis in background"""
        try:
            self.after(0, lambda: self.progress.update_status("Loading documents..."))
            
            report = self.engine.analyze(
                source_doc=source_doc,
                reference_docs=ref_docs,
                mode=mode,
                focus_area=focus
            )
            
            self.after(0, lambda: self.progress.update_status(
                f"✅ Complete! Found {len(report.compliance_issues)} issues, "
                f"{len(report.gaps)} gaps"
            ))
            
            self.after(1000, self.progress.destroy)
            self.after(1100, lambda: self._show_report(report))
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}", exc_info=True)
            self.after(0, self.progress.destroy)
            self.after(0, lambda: messagebox.showerror("Error", f"Analysis failed: {str(e)}"))
            self.after(0, self._reset_ui)
    
    def _show_report(self, report: ComplianceReport):
        """Show the analysis report"""
        self.destroy()
        ComplianceReportDialog(self.master, report)
    
    def _reset_ui(self):
        """Reset UI after error"""
        self.analyze_btn.configure(state="normal", text="🚀 Start Analysis")
        self.cancel_btn.configure(state="normal")


class ComplianceProgressDialog(ctk.CTkToplevel):
    """Progress dialog during analysis"""
    
    def __init__(self, parent, source_doc: str, ref_docs: List[str]):
        super().__init__(parent)
        
        self.title("Analysis in Progress")
        self.geometry("500x280")
        self.resizable(False, False)
        
        # Center
        x = parent.winfo_x() + parent.winfo_width() // 2 - 250
        y = parent.winfo_y() + parent.winfo_height() // 2 - 140
        self.geometry(f"500x280+{x}+{y}")
        
        self.transient(parent)
        self.grab_set()
        
        # Content
        main = ctk.CTkFrame(self)
        main.pack(fill="both", expand=True, padx=30, pady=30)
        
        title = ctk.CTkLabel(
            main,
            text="🔄 Analyzing Documents",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(pady=(0, 15))
        
        info = ctk.CTkLabel(
            main,
            text=f"📄 Checking: {source_doc}\n📚 Against: {', '.join(ref_docs)}",
            font=ctk.CTkFont(size=12),
            justify="center"
        )
        info.pack(pady=(0, 20))
        
        self.progress = ctk.CTkProgressBar(main, mode="indeterminate")
        self.progress.pack(fill="x", pady=(0, 15))
        self.progress.start()
        
        self.status = ctk.CTkLabel(
            main,
            text="Initializing...",
            font=ctk.CTkFont(size=13)
        )
        self.status.pack()
    
    def update_status(self, text: str):
        """Update status text"""
        self.status.configure(text=text)


class ComplianceReportDialog(ctk.CTkToplevel):
    """Display compliance analysis results"""
    
    def __init__(self, parent, report: ComplianceReport):
        super().__init__(parent)
        
        self.report = report
        
        self.title("📊 Compliance Analysis Report")
        self.geometry("1100x800")
        self.minsize(1000, 700)
        
        # Center
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 1100) // 2
        y = (self.winfo_screenheight() - 800) // 2
        self.geometry(f"1100x800+{x}+{y}")
        
        self.transient(parent)
        self.grab_set()
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create report widgets"""
        main = ctk.CTkFrame(self)
        main.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header with score
        self._create_header(main)
        
        # Summary cards
        self._create_summary_cards(main)
        
        # Tabbed results
        self._create_tabs(main)
        
        # Buttons
        self._create_buttons(main)
    
    def _create_header(self, parent):
        """Create header with compliance score"""
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", pady=(0, 15))
        
        # Left side - Title and info
        left = ctk.CTkFrame(header, fg_color="transparent")
        left.pack(side="left", fill="y")
        
        title = ctk.CTkLabel(
            left,
            text="📊 Compliance Analysis Report",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        title.pack(anchor="w")
        
        info = ctk.CTkLabel(
            left,
            text=f"📄 {self.report.source_document}  →  📚 {', '.join(self.report.reference_documents)}",
            font=ctk.CTkFont(size=12),
            text_color=COLORS['text_muted']
        )
        info.pack(anchor="w", pady=(5, 0))
        
        if self.report.focus_area:
            focus = ctk.CTkLabel(
                left,
                text=f"🎯 Focus: {self.report.focus_area}",
                font=ctk.CTkFont(size=11),
                text_color=COLORS['text_muted']
            )
            focus.pack(anchor="w")
        
        # Right side - Score
        right = ctk.CTkFrame(header, fg_color="transparent")
        right.pack(side="right")
        
        score = self.report.compliance_score
        if score >= 80:
            score_color = COLORS['low']
            score_emoji = "✅"
        elif score >= 60:
            score_color = COLORS['medium']
            score_emoji = "⚠️"
        else:
            score_color = COLORS['critical']
            score_emoji = "❌"
        
        score_label = ctk.CTkLabel(
            right,
            text=f"{score_emoji} {score:.0f}%",
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color=score_color
        )
        score_label.pack()
        
        score_text = ctk.CTkLabel(
            right,
            text="Compliance Score",
            font=ctk.CTkFont(size=11),
            text_color=COLORS['text_muted']
        )
        score_text.pack()
    
    def _create_summary_cards(self, parent):
        """Create summary cards"""
        cards = ctk.CTkFrame(parent, fg_color="transparent")
        cards.pack(fill="x", pady=(0, 15))
        
        # Issue counts
        counts = [
            ("🔴 Critical", self.report.critical_count, COLORS['critical']),
            ("🟠 High", self.report.high_count, COLORS['high']),
            ("🟡 Medium", self.report.medium_count, COLORS['medium']),
            ("🟢 Low", self.report.low_count, COLORS['low']),
            ("📋 Gaps", len(self.report.gaps), COLORS['info']),
            ("📐 Values", len(self.report.value_comparisons), COLORS['text_muted'])
        ]
        
        for label, count, color in counts:
            card = ctk.CTkFrame(cards, width=120, height=80)
            card.pack(side="left", padx=5, fill="y")
            card.pack_propagate(False)
            
            num = ctk.CTkLabel(
                card,
                text=str(count),
                font=ctk.CTkFont(size=28, weight="bold"),
                text_color=color
            )
            num.pack(pady=(15, 0))
            
            txt = ctk.CTkLabel(
                card,
                text=label,
                font=ctk.CTkFont(size=11),
                text_color=COLORS['text_muted']
            )
            txt.pack()
    
    def _create_tabs(self, parent):
        """Create tabbed results view"""
        self.tabview = ctk.CTkTabview(parent)
        self.tabview.pack(fill="both", expand=True, pady=(0, 15))
        
        # Issues Tab
        issues_tab = self.tabview.add("⚠️ Issues")
        self._populate_issues(issues_tab)
        
        # Gaps Tab
        gaps_tab = self.tabview.add("📋 Gaps")
        self._populate_gaps(gaps_tab)
        
        # Values Tab
        values_tab = self.tabview.add("📐 Values")
        self._populate_values(values_tab)
        
        # Standards Tab
        standards_tab = self.tabview.add("📚 Standards")
        self._populate_standards(standards_tab)
    
    def _populate_issues(self, parent):
        """Populate issues tab"""
        text = ctk.CTkTextbox(parent, wrap="word")
        text.pack(fill="both", expand=True)
        
        if not self.report.compliance_issues:
            text.insert("1.0", "✅ No compliance issues found!\n\n")
            text.insert("end", "Your specification appears to be compliant with the reference documents.")
        else:
            # Group by severity
            for severity in [IssueSeverity.CRITICAL, IssueSeverity.HIGH, IssueSeverity.MEDIUM, IssueSeverity.LOW]:
                issues = [i for i in self.report.compliance_issues if i.severity == severity]
                if not issues:
                    continue
                
                emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}[severity.value]
                text.insert("end", f"\n{emoji} {severity.value.upper()} SEVERITY ({len(issues)})\n")
                text.insert("end", "═" * 80 + "\n\n")
                
                for i, issue in enumerate(issues, 1):
                    text.insert("end", f"Issue #{i}: {issue.topic}\n")
                    text.insert("end", f"Category: {issue.category.value.replace('_', ' ').title()}\n")
                    text.insert("end", f"Description: {issue.description}\n\n")
                    
                    text.insert("end", f"📄 Your Spec ({issue.source_doc}):\n")
                    text.insert("end", f"   Section: {issue.source_section} (Page {issue.source_page})\n")
                    if issue.source_value:
                        text.insert("end", f"   Value: {issue.source_value}\n")
                    text.insert("end", f"   \"{issue.source_text[:200]}...\"\n\n")
                    
                    text.insert("end", f"📚 Reference ({issue.reference_doc}):\n")
                    text.insert("end", f"   Section: {issue.reference_section} (Page {issue.reference_page})\n")
                    if issue.reference_value:
                        text.insert("end", f"   Value: {issue.reference_value}\n")
                    text.insert("end", f"   \"{issue.reference_text[:200]}...\"\n\n")
                    
                    if issue.recommendation:
                        text.insert("end", f"💡 Recommendation: {issue.recommendation}\n")
                    
                    text.insert("end", "─" * 80 + "\n\n")
        
        text.configure(state="disabled")
    
    def _populate_gaps(self, parent):
        """Populate gaps tab"""
        text = ctk.CTkTextbox(parent, wrap="word")
        text.pack(fill="both", expand=True)
        
        if not self.report.gaps:
            text.insert("1.0", "✅ No significant gaps found!\n\n")
            text.insert("end", "Your specification appears to cover the requirements from reference documents.")
        else:
            mandatory = [g for g in self.report.gaps if g.mandatory]
            optional = [g for g in self.report.gaps if not g.mandatory]
            
            if mandatory:
                text.insert("end", "🔴 MANDATORY REQUIREMENTS (Missing)\n")
                text.insert("end", "═" * 80 + "\n\n")
                
                for i, gap in enumerate(mandatory, 1):
                    text.insert("end", f"Gap #{i}: {gap.topic}\n")
                    text.insert("end", f"Source: {gap.reference_doc} - {gap.reference_section}\n")
                    text.insert("end", f"\nMissing Requirement:\n")
                    text.insert("end", f"\"{gap.missing_requirement}\"\n\n")
                    text.insert("end", f"Impact: {gap.impact}\n")
                    text.insert("end", f"💡 Recommendation: {gap.recommendation}\n")
                    text.insert("end", "─" * 80 + "\n\n")
            
            if optional:
                text.insert("end", "\n🟡 RECOMMENDED (Consider Adding)\n")
                text.insert("end", "═" * 80 + "\n\n")
                
                for i, gap in enumerate(optional, 1):
                    text.insert("end", f"Item #{i}: {gap.topic}\n")
                    text.insert("end", f"Source: {gap.reference_doc}\n")
                    text.insert("end", f"Description: {gap.description}\n")
                    text.insert("end", "─" * 80 + "\n\n")
        
        text.configure(state="disabled")
    
    def _populate_values(self, parent):
        """Populate values comparison tab"""
        text = ctk.CTkTextbox(parent, wrap="word")
        text.pack(fill="both", expand=True)
        
        if not self.report.value_comparisons:
            text.insert("1.0", "ℹ️ No value comparisons available.\n\n")
            text.insert("end", "No matching numerical parameters found between documents.")
        else:
            text.insert("end", "📐 VALUE COMPARISONS\n")
            text.insert("end", "═" * 80 + "\n\n")
            
            # Table header
            text.insert("end", f"{'Parameter':<20} {'Your Spec':<15} {'Reference':<15} {'Diff %':<10} {'Status':<10}\n")
            text.insert("end", "─" * 80 + "\n")
            
            for comp in self.report.value_comparisons:
                status_emoji = {
                    "MATCH": "✅",
                    "HIGHER": "⬆️",
                    "LOWER": "⬇️",
                    "CONFLICT": "❌"
                }.get(comp.status, "❓")
                
                text.insert(
                    "end",
                    f"{comp.parameter:<20} "
                    f"{comp.source_value}{comp.unit:<10} "
                    f"{comp.reference_value}{comp.unit:<10} "
                    f"{comp.percentage_diff:+.1f}%{'':5} "
                    f"{status_emoji} {comp.status}\n"
                )
            
            text.insert("end", "\n" + "─" * 80 + "\n")
            text.insert("end", f"\nSource: {self.report.source_document}\n")
            text.insert("end", f"References: {', '.join(self.report.reference_documents)}\n")
        
        text.configure(state="disabled")
    
    def _populate_standards(self, parent):
        """Populate standards coverage tab"""
        text = ctk.CTkTextbox(parent, wrap="word")
        text.pack(fill="both", expand=True)
        
        text.insert("end", "📚 STANDARDS COVERAGE\n")
        text.insert("end", "═" * 80 + "\n\n")
        
        text.insert("end", "✅ Standards Referenced in Your Spec:\n")
        if self.report.standards_referenced:
            for std in sorted(self.report.standards_referenced):
                text.insert("end", f"   • {std}\n")
        else:
            text.insert("end", "   (None found)\n")
        
        text.insert("end", f"\n⚠️ Standards in References but NOT in Your Spec:\n")
        if self.report.standards_missing:
            for std in sorted(self.report.standards_missing):
                text.insert("end", f"   • {std}\n")
        else:
            text.insert("end", "   ✅ All referenced standards are covered!\n")
        
        text.configure(state="disabled")
    
    def _create_buttons(self, parent):
        """Create action buttons"""
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.pack(fill="x")
        
        ctk.CTkButton(
            btn_frame,
            text="📋 Copy Report",
            command=self._copy_report,
            width=150,
            fg_color=COLORS['card_bg']
        ).pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(
            btn_frame,
            text="💾 Export PDF",
            command=self._export_pdf,
            width=150,
            fg_color=COLORS['card_bg'],
            state="disabled"  # Future feature
        ).pack(side="left")
        
        ctk.CTkButton(
            btn_frame,
            text="Close",
            command=self.destroy,
            width=150
        ).pack(side="right")
    
    def _copy_report(self):
        """Copy report to clipboard"""
        text = self._generate_text_report()
        self.clipboard_clear()
        self.clipboard_append(text)
        messagebox.showinfo("Copied", "Report copied to clipboard!")
    
    def _generate_text_report(self) -> str:
        """Generate plain text report"""
        lines = []
        lines.append("=" * 80)
        lines.append("COMPLIANCE ANALYSIS REPORT")
        lines.append("=" * 80)
        lines.append(f"\nSource: {self.report.source_document}")
        lines.append(f"References: {', '.join(self.report.reference_documents)}")
        lines.append(f"Focus: {self.report.focus_area or 'All areas'}")
        lines.append(f"Compliance Score: {self.report.compliance_score:.0f}%")
        lines.append(f"\nGenerated: {self.report.timestamp}")
        lines.append(f"Duration: {self.report.analysis_duration:.1f}s")
        lines.append("\n" + self.report.summary)
        
        if self.report.compliance_issues:
            lines.append("\n\nCOMPLIANCE ISSUES")
            lines.append("-" * 80)
            for i, issue in enumerate(self.report.compliance_issues, 1):
                lines.append(f"\n{i}. [{issue.severity.value.upper()}] {issue.topic}")
                lines.append(f"   {issue.description}")
                if issue.recommendation:
                    lines.append(f"   Recommendation: {issue.recommendation}")
        
        if self.report.gaps:
            lines.append("\n\nGAPS FOUND")
            lines.append("-" * 80)
            for i, gap in enumerate(self.report.gaps, 1):
                lines.append(f"\n{i}. {'[MANDATORY]' if gap.mandatory else '[OPTIONAL]'} {gap.topic}")
                lines.append(f"   {gap.description}")
        
        return "\n".join(lines)
    
    def _export_pdf(self):
        """Export to PDF (future feature)"""
        messagebox.showinfo("Coming Soon", "PDF export will be available in a future update.")


# For backwards compatibility
CrossReferenceDialog = CrossReferenceDialogV2
