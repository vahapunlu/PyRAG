# PyRAG - GUI Application Guide

## 🎨 Professional Windows Desktop Interface

PyRAG now includes a modern, user-friendly Windows desktop application built with CustomTkinter.

---

## 🚀 Quick Start

### Method 1: Double-Click Launch (Easiest)

Simply double-click `start_gui.bat` - it will:
- ✅ Create virtual environment (if needed)
- ✅ Install dependencies automatically
- ✅ Launch the GUI application

### Method 2: Command Line

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Launch GUI
python main.py gui

# Or simply
python main.py
```

---

## 💻 GUI Features

### Main Interface

- **Dark Mode Theme** - Modern, professional appearance
- **Chat Interface** - Natural conversation-style Q&A
- **Real-time Status** - System status indicators
- **Source Display** - Toggle to show/hide source documents

### Sidebar Controls

1. **📁 Add Document**
   - Create new document entries
   - Set project/category metadata
   - Browse and select PDFs
   - Auto-copy to data folder
   - Multi-file selection

2. **🔗 Cross-Reference**
   - Search across multiple documents simultaneously
   - Select documents to search
   - Get combined results with document sources
   - Filter by relevance

3. **📄 Auto-Summary**
   - Extract focused information from large specs
   - Three modes: Topic Extraction, Requirements List, Cross-Trade Comparison
   - Quick topic buttons (Electrical, UPS, Generator, etc.)
   - Export summaries to PDF or text
   - **Full-screen interface** with left/right panel layout

4. **🗄️ Database Manager**
   - View all Qdrant collections
   - Browse documents and chunks
   - Edit metadata (project, category, tags)
   - Export documents to text
   - Delete documents/collections
   - Real-time statistics

5. **📊 View Statistics**
   - Database info
   - Node count
   - PDF files list

6. **🗑️ Clear History**
   - Reset chat conversation
   - Confirm before clearing

7. **Settings**
   - API configuration
   - Model selection (GPT-4o/DeepSeek)
   - Temperature settings
   - Toggle source display

---

## 📖 How to Use

### First Time Setup

1. **Launch Application**
   ```
   Double-click: start_gui.bat
   ```

2. **Add PDF Files**
   - Click "➕ Add PDF Files"
   - Select your technical standard PDFs
   - (IS10101, ETCI Rules, etc.)

3. **Index Documents**
   - Click "📁 Index Documents"
   - Wait 5-10 minutes (one-time process)
   - ☕ Grab a coffee!

4. **Start Asking**
   - Type your question in the input box
   - Press Enter or click "Send ➤"
   - Get instant answers!

### Daily Usage

1. Launch app (double-click `start_gui.bat`)
2. Wait for "Ready" status (green)
3. Type questions and get answers!

---

## ✨ Example Questions

### Standard Chat Queries

Type these in the main chat:

```
What is the current carrying capacity for 2.5mm² copper cable?

Show me temperature correction factors for PVC insulated cables

What should be the grounding resistance according to IS10101?

Cable sizing for 32A breaker, PVC conduit, 3 cables

Correction factors for 4-cable group in 35°C ambient
```

### Auto-Summary Examples

1. **Topic Extraction**
   - "Show me all ELECTRICAL sections from LDA spec"
   - Click 📄 Auto-Summary → Select document → Click ⚡ Electrical

2. **Requirements List**
   - "List all UPS requirements from the specification"
   - Click 📄 Auto-Summary → Requirements List → Select doc → Click 🔋 UPS

3. **Cross-Trade Comparison**
   - "Compare firestopping requirements across all specs"
   - Click 📄 Auto-Summary → Comparison → Select multiple docs → Click 🧯 Firestopping

### Cross-Reference Examples

```
Find all voltage drop calculations across all specifications

Show me cable sizing tables from all documents

