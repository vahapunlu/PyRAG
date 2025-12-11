# PyRAG - Quick Start Guide

## 🚀 Get Started in 3 Steps

### 1️⃣ Installation

```powershell
# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 2️⃣ Configuration

Edit `.env` file:
```env
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
```

Add your PDFs to `data/` folder.

### 3️⃣ Run

#### 🎨 GUI Mode (Recommended - Easiest!)

```powershell
# Just double-click:
start_gui.bat

# Or from command line:
python main.py gui
# or simply:
python main.py
```

**GUI Features:**
- 💬 **Chat**: Natural Q&A with your documents
- 📄 **Auto-Summary**: Extract focused info from large specs (full-screen interface)
- 🔗 **Cross-Reference**: Search across multiple documents simultaneously
- 🗄️ **Database Manager**: Visual Qdrant management with metadata editing
- 📁 **Add Document**: Upload PDFs with project/category metadata
- 📊 **Statistics**: View database stats and document counts

#### 💻 CLI Mode (Advanced)

```powershell
# Index documents (first time)
python main.py ingest

# Ask questions
python main.py query "Your question here"

# or Interactive mode
python main.py interactive

# or Start API server
python main.py serve
```

## 📚 Full Documentation

See [README.md](README.md) for complete features and usage scenarios.

## ⚡ Quick Test

```powershell
# System check
python src/utils.py

# Indexing check
python main.py stats

# Test Auto-Summary
# In GUI: Click "📄 Auto-Summary" → Select document → Click ⚡ Electrical

# Test Cross-Reference
# In GUI: Click "🔗 Cross-Reference" → Select documents → Enter query
```

## 🆘 Having Issues?

1. Check logs in `logs/` folder
2. See "Troubleshooting" section in README
3. Verify `.env` file configuration

---

**Happy coding! 🎉**
