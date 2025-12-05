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

1. **📁 Index Documents**
   - Process PDF files
   - Force rebuild option
   - Progress tracking
   - Cost warning ($0.50-2.00)

2. **➕ Add PDF Files**
   - Browse and select PDFs
   - Auto-copy to data folder
   - Multi-file selection

3. **📊 View Statistics**
   - Database info
   - Node count
   - PDF files list

4. **🗑️ Clear History**
   - Reset chat conversation
   - Confirm before clearing

5. **Settings**
   - Toggle source display
   - (More settings coming)

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

Type these in the chat:

```
What is the current carrying capacity for 2.5mm² copper cable?

Show me temperature correction factors for PVC insulated cables

What should be the grounding resistance according to IS10101?

Cable sizing for 32A breaker, PVC conduit, 3 cables

Correction factors for 4-cable group in 35°C ambient
```

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
2. Delete `chroma_db/` folder
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

## 🎯 Coming Soon

- [ ] Export chat to PDF/TXT
- [ ] Dark/Light theme toggle
- [ ] Font size controls
- [ ] Search in chat history
- [ ] Favorite questions
- [ ] Multi-language interface
- [ ] Custom system prompts
- [ ] Offline mode indicator

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
