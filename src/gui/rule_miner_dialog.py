
import customtkinter as ctk
from tkinter import messagebox
import threading
from .constants import *
from ..rule_miner import RuleMiner

class RuleMinerDialog(ctk.CTkToplevel):
    def __init__(self, parent, documents):
        super().__init__(parent)
        
        self.title("Rule Miner - Engineering Standards")
        self.geometry("900x700")
        
        # Bring to front
        self.lift()
        self.focus_force()
        self.attributes('-topmost', True)
        self.after(100, lambda: self.attributes('-topmost', False))
        
        self.documents = documents
        self.miner = RuleMiner()
        self.found_rules = []
        self.check_vars = []
        
        self._create_ui()
        
    def _create_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        # 1. Header & Selection
        header_frame = ctk.CTkFrame(self)
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=20)
        
        ctk.CTkLabel(
            header_frame, 
            text="Miner Protocol: Extract Mandatory Rules", 
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(side="left", padx=15, pady=15)
        
        # 2. Controls
        control_frame = ctk.CTkFrame(self)
        control_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))
        
        ctk.CTkLabel(control_frame, text="Select Standard:").pack(side="left", padx=10)
        
        # Get processed documents (for info/warning if needed)
        processed_docs = self.miner.get_processed_documents()
        
        # Filter out already processed documents
        self.available_docs = sorted([d for d in self.documents if d not in processed_docs])
        
        self.doc_var = ctk.StringVar()
        self.doc_combo = ctk.CTkComboBox(control_frame, values=self.available_docs, variable=self.doc_var, width=300)
        
        if self.available_docs:
            self.doc_combo.set(self.available_docs[0])
        else:
            self.doc_combo.set("All documents processed!")
            self.doc_combo.configure(state="disabled")
            
        self.doc_combo.pack(side="left", padx=10)
        
        self.mine_btn = ctk.CTkButton(
            control_frame, 
            text="⛏️ Mine Rules", 
            command=self._start_mining,
            fg_color=COLORS['primary']
        )
        if not self.available_docs:
            self.mine_btn.configure(state="disabled")
            
        self.mine_btn.pack(side="left", padx=10)
        
        self.status_label = ctk.CTkLabel(control_frame, text="", text_color="gray")
        self.status_label.pack(side="left", padx=10)

        # 3. Results Area
        self.results_frame = ctk.CTkScrollableFrame(self, label_text="Extracted Rules (Select to Save)")
        self.results_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
        
        # 4. Footer Actions
        footer_frame = ctk.CTkFrame(self)
        footer_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=20)
        
        self.save_btn = ctk.CTkButton(
            footer_frame,
            text="💾 Save to Knowledge Base",
            command=self._save_rules,
            state="disabled",
            fg_color=COLORS['success'],
            width=200
        )
        self.save_btn.pack(side="right", padx=10, pady=10)
        
        self.count_label = ctk.CTkLabel(footer_frame, text="0 rules found")
        self.count_label.pack(side="left", padx=15)

    def _start_mining(self):
        doc = self.doc_var.get()
        if not doc: return
        
        self.mine_btn.configure(state="disabled")
        self.status_label.configure(text=f"Scanning {doc}...", text_color="orange")
        
        # Run in thread
        threading.Thread(target=self._mining_process, args=(doc,)).start()

    def _mining_process(self, doc_name):
        try:
            rules = self.miner.mine_rules(doc_name)
            self.after(0, lambda: self._display_results(rules))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            self.after(0, lambda: self.mine_btn.configure(state="normal"))
            self.after(0, lambda: self.status_label.configure(text=""))

    def _display_results(self, rules):
        # Clear previous
        for widget in self.results_frame.winfo_children():
            widget.destroy()
            
        self.found_rules = rules
        self.check_vars = []
        
        if not rules:
            ctk.CTkLabel(self.results_frame, text="No mandatory rules found.").pack(pady=20)
            self.save_btn.configure(state="disabled")
            self.count_label.configure(text="0 rules found")
            return

        for i, rule in enumerate(rules):
            row = ctk.CTkFrame(self.results_frame)
            row.pack(fill="x", pady=2, padx=5)
            
            # Checkbox
            var = ctk.IntVar(value=1) # Default selected
            self.check_vars.append(var)
            
            cb = ctk.CTkCheckBox(
                row, 
                text="", 
                variable=var, 
                width=24,
                checkbox_width=20, 
                checkbox_height=20
            )
            cb.pack(side="left", padx=5, pady=5)
            
            # Text
            text_frame = ctk.CTkFrame(row, fg_color="transparent")
            text_frame.pack(side="left", fill="x", expand=True, padx=5)
            
            # Highlight keyword ? simpler just to show text
            ctk.CTkLabel(
                text_frame, 
                text=rule['rule_text'], 
                wraplength=700, 
                justify="left",
                anchor="w"
            ).pack(fill="x", pady=5)
            
            # Metadata badge
            meta = [f"Found: {', '.join(rule['keywords'])}"]
            if rule.get('context'):
                meta.append(f"Section: {rule['context']}")
            if rule.get('topics'):
                meta.append(f"Tags: {', '.join(rule['topics'])}")
            
            ctk.CTkLabel(
                text_frame, 
                text=" | ".join(meta), 
                font=ctk.CTkFont(size=10),
                text_color="gray"
            ).pack(anchor="w")

        self.count_label.configure(text=f"{len(rules)} candidates found")
        self.save_btn.configure(state="normal")
        self.status_label.configure(text=f"Completed. {len(rules)} candidates.", text_color="green")

    def _save_rules(self):
        selected_rules = []
        for i, var in enumerate(self.check_vars):
            if var.get() == 1:
                selected_rules.append(self.found_rules[i])
        
        if not selected_rules:
            messagebox.showwarning("Warning", "No rules selected to save.")
            return
            
        try:
            count = self.miner.save_rules(selected_rules)
            messagebox.showinfo("Success", f"Successfully saved {count} new rules to Knowledge Base.\nThe system will now prioritize these rules in queries.")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {e}")