Search for grounding requirements in all standards
```

---

## 📄 Auto-Summary Feature Deep Dive

### Full-Screen Interface

Auto-Summary opens in a **full-screen window** with modern layout:

**Left Panel (300px):**
- Document selection (radio buttons)
- Quick Topic buttons (8 common topics)

**Right Panel (expandable):**
- Topic input field
- Generate/Export buttons
- Tabbed results view:
  - **Summary Tab**: LLM-generated structured summary
  - **Sections Tab**: All extracted sections with page numbers

### Quick Topic Buttons

Pre-configured for common MEP systems:
- ⚡ **Electrical**: electrical, electric, power, voltage, circuit, wiring
- 🔋 **UPS**: ups, uninterruptible power, emergency power
- ⚙️ **Generator**: generator, standby power, backup generator
- 💡 **Lighting**: lighting, illumination, luminaire, lamp
- 🔥 **Fire Alarm**: fire alarm, fire detection, smoke detector
- 🧯 **Firestopping**: firestopping, fire barrier, penetration seal
- 🔌 **Cable**: cable, conductor, wire, wiring, cabling
- 🧪 **Testing**: testing, commissioning, verification, inspection

Each button automatically expands the topic with relevant keywords for comprehensive extraction.

### Export Options

- **Text Export**: Plain text with all sections and page numbers
- **PDF Export**: Formatted report (coming soon - reportlab)

Export format includes:
- Header with metadata (date, document, topic)
- LLM summary section
- Complete extracted sections with page references

### Performance Tips

1. **Use Quick Topics** when possible - optimized keywords
2. **Be specific** with manual topics - "emergency lighting" vs "lighting"
3. **Multi-document comparison** takes 5-15 seconds
4. **Large specs (150+ pages)** process in 2-10 seconds

---

## 🎯 GUI vs CLI Comparison

| Feature | GUI | CLI |
|---------|-----|-----|
| Ease of Use | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Visual Feedback | ✅ Yes | ❌ No |
| Multi-turn Chat | ✅ Natural | ⭐⭐⭐ Basic |
| Progress Tracking | ✅ Visual | ⭐⭐ Text |
| PDF Management | ✅ File Dialog | ❌ Manual |
| Best For | Daily Use | Automation |

**Recommendation**: Use GUI for regular work, CLI for scripts/automation.

---

## 🎨 Interface Overview

```
┌─────────────────────────────────────────────────────────┐
│  SIDEBAR              │  MAIN CHAT AREA                 │
│                       │                                 │
│  ⚡ PyRAG             │  💬 Ask Your Questions          │
│  Engineering AI       │                                 │
│                       │  [Chat history displays here]   │
│  ● System Status      │                                 │
│    Ready (452 nodes)  │                                 │
│                       │                                 │
│  📁 Index Documents   │                                 │
│  ➕ Add PDF Files     │                                 │
│  📊 View Statistics   │                                 │
│  🗑️ Clear History     │                                 │
│                       │                                 │
│  Settings             │  [Type question] ______  Send ➤ │
│  ☑ Show Sources       │                                 │
│                       │                                 │
│  v1.0.0 | Local AI    │                                 │
└─────────────────────────────────────────────────────────┘
```

---

## ⚙️ Advanced Features

### Keyboard Shortcuts

- **Enter** - Send message
- **Ctrl+L** - Clear chat (future)
- **Ctrl+I** - Open indexing dialog (future)

### Status Indicators

- 🟢 **Green "Ready"** - System operational
- 🟠 **Orange "Processing"** - Working on your query
- 🔴 **Red "Error"** - Check logs
- ⚪ **Gray "Not initialized"** - Need to index

---

## 🐛 Troubleshooting

### "System not initialized"

**Solution**: 
1. Add PDFs to data folder
2. Click "Index Documents"
3. Wait for completion

### "Failed to import GUI"

**Solution**:
```powershell
pip install customtkinter pillow
```

### GUI doesn't start

**Solution**:
```powershell
# Check Python version (need 3.10+)
python --version

# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

### Slow responses

**Possible causes**:
- Large PDF files
- Many indexed nodes
- Slow internet (OpenAI API)

**Solution**: Normal for first query, subsequent queries are faster

---

## 🔄 Updates & Maintenance

### Add New PDFs

1. Click "➕ Add PDF Files"
2. Select new PDFs
3. Click "📁 Index Documents"
4. Check "Force rebuild"

### Clear Index

1. Stop application
2. Delete `qdrant_db/` folder
3. Restart and re-index

### View Logs

Check `logs/pyrag_YYYY-MM-DD.log` for detailed information

---

## 💡 Tips & Best Practices

1. **Specific Questions Get Better Answers**
   - ❌ "Tell me about cables"
   - ✅ "Current capacity for 2.5mm² copper cable in conduit"

2. **Enable "Show Sources"**
   - Verify information accuracy
   - See which pages were referenced

3. **Use Statistics**
   - Monitor indexed content
   - Verify all PDFs are processed

4. **Keep Chat History**
   - Review previous answers
   - Learn from past queries

---

## 🎯 Recent Features & Coming Soon

### ✅ Recently Added
- [x] **Auto-Summary Engine** - Extract focused info from large specs
- [x] **Cross-Reference Search** - Search multiple documents at once
- [x] **Database Manager** - Visual Qdrant management
- [x] **DeepSeek Integration** - 90% cost reduction vs GPT-4o
- [x] **Metadata Management** - Project/category tagging system
- [x] **Full-Screen Auto-Summary** - Modern left/right panel layout

### 🚧 Coming Soon
- [ ] Export chat to PDF/TXT
- [ ] Dark/Light theme toggle
- [ ] Font size controls
- [ ] Search in chat history
- [ ] Favorite questions
- [ ] Multi-language interface
- [ ] Custom system prompts
- [ ] PDF export for Auto-Summary (reportlab integration)
- [ ] Quantity Takeoff (technical drawing analysis)

---

## 📝 Technical Details

**Framework**: CustomTkinter (modern tkinter)
**Threading**: Background processing for queries
**Auto-scroll**: Chat always shows latest
**State Management**: Proper enable/disable of controls
**Error Handling**: User-friendly error messages

---

## 🆘 Need Help?

1. Check this guide
2. View `README.md` for full documentation
3. Check logs in `logs/` folder
4. Verify `.env` configuration
5. Try CLI mode: `python main.py stats`

---

**Enjoy your professional AI assistant! 🎉**
