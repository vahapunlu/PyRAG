# PyRAG - Engineering Compliance & Gap Analysis System
## Comprehensive Design Document
**Date:** 09.01.2026  
**Version:** 2.0  

---

## 1. Executive Summary
PyRAG is a specialized Retrieval-Augmented Generation (RAG) system designed for the engineering and construction sector. Unlike generic document chat bots, PyRAG functions as an automated "Compliance Auditor". It ingests technical specifications (PDFs), extracts mandatory engineering rules ("Golden Rules"), and performs cross-reference analysis to identify conflicts, missing requirements, and numerical discrepancies between two documents.

The system is built to mimic the workflow of a Senior Engineer reviewing a contractor's proposal against an employer's requirements, outputting formal reports suitable for submission (HTML/PDF).

---

## 2. System Architecture

### 2.1. High-Level Overview
The application follows a modular "Pipeline" architecture:
1.  **Ingestion Layer**: Processing raw PDFs into structured text and vector embeddings.
2.  **Intelligence Layer**: LLM-based reasoning to find specific rules (Rule Miner) and compare them (Comparator).
3.  **Storage Layer**: Hybrid storage using Vector DB (semantic search) and JSON/SQL (structured rules).
4.  **Presentation Layer**: Modern Windows GUI (CustomTkinter) and HTML/PDF Reporting Engine.

### 2.2. Tech Stack Setup
| Component | Technology | Role |
| :--- | :--- | :--- |
| **Language** | Python 3.10+ | Core logic |
| **GUI Framework** | CustomTkinter | Modern, dark-mode friendly desktop UI |
| **LLM Inference** | DeepSeek V3 / OpenAI | Reasoning, rule extraction, and comparison |
| **Orchestration** | LlamaIndex 0.9+ | RAG pipeline management, chunking, retrieval |
| **Vector DB** | Qdrant | Storing document embeddings for semantic search |
| **Rule Storage** | JSON (Local) | Storing "Golden Rules" (mined constraints) |
| **PDF Processing** | PyMuPDF (Check) | extracting text and tables from PDFs |
| **Reporting** | ReportLab (PDF), Jinja2/HTML | Generating enterprise-grade output files |

---

## 3. Core Workflows & Algorithms

### 3.1. Document Ingestion Pipeline
*   **Input**: PDF files (Specs, Standards).
*   **Process**:
    1.  Text Extraction via `PyMuPDF`.
    2.  Chunking (Split by paragraphs/headers).
    3.  Embedding Generation (text-3-small or similar).
    4.  Storage in Qdrant Vector DB.

### 3.2. "Golden Rule" Miner (RuleMiner)
This is the system's "memory" creation process.
*   **Goal**: Convert unstructured text into a database of specific engineering constraints.
*   **Logic**:
    1.  Scans document for keywords: *shall, must, required, minimum, maximum, rated at*.
    2.  Uses Regex `numeric_pattern` to capture parameters (e.g., `500 lux`, `2.5mm2`, `IP65`).
    3.  DeepSeek LLM validates: "Is this a mandatory engineering constraint?"
    4.  **Output**: `existing_rules` (List of Dictionaries) stored in `data/golden_rules.json`.

### 3.3. Cross-Reference Engine (RuleComparator)
This is the system's "reasoning" engine.
*   **Inputs**: Document A (Reference), Document B (Target).
*   **Logic**:
    1.  Retrieves "Golden Rules" for both documents.
    2.  Clusters rules by **Topic** (e.g., "Cables", "Lighting", "Forms of Separation").
    3.  **Delta Analysis (LLM)**: For each topic, the LLM compares the parameters.
        *   Look for Agreement (A=B).
        *   Look for Conflict (A says 500, B says 300).
        *   Look for Silence (A has requirement, B says nothing).
    4.  **Output**: Structured Dictionary containing analysis text and "TQs" (Technical Queries).

### 3.4. Enterprise Reporting (ReportGenerator)
*   **Goal**: Turn raw JSON/Dict data into a client-ready document.
*   **Formats**:
    *   **HTML**: Interactive, responsive, good for quick review.
    *   **PDF**: Strict A4 formatting, header/footer, permanent record.
*   **Features**:
    *   **Delta Tables**: Red/Green automated highlighting for numeric conflicts.
    *   **TQ Safety Net**: Automatically compiles a "Draft Technical Query" list at the end of the report.

---

## 4. User Interface (GUI) Design
The GUI is built with `CustomTkinter` for a professional "Dark Theme" look.

### 4.1. Sidebar Navigation
*   **Chat**: Free-form Q&A with documents.
*   **Rule Miner**: Tool to index a document and find its rules.
*   **Cross-Reference**: The main audit tool for comparing two docs.
*   **Settings**: API key configuration and prompt tuning.

### 4.2. Cross-Reference Dialog
*   **Inputs**: Select "Base Doc" and "Comparison Doc".
*   **Metadata**: Field for "Project Ref No".
*   **Actions**: "Analyze" (Runs Thread), "Export HTML" (Green), "Export PDF" (Red).

---

## 5. Directory Structure
```
d:\PYT\RAG\
│
├── data/
│   ├── golden_rules.json      # The "Brain" (Mined Rules)
│   └── document_categories.json
│
├── exports/                   # Generated Reports
│
├── src/
│   ├── gui/
│   │   ├── main_window.py
│   │   ├── sidebar.py
│   │   └── cross_reference_dialog_v2.py
│   │
│   ├── reports/
│   │   └── report_generator.py # HTML/PDF Engine
│   │
│   ├── rule_miner.py          # Extraction Logic
│   ├── rule_comparator.py     # Comparison Logic
│   └── query_engine.py        # LlamaIndex Wrapper
│
├── app_gui.py                 # Entry Point
└── requirements.txt
```

## 6. Future Roadmap
1.  **Multi-Doc Comparison**: Compare 1 Standard against 5 Contractor Proposals simultaneously.
2.  **Excel/CSV Export**: For Quantity Surveyors (QS) to import into cost sheets.
3.  **Active Learning**: User feedback ("This isn't a conflict") trains the local Rule Miner.

---

**Prepared By:** PyRAG Development Team  
**Confidentiality:** Internal Use Only
