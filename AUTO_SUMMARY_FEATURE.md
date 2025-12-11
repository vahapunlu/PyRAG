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
2. **Full-screen interface** opens with modern layout:
   - **Left Panel (300px)**: Document selection + Quick Topic buttons
   - **Right Panel**: Topic input, Generate/Export buttons, Results tabs
3. Select document(s) using radio buttons (left panel)
4. Enter topic manually OR click a Quick Topic button
5. Click **Generate** button
6. View results in two tabs:
   - **Summary**: LLM-generated structured summary with rich text formatting
   - **Sections**: All found sections with page numbers
7. Click **Export** to save as text file (PDF export coming soon)

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
   - Automatic document discovery from Qdrant
   - Error handling and validation

### Dependencies
- Uses existing QueryEngine (no new API calls)
- Qdrant for document storage and retrieval
- DeepSeek LLM for summary generation
- CustomTkinter for GUI

## UI Design

### Full-Screen Layout

```
┌─────────────────────────────────────────────────────────────┐
│  Auto-Summary - PyRAG Engineering Assistant                │
├───────────────┬─────────────────────────────────────────────┤
│  LEFT PANEL   │  RIGHT PANEL                                │
│  (300px)      │  (expandable)                              │
│               │                                             │
│  📄 Documents │  Enter Topic: [________________]           │
│  ○ LDA.pdf    │                                             │
│  ○ IS3218.pdf │  [Generate] [Export]                       │
│  ○ NSAI.pdf   │                                             │
│               │  ┌───────────────────────────────────────┐ │
│  Quick Topics │  │ Summary  │ Sections  │                │ │
│  ⚡ Electrical │  ├───────────────────────────────────────┤ │
│  🔋 UPS        │  │                                        │ │
│  ⚙️ Generator  │  │  [Results display here with rich      │ │
│  💡 Lighting   │  │   text formatting]                    │ │
│  🔥 Fire Alarm │  │                                        │ │
│  🧯 Firestop   │  │                                        │ │
│  🔌 Cable      │  │                                        │ │
│  🧪 Testing    │  │                                        │ │
│               │  └───────────────────────────────────────┘ │
└───────────────┴─────────────────────────────────────────────┘
```

### Rich Text Formatting

Summary results include:
- **Headings** (## bold text)
- **Bold text** (\*\*text\*\*)
- **Bullet points** (•)
- **Code blocks** (monospace font)
- Proper spacing and indentation

## Future Enhancements

### ✅ Recently Completed
- [x] Full-screen interface with left/right panels
- [x] Rich text formatting for summaries
- [x] 8 Quick Topic buttons with keyword expansion
- [x] Tabbed results view (Summary + Sections)

### 🚧 Coming Soon
- [ ] PDF export with formatting (reportlab integration in progress)
- [ ] Custom keyword expansion by user
- [ ] Save/load favorite topics
- [ ] Summary templates (e.g., "Compliance Checklist")
- [ ] Multi-language support
- [ ] Comparison matrix view for cross-trade analysis
- [ ] Topic clustering (group similar sections automatically)
- Diff view for comparing specific requirements
