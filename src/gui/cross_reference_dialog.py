"""
Cross-Reference Analysis Dialog

This module provides the GUI dialog for multi-document cross-reference analysis.
"""

import customtkinter as ctk
from typing import Optional, Dict, List
import logging
from threading import Thread

from ..cross_reference import (
    CrossReferenceEngine,
    AnalysisType,
    AnalysisReport,
    SeverityLevel
)

logger = logging.getLogger(__name__)

# Golden ratio
PHI = 1.618


class CrossReferenceDialog(ctk.CTkToplevel):
    """Dialog for cross-reference analysis between multiple documents"""
    
    def __init__(self, parent, query_engine, available_documents: List[str]):
        """
        Initialize the Cross-Reference Dialog
        
        Args:
            parent: Parent window
            query_engine: Instance of QueryEngine
            available_documents: List of available document names
        """
        super().__init__(parent)
        
        self.query_engine = query_engine
        self.available_documents = sorted(available_documents)
        self.engine = CrossReferenceEngine(query_engine)
        
        # Window settings
        self.title("Cross-Reference Analysis")
        
        # Set minimum size and make resizable
        self.minsize(700, 800)
        self.geometry("750x850")
        self.resizable(True, True)  # Allow resize
        
        # Add maximize button functionality
        self.attributes('-topmost', False)
        
        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (750 // 2)
        y = (self.winfo_screenheight() // 2) - (850 // 2)
        self.geometry(f"750x850+{x}+{y}")
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        # Selected documents and analysis type
        self.selected_docs = []
        self.analysis_type_var = ctk.StringVar(value="conflicts")
        
        self._create_widgets()
        
    def _create_widgets(self):
        """Create dialog widgets"""
        
        # Main container
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="🔗 Cross-Reference Analysis",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Document selection (fixed height)
        doc_frame = ctk.CTkFrame(main_frame, height=280)
        doc_frame.pack(fill="x", pady=(0, 10))
        doc_frame.pack_propagate(False)  # Maintain fixed height
        
        # Base document selection
        base_label = ctk.CTkLabel(
            doc_frame,
            text="📄 Base Document (Reference):",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        base_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        self.base_doc_var = ctk.StringVar(value="Select base document...")
        self.base_dropdown = ctk.CTkOptionMenu(
            doc_frame,
            variable=self.base_doc_var,
            values=self.available_documents,
            command=self._on_base_doc_changed,
            width=660
        )
        self.base_dropdown.pack(fill="x", padx=10, pady=(0, 15))
        
        # Compare against selection
        compare_label = ctk.CTkLabel(
            doc_frame,
            text="📋 Compare Against (1-4):",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        compare_label.pack(anchor="w", padx=10, pady=(5, 5))
        
        # Scrollable frame for compare checkboxes
        self.doc_scroll = ctk.CTkScrollableFrame(doc_frame, height=120)
        self.doc_scroll.pack(fill="x", padx=10, pady=(0, 10))
        
        # Create checkboxes for compare against
        self.compare_vars: Dict[str, ctk.BooleanVar] = {}
        self.compare_checkboxes: Dict[str, ctk.CTkCheckBox] = {}
        for doc_name in self.available_documents:
            var = ctk.BooleanVar(value=False)
            cb = ctk.CTkCheckBox(
                self.doc_scroll,
                text=doc_name,
                variable=var,
                command=self._on_compare_selected
            )
            cb.pack(anchor="w", padx=5, pady=2)
            self.compare_vars[doc_name] = var
            self.compare_checkboxes[doc_name] = cb
        
        # Selection counter
        self.selection_label = ctk.CTkLabel(
            doc_frame,
            text="Base: None | Compare: 0 document(s)",
            font=ctk.CTkFont(size=12)
        )
        self.selection_label.pack(anchor="w", padx=10, pady=(0, 10))
        
        # Analysis type (fixed height)
        analysis_frame = ctk.CTkFrame(main_frame, height=180)
        analysis_frame.pack(fill="x", pady=(0, 10))
        analysis_frame.pack_propagate(False)
        
        analysis_label = ctk.CTkLabel(
            analysis_frame,
            text="🎯 Analysis Type:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        analysis_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        # Radio buttons for analysis type
        radio_frame = ctk.CTkFrame(analysis_frame, fg_color="transparent")
        radio_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        ctk.CTkRadioButton(
            radio_frame,
            text="Detect Conflicts",
            variable=self.analysis_type_var,
            value="conflicts"
        ).pack(anchor="w", pady=2)
        
        ctk.CTkRadioButton(
            radio_frame,
            text="Gap Analysis",
            variable=self.analysis_type_var,
            value="gaps"
        ).pack(anchor="w", pady=2)
        
        ctk.CTkRadioButton(
            radio_frame,
            text="Requirement Alignment",
            variable=self.analysis_type_var,
            value="alignment"
        ).pack(anchor="w", pady=2)
        
        ctk.CTkRadioButton(
            radio_frame,
            text="Requirements Mapping",
            variable=self.analysis_type_var,
            value="requirements"
        ).pack(anchor="w", pady=2)
        
        # Focus area (optional, fixed height)
        focus_frame = ctk.CTkFrame(main_frame, height=90)
        focus_frame.pack(fill="x", pady=(0, 15))
        focus_frame.pack_propagate(False)
        
        focus_label = ctk.CTkLabel(
            focus_frame,
            text="🔍 Focus Area (optional):",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        focus_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        self.focus_entry = ctk.CTkEntry(
            focus_frame,
            placeholder_text="e.g., fire safety, cable sizing, maximum impedance..."
        )
        self.focus_entry.pack(fill="x", padx=10, pady=(0, 10))
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(10, 0))
        
        self.cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.destroy,
            width=150
        )
        self.cancel_btn.pack(side="left", padx=(0, 10))
        
        self.analyze_btn = ctk.CTkButton(
            button_frame,
            text="🚀 Analyze",
            command=self._start_analysis,
            width=150,
            state="disabled"
        )
        self.analyze_btn.pack(side="right")
        
    def _on_base_doc_changed(self, value):
        """Handle base document selection change"""
        base_doc = self.base_doc_var.get()
        
        # Disable checkbox for selected base document
        for doc_name, cb in self.compare_checkboxes.items():
            if doc_name == base_doc:
                cb.configure(state="disabled")
                self.compare_vars[doc_name].set(False)
            else:
                cb.configure(state="normal")
        
        self._update_selection_status()
    
    def _on_compare_selected(self):
        """Handle compare document selection change"""
        self._update_selection_status()
    
    def _update_selection_status(self):
        """Update selection status label and analyze button state"""
        base_doc = self.base_doc_var.get()
        
        # Count selected compare documents
        compare_count = sum(1 for var in self.compare_vars.values() if var.get())
        
        # Update label
        base_text = base_doc if base_doc != "Select base document..." else "None"
        self.selection_label.configure(
            text=f"Base: {base_text} | Compare: {compare_count} document(s)"
        )
        
        # Enable analyze button if base selected and 1-4 compare documents selected
        if base_doc != "Select base document..." and 1 <= compare_count <= 4:
            self.analyze_btn.configure(state="normal")
        else:
            self.analyze_btn.configure(state="disabled")
    
    def _start_analysis(self):
        """Start the cross-reference analysis"""
        # Get base document
        base_doc = self.base_doc_var.get()
        if base_doc == "Select base document...":
            self._show_error("Please select a base document")
            return
        
        # Get compare documents
        compare_docs = [
            doc_name for doc_name, var in self.compare_vars.items()
            if var.get()
        ]
        
        if len(compare_docs) < 1:
            self._show_error("Please select at least 1 document to compare against")
            return
        
        if len(compare_docs) > 4:
            self._show_error("Please select maximum 4 documents to compare")
            return
        
        # Build document list: base document + compare documents
        selected_docs = [base_doc] + compare_docs
        
        # Get analysis type
        analysis_type_str = self.analysis_type_var.get()
        analysis_type = AnalysisType(analysis_type_str)
        
        # Get focus area
        focus_area = self.focus_entry.get().strip()
        if not focus_area:
            focus_area = None
        
        # Show progress dialog
        self.progress_dialog = AnalysisProgressDialog(self, selected_docs[0], len(selected_docs) - 1)
        
        # Disable main dialog UI during analysis
        self.analyze_btn.configure(state="disabled", text="Analyzing...")
        self.cancel_btn.configure(state="disabled")
        
        # Run analysis in background thread
        thread = Thread(
            target=self._run_analysis,
            args=(selected_docs, analysis_type, focus_area),
            daemon=True
        )
        thread.start()
    
    def _run_analysis(
        self,
        selected_docs: List[str],
        analysis_type: AnalysisType,
        focus_area: Optional[str]
    ):
        """
        Run the analysis in background thread
        
        Args:
            selected_docs: List of selected document names
            analysis_type: Type of analysis
            focus_area: Optional focus area
        """
        import time
        
        try:
            logger.info(f"Starting analysis: {analysis_type.value} on {len(selected_docs)} docs")
            
            # Update progress: Starting
            self.after(0, lambda: self.progress_dialog.update_status("Initializing analysis..."))
            time.sleep(0.5)
            
            # Run analysis
            self.after(0, lambda: self.progress_dialog.update_status("Comparing documents..."))
            
            report = self.engine.analyze(
                doc_names=selected_docs,
                analysis_type=analysis_type,
                focus_area=focus_area,
                top_k=10
            )
            
            # Update progress: Complete
            self.after(0, lambda: self.progress_dialog.update_status(f"✅ Found {len(report.conflicts)} conflicts!"))
            time.sleep(1)
            
            # Close progress dialog
            self.after(0, lambda: self.progress_dialog.destroy())
            
            # Show results in UI thread
            self.after(0, self._show_results, report)
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}", exc_info=True)
            self.after(0, lambda: self.progress_dialog.destroy())
            self.after(0, self._show_error, f"Analysis failed: {str(e)}")
            self.after(0, self._reset_ui)
    
    def _show_results(self, report: AnalysisReport):
        """Show analysis results"""
        # Close this dialog and open report dialog
        self.destroy()
        
        # Open report dialog
        report_dialog = CrossReferenceReportDialog(self.master, report)
        report_dialog.focus()
    
    def _show_error(self, message: str):
        """Show error message"""
        error_dialog = ctk.CTkToplevel(self)
        error_dialog.title("Error")
        error_dialog.geometry("400x150")
        error_dialog.resizable(False, False)
        
        # Center on parent
        error_dialog.transient(self)
        error_dialog.grab_set()
        
        label = ctk.CTkLabel(
            error_dialog,
            text=message,
            wraplength=350,
            font=ctk.CTkFont(size=13)
        )
        label.pack(pady=30)
        
        btn = ctk.CTkButton(
            error_dialog,
            text="OK",
            command=error_dialog.destroy,
            width=100
        )
        btn.pack(pady=(0, 20))
    
    def _reset_ui(self):
        """Reset UI after analysis"""
        self.analyze_btn.configure(state="normal", text="🚀 Analyze")
        self.cancel_btn.configure(state="normal")


class CrossReferenceReportDialog(ctk.CTkToplevel):
    """Dialog to display cross-reference analysis report"""
    
    def __init__(self, parent, report: AnalysisReport):
        """
        Initialize the Report Dialog
        
        Args:
            parent: Parent window
            report: Analysis report to display
        """
        super().__init__(parent)
        
        self.report = report
        
        # Window settings
        self.title("Analysis Report")
        self.geometry("900x700")
        
        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (900 // 2)
        y = (self.winfo_screenheight() // 2) - (700 // 2)
        self.geometry(f"900x700+{x}+{y}")
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create report display widgets"""
        
        # Main container
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 15))
        
        title = self._get_analysis_title()
        title_label = ctk.CTkLabel(
            header_frame,
            text=title,
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack()
        
        # Documents analyzed
        doc_text = f"Documents: {', '.join(self.report.documents)}"
        doc_label = ctk.CTkLabel(
            header_frame,
            text=doc_text,
            font=ctk.CTkFont(size=12)
        )
        doc_label.pack(pady=(5, 0))
        
        if self.report.focus_area:
            focus_label = ctk.CTkLabel(
                header_frame,
                text=f"Focus Area: {self.report.focus_area}",
                font=ctk.CTkFont(size=12)
            )
            focus_label.pack()
        
        # Summary
        summary_frame = ctk.CTkFrame(main_frame)
        summary_frame.pack(fill="x", pady=(0, 15))
        
        summary_text = ctk.CTkTextbox(summary_frame, height=80, wrap="word")
        summary_text.pack(fill="x", padx=10, pady=10)
        summary_text.insert("1.0", self.report.summary)
        summary_text.configure(state="disabled")
        
        # Results
        results_frame = ctk.CTkFrame(main_frame)
        results_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        results_label = ctk.CTkLabel(
            results_frame,
            text="Detailed Results:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        results_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        # Scrollable results
        self.results_text = ctk.CTkTextbox(results_frame, wrap="word")
        self.results_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self._populate_results()
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x")
        
        ctk.CTkButton(
            button_frame,
            text="Copy Report",
            command=self._copy_report,
            width=150
        ).pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(
            button_frame,
            text="Close",
            command=self.destroy,
            width=150
        ).pack(side="right")
    
    def _get_analysis_title(self) -> str:
        """Get title based on analysis type"""
        titles = {
            AnalysisType.CONFLICTS: "⚠️ Conflict Analysis Report",
            AnalysisType.GAPS: "📊 Gap Analysis Report",
            AnalysisType.ALIGNMENT: "🎯 Alignment Check Report",
            AnalysisType.REQUIREMENTS: "📋 Requirements Mapping Report"
        }
        return titles.get(self.report.analysis_type, "Analysis Report")
    
    def _populate_results(self):
        """Populate results textbox"""
        if self.report.analysis_type == AnalysisType.CONFLICTS:
            self._show_conflicts()
        elif self.report.analysis_type == AnalysisType.GAPS:
            self._show_gaps()
        else:
            self.results_text.insert("1.0", "Implementation in progress...")
        
        self.results_text.configure(state="disabled")
    
    def _show_conflicts(self):
        """Display conflict analysis results"""
        if not self.report.conflicts:
            self.results_text.insert("1.0", "No conflicts detected.\n")
            return
        
        # Group by severity
        high = [c for c in self.report.conflicts if c.severity == SeverityLevel.HIGH]
        medium = [c for c in self.report.conflicts if c.severity == SeverityLevel.MEDIUM]
        low = [c for c in self.report.conflicts if c.severity == SeverityLevel.LOW]
        
        # Display high severity first
        if high:
            self.results_text.insert("end", "🔴 HIGH SEVERITY CONFLICTS\n", "heading")
            self.results_text.insert("end", "=" * 80 + "\n\n")
            for i, conflict in enumerate(high, 1):
                self._format_conflict(conflict, i)
        
        if medium:
            self.results_text.insert("end", "\n🟡 MEDIUM SEVERITY CONFLICTS\n", "heading")
            self.results_text.insert("end", "=" * 80 + "\n\n")
            for i, conflict in enumerate(medium, 1):
                self._format_conflict(conflict, i)
        
        if low:
            self.results_text.insert("end", "\n🟢 LOW SEVERITY CONFLICTS\n", "heading")
            self.results_text.insert("end", "=" * 80 + "\n\n")
            for i, conflict in enumerate(low, 1):
                self._format_conflict(conflict, i)
    
    def _format_conflict(self, conflict, index: int):
        """Format a single conflict for display"""
        self.results_text.insert("end", f"Conflict #{index}: {conflict.topic}\n", "bold")
        self.results_text.insert("end", f"Description: {conflict.description}\n\n")
        
        self.results_text.insert("end", f"📄 {conflict.doc1_name}\n", "doc")
        self.results_text.insert("end", f"   Section: {conflict.doc1_section} (Page {conflict.doc1_page})\n")
        self.results_text.insert("end", f"   \"{conflict.doc1_text}\"\n\n")
        
        self.results_text.insert("end", f"📄 {conflict.doc2_name}\n", "doc")
        self.results_text.insert("end", f"   Section: {conflict.doc2_section} (Page {conflict.doc2_page})\n")
        self.results_text.insert("end", f"   \"{conflict.doc2_text}\"\n\n")
        
        if conflict.resolution:
            self.results_text.insert("end", f"💡 Resolution: {conflict.resolution}\n")
        
        self.results_text.insert("end", "-" * 80 + "\n\n")
    
    def _show_gaps(self):
        """Display gap analysis results"""
        if not self.report.gaps:
            self.results_text.insert("1.0", "Gap analysis complete. Implementation details coming soon.\n")
        else:
            for gap in self.report.gaps:
                self.results_text.insert("end", f"Gap: {gap.topic}\n")
                self.results_text.insert("end", f"{gap.description}\n\n")
    
    def _copy_report(self):
        """Copy report to clipboard"""
        report_text = self._generate_text_report()
        self.clipboard_clear()
        self.clipboard_append(report_text)
        
        # Show confirmation
        self.title("Analysis Report - Copied!")
        self.after(2000, lambda: self.title("Analysis Report"))
    
    def _generate_text_report(self) -> str:
        """Generate plain text version of report"""
        lines = []
        lines.append(self._get_analysis_title())
        lines.append("=" * 80)
        lines.append(f"Documents: {', '.join(self.report.documents)}")
        if self.report.focus_area:
            lines.append(f"Focus Area: {self.report.focus_area}")
        lines.append(f"Timestamp: {self.report.timestamp}")
        lines.append("")
        lines.append("SUMMARY")
        lines.append("-" * 80)
        lines.append(self.report.summary)
        lines.append("")
        
        if self.report.conflicts:
            lines.append("CONFLICTS")
            lines.append("-" * 80)
            for i, conflict in enumerate(self.report.conflicts, 1):
                lines.append(f"\nConflict #{i}: {conflict.topic}")
                lines.append(f"Severity: {conflict.severity.value.upper()}")
                lines.append(f"Description: {conflict.description}")
                lines.append(f"\n{conflict.doc1_name} ({conflict.doc1_section}):")
                lines.append(f'  "{conflict.doc1_text}"')
                lines.append(f"\n{conflict.doc2_name} ({conflict.doc2_section}):")
                lines.append(f'  "{conflict.doc2_text}"')
                if conflict.resolution:
                    lines.append(f"\nResolution: {conflict.resolution}")
                lines.append("-" * 80)
        
        return "\n".join(lines)


class AnalysisProgressDialog(ctk.CTkToplevel):
    """Progress dialog for cross-reference analysis"""
    
    def __init__(self, parent, base_doc: str, compare_count: int):
        super().__init__(parent)
        
        self.base_doc = base_doc
        self.compare_count = compare_count
        
        # Window settings
        self.title("Analysis in Progress")
        self.geometry("500x250")
        self.resizable(False, False)
        
        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - 250
        y = parent.winfo_y() + (parent.winfo_height() // 2) - 125
        self.geometry(f"500x250+{x}+{y}")
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create progress widgets"""
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=30, pady=30)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="🔄 Analyzing Documents",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Info
        info_text = f"Base: {self.base_doc}\nComparing against {self.compare_count} document(s)"
        info_label = ctk.CTkLabel(
            main_frame,
            text=info_text,
            font=ctk.CTkFont(size=12)
        )
        info_label.pack(pady=(0, 20))
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(main_frame, mode="indeterminate")
        self.progress_bar.pack(fill="x", pady=(0, 15))
        self.progress_bar.start()
        
        # Status label
        self.status_label = ctk.CTkLabel(
            main_frame,
            text="Initializing...",
            font=ctk.CTkFont(size=13)
        )
        self.status_label.pack(pady=(0, 10))
        
        # Conflict counter
        self.conflict_label = ctk.CTkLabel(
            main_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.conflict_label.pack()
    
    def update_status(self, status_text: str, conflicts: int = 0):
        """Update progress status"""
        self.status_label.configure(text=status_text)
        
        if conflicts > 0:
            self.conflict_label.configure(
                text=f"🔴 {conflicts} potential conflicts detected"
            )
