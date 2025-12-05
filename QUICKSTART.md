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
```

## 🆘 Having Issues?

1. Check logs in `logs/` folder
2. See "Troubleshooting" section in README
3. Verify `.env` file configuration

---

**Happy coding! 🎉**
