# Auto-Summary Feature

## Overview
The Auto-Summary feature allows MEP engineers to quickly extract focused information from large specification documents (150+ pages).

## Features

### Three Summary Types

1. **Topic Extraction** 📑
   - Extract all sections about a specific topic from one document
   - Example: "Show me all ELECTRICAL sections from this 150-page spec"
   - Uses keyword expansion: "electrical" → [electrical, electric, power, voltage, circuit, wiring, cable, conductor]

2. **Requirements List** 📋
   - List all requirements for a specific system from one document
   - Example: "What are all the UPS requirements?"
   - Generates structured list of requirements

3. **Cross-Trade Comparison** 🔄
   - Compare how a topic is addressed across multiple documents
   - Example: "Compare firestopping requirements across all specs"
   - Highlights differences and similarities

## Quick Topics

Pre-configured buttons for common MEP systems:
- ⚡ Electrical
- 🔋 UPS
- ⚙️ Generator
- 💡 Lighting
- 🔥 Fire Alarm
- 🧯 Firestopping
- 🔌 Cable
- 🧪 Testing

## Usage

### From GUI
1. Click **"📄 Auto-Summary"** button in the sidebar
2. Select summary type (Topic/Requirements/Comparison)
3. Choose document(s)
4. Enter topic or click a Quick Topic button
5. Click **Generate**
6. View results in two tabs:
   - **Summary**: LLM-generated structured summary
   - **Extracted Sections**: All found sections with page numbers
7. Export to text file if needed

### Example Workflows

#### Extract Electrical Requirements
```
1. Select: "Topic Extraction"
2. Document: "LDA.pdf"
3. Topic: Click "⚡ Electrical" or type "electrical systems"
4. Generate
→ Gets all electrical-related sections with LLM summary
```

#### Compare Firestopping Across Specs
```
1. Select: "Cross-Trade Comparison"
2. Documents: Check "LDA.pdf", "IS3218 2024.pdf", "NSAI.pdf"
3. Topic: Click "🧯 Firestopping" or type "firestopping"
4. Generate
→ Compares firestopping requirements across all 3 documents
```

#### List UPS Requirements
```
1. Select: "Requirements List"
2. Document: "LDA.pdf"
3. Topic: Click "🔋 UPS" or type "UPS systems"
4. Generate
→ Creates structured list of all UPS-related requirements
```

## Technical Details

### Keyword Expansion
The system automatically expands topics to catch variations:

- **electrical** → electrical, electric, power, voltage, circuit, wiring, cable, conductor
- **ups** → ups, uninterruptible power, emergency power, backup power
- **firestopping** → firestopping, fire stopping, fire barrier, fire seal, penetration seal
- **hvac** → hvac, heating, ventilation, air conditioning, climate control
- **plumbing** → plumbing, piping, water supply, drainage, sanitary
- **lighting** → lighting, illumination, luminaire, lamp, fixture
- **cable** → cable, conductor, wire, wiring, cabling
- **generator** → generator, standby power, backup generator, emergency generator
- **fire** → fire alarm, fire detection, smoke detector, fire safety

### Performance
- Efficient chunk filtering using keywords (no LLM per chunk)
- LLM only for final summary generation
- Typical processing: 2-10 seconds for topic extraction
- Comparison mode: ~5-15 seconds depending on document count

### Export Format
Exported text files include:
```
AUTO-SUMMARY REPORT
===================
Generated: 2024-12-07 20:30:45
Type: Topic Extraction
Document: LDA.pdf
Topic: electrical

SUMMARY
-------
[LLM-generated structured summary]

EXTRACTED SECTIONS (25 sections found)
--------------------------------------
[All found sections with page numbers]
```

## Architecture

### Core Components
1. **AutoSummaryEngine** (`src/auto_summary.py`)
   - Handles topic extraction, requirements listing, cross-trade comparison
   - Keyword expansion and chunk filtering
   - LLM summary generation

2. **AutoSummaryDialog** (`src/gui/auto_summary_dialog.py`)
   - User interface for summary generation
   - Radio buttons for summary type selection
   - Document selection (single/multi)
   - Quick topic buttons
   - Result display with tabs
   - Export functionality

3. **Integration** (`src/gui/main_window.py`, `src/gui/sidebar.py`)
   - Sidebar button: "📄 Auto-Summary"
   - Automatic document discovery from ChromaDB
   - Error handling and validation

### Dependencies
- Uses existing QueryEngine (no new API calls)
- ChromaDB for document storage and retrieval
- DeepSeek LLM for summary generation
- CustomTkinter for GUI

## Future Enhancements

Potential improvements:
- Custom keyword expansion by user
- Save/load favorite topics
- Summary templates (e.g., "Compliance Checklist")
- Multi-language support
- PDF export with formatting
- Comparison matrix view for cross-trade analysis
- Topic clustering (group similar sections automatically)
- Diff view for comparing specific requirements
