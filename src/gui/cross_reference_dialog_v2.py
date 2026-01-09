"""
Cross-Reference Analysis Dialog - Golden Rule Comparison

Simplified GUI for verifying compatibility between documents based on Extraction Rules.
"""

import customtkinter as ctk
from threading import Thread
from tkinter import messagebox
import logging
import webbrowser
import os

from src.rule_comparator import RuleComparator
from src.rule_miner import RuleMiner
from src.reports.report_generator import ReportGenerator

logger = logging.getLogger(__name__)

class CrossReferenceDialogV2(ctk.CTkToplevel):
    def __init__(self, parent, query_engine, available_documents_unused):
        super().__init__(parent)
        
        self.query_engine = query_engine
        self.comparator = RuleComparator(query_engine)
        self.last_report_data = None
        
        # We only care about documents that have been mined
        self.available_documents = sorted(list({
            r['source_doc'] for r in self.comparator.miner.existing_rules 
            if r.get('source_doc')
        }))
        
        # Window settings
        self.title("⚖️ Golden Rule Cross-Reference")
        self.geometry("1000x800")
        
        # Center window
        self.update_idletasks()
        try:
            x = (self.winfo_screenwidth() // 2) - 500
            y = (self.winfo_screenheight() // 2) - 400
            self.geometry(f"1000x800+{x}+{y}")
        except:
            pass
            
        self.lift()
        self.focus_force()
        
        self._create_ui()
        
    def _create_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        # 1. Header
        header = ctk.CTkFrame(self)
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=20)
        
        ctk.CTkLabel(
            header,
            text="Rule-Based Compliance Check",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(side="left", padx=20, pady=15)
        
        # Project Metadata Inputs
        meta_frame = ctk.CTkFrame(header, fg_color="transparent")
        meta_frame.pack(side="right", padx=20)
        
        self.project_ref_var = ctk.StringVar(value="PROJ-001")
        ctk.CTkEntry(meta_frame, textvariable=self.project_ref_var, width=100, placeholder_text="Ref No").pack(side="right", padx=5)
        ctk.CTkLabel(meta_frame, text="Ref:").pack(side="right")
        
        # 2. Controls (Selection)
        controls = ctk.CTkFrame(self)
        controls.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))
        
        # Doc A
        ctk.CTkLabel(controls, text="Base Document:").pack(side="left", padx=10)
        self.doc1_var = ctk.StringVar()
        self.combo1 = ctk.CTkComboBox(controls, values=self.available_documents, variable=self.doc1_var, width=250)
        if self.available_documents: self.combo1.set(self.available_documents[0])
        self.combo1.pack(side="left", padx=5)
        
        ctk.CTkLabel(controls, text="VS", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=15)
        
        # Doc B
        ctk.CTkLabel(controls, text="Comparison Doc:").pack(side="left", padx=10)
        self.doc2_var = ctk.StringVar()
        self.combo2 = ctk.CTkComboBox(controls, values=self.available_documents, variable=self.doc2_var, width=250)
        if len(self.available_documents) > 1: self.combo2.set(self.available_documents[1])
        self.combo2.pack(side="left", padx=5)
        
        # Action
        self.btn_compare = ctk.CTkButton(
            controls, 
            text="Analyze Compatibility",
            command=self._start_analysis
        )
        self.btn_compare.pack(side="left", padx=20)

        # Export (Hidden/Disabled initially)
        self.btn_export = ctk.CTkButton(
            controls,
            text="Export HTML",
            command=self._export_report,
            state="disabled",
            fg_color="green",
            width=100
        )
        self.btn_export.pack(side="left", padx=5)

        self.btn_export_pdf = ctk.CTkButton(
            controls,
            text="Export PDF",
            command=self._export_report_pdf,
            state="disabled",
            fg_color="#B30B00", # PDF Red
            width=100
        )
        self.btn_export_pdf.pack(side="left", padx=5)
        
        if not self.available_documents:
            self.btn_compare.configure(state="disabled", text="No Mined Rules Found")
        
        # 3. Output
        self.result_area = ctk.CTkTextbox(self, font=ctk.CTkFont(family="Consolas", size=12))
        self.result_area.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
        self.result_area.insert("0.0", "Select two documents and click Analyze to compare their mandatory rules.\nOnly documents processed by 'Rule Miner' appear here.")
        
        # 4. Status
        self.status_bar = ctk.CTkLabel(self, text="Ready", anchor="w")
        self.status_bar.grid(row=3, column=0, sticky="ew", padx=20, pady=10)

    def _start_analysis(self):
        doc1 = self.doc1_var.get()
        doc2 = self.doc2_var.get()
        
        if not doc1 or not doc2:
            messagebox.showwarning("Selection Error", "Please select two documents.")
            return
            
        if doc1 == doc2:
            messagebox.showinfo("Wait", "comparing a document to itself is trivial (100% match). Choose different docs.")
            return

        self.btn_compare.configure(state="disabled")
        self.result_area.delete("1.0", "end")
        self.result_area.insert("1.0", f"Analyzing compatibility between {doc1} and {doc2}...\nThis may take a minute based on the number of rules.\n\n")
        self.status_bar.configure(text="Processing...", text_color="orange")
        
        Thread(target=self._run_comparison, args=(doc1, doc2)).start()

    def _run_comparison(self, d1, d2):
        try:
            # report is now a Dict
            report_data = self.comparator.compare_documents(d1, d2)
            self.after(0, lambda: self._show_report(report_data))
        except Exception as e:
            self.after(0, lambda: self._show_error(str(e)))
            
    def _show_report(self, report_data):
        self.last_report_data = report_data
        
        # Display text summary in the UI box
        text_content = report_data.get("text_report", "No report content generated.")
        
        self.result_area.delete("1.0", "end")
        self.result_area.insert("0.0", text_content)
        
        self.btn_compare.configure(state="normal")
        self.btn_export.configure(state="normal")  # Enable export
        self.btn_export_pdf.configure(state="normal") # Enable PDF export
        self.status_bar.configure(text="Analysis Complete", text_color="green")

    def _export_report(self):
        self._run_export("html")

    def _export_report_pdf(self):
        self._run_export("pdf")

    def _run_export(self, format_type):
        if not self.last_report_data:
            return
            
        try:
            # Inject metadata
            self.last_report_data["project_ref"] = self.project_ref_var.get()
            generator = ReportGenerator()
            
            if format_type == "html":
                filepath = generator.generate_html_report(self.last_report_data)
            else:
                filepath = generator.generate_pdf_report(self.last_report_data)
            
            # Ask to open
            if messagebox.askyesno("Report Ready", f"{format_type.upper()} Report saved to:\n{filepath}\n\nOpen now?"):
                import pathlib
                uri = pathlib.Path(filepath).as_uri()
                webbrowser.open(uri)
                
        except Exception as e:
            messagebox.showerror("Export Error", str(e))
        
    def _show_error(self, msg):
        messagebox.showerror("Error", msg)
        self.btn_compare.configure(state="normal")
        self.status_bar.configure(text="Error", text_color="red")
