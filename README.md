# PyRAG - Engineering Standards RAG Assistant 🚀

**Table-Aware**, **Local** Python-based RAG (Retrieval-Augmented Generation) system specifically designed for technical standards like IS10101.

---

## 🎯 Features

- ✅ **Modern Windows GUI**: Professional desktop application with CustomTkinter
- ✅ **Auto-Summary Engine**: Extract focused information from large specs (150+ pages)
- ✅ **Cross-Reference Search**: Find matching requirements across multiple documents
- ✅ **Database Manager**: Visual management of ChromaDB collections and documents
- ✅ **Table Awareness**: Preserves PDF tables in Markdown format for accurate reading
- ✅ **Local Database**: All data stays on your computer with ChromaDB
- ✅ **Hybrid Search**: Semantic + Keyword search for best results
- ✅ **GPT-4o/DeepSeek Support**: Interprets complex technical tables (90% cheaper with DeepSeek)
- ✅ **REST API**: Ready-to-use FastAPI service for React/Flutter
- ✅ **CLI Tools**: Command-line interface for all operations

---

## 📋 Requirements

- Python 3.10 or higher
- OpenAI API key ([get it here](https://platform.openai.com/api-keys))
- 2GB+ RAM (during indexing)
- Windows/Mac/Linux

---

## 🚀 Installation

### 1. Setup Python Environment

```powershell
# Create virtual environment (recommended)
python -m venv venv

# Activate (Windows)
.\venv\Scripts\Activate.ps1

# or (Mac/Linux)
source venv/bin/activate
```

### 2. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 3. Configure API Keys

Edit `.env` file and add your OpenAI API key:

```env
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
```

### 4. Add Your PDFs

Copy your standard PDFs (IS10101, etc.) to the `data/` folder:

```
data/
  ├── IS10101.pdf
  ├── ETCI_Rules.pdf
  └── BS7671.pdf
```

---

## 📖 Usage

### A. GUI Application (Recommended for Windows Users)

**Easiest way to use PyRAG:**

```powershell
# Simply double-click this file:
start_gui.bat
```

Or from command line:

```powershell
python main.py gui
# or just
python main.py
```

**Features:**
- 🎨 Modern dark theme interface
- 💬 Natural chat-style Q&A
- 📄 **Auto-Summary**: Extract topic-focused information from large specs
- 🔗 **Cross-Reference**: Search across multiple documents simultaneously
- 🗄️ **Database Manager**: Visual ChromaDB management with metadata editing
- 📁 Visual PDF management
- 📊 Real-time statistics
- ⚡ One-click indexing

See [GUI_GUIDE.md](GUI_GUIDE.md) for complete GUI documentation.

---

### B. Index Documents (First Step for CLI Users!)

On first use, you need to read PDFs and save them to the database:

```powershell
python main.py ingest
```

This process:
- Reads PDFs
- Detects and converts tables to Markdown
- Splits text semantically
- Vectorizes with OpenAI
- Saves to ChromaDB

⏱️ **Duration**: ~5-10 minutes for 100-page document

💰 **Cost**: ~$0.50-2 (document size dependent, one-time only)

---

### C. Ask Questions from Command Line

#### 1. Single Question

```powershell
python main.py query "What is the current carrying capacity for 2.5mm² copper cable?"
```

#### 2. Interactive Mode (Multiple Questions)

```powershell
python main.py interactive
```

```
❓ Question: What is the temperature correction factor for PVC cables?
✅ Answer: According to Table 5.2.1, for ambient temperature 30°C the correction factor is 1.0...
```

Type `exit` to quit

---

### D. Start API Server (for React/Flutter)

```powershell
python main.py serve
```

After server starts:
- 🌐 API Docs: http://localhost:8000/docs
- 📊 Health Check: http://localhost:8000/health

#### API Usage Example (JavaScript)

```javascript
const response = await fetch('http://localhost:8000/api/query', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    question: "What is 2.5mm cable current capacity?",
    return_sources: true
  })
});

const data = await response.json();
console.log(data.answer);
console.log(data.sources);
```

#### API Usage Example (Python)

```python
import requests

response = requests.post(
    'http://localhost:8000/api/query',
    json={
        'question': 'What is 2.5mm cable current capacity?',
        'return_sources': True
    }
)

data = response.json()
print(data['answer'])
```

---

## 🛠️ Advanced Usage

### Rebuild Index

If you've added new PDFs or changed settings:

```powershell
python main.py ingest --force
```

### View Statistics

```powershell
python main.py stats
```

Output:
```
📊 Database Information:
Collection: engineering_standards
Total Nodes: 452
Database Path: ./chroma_db
```

### Test Individual Modules

```powershell
# Test utils module
python src/utils.py

# Test ETL pipeline
python src/ingestion.py

# Test query engine
python src/query_engine.py
```

---

## 📂 Project Structure

```
PyRAG/
│
├── data/                    # Your PDF files go here
│   ├── IS10101.pdf
│   └── ...
│
├── chroma_db/              # Vector database (auto-created)
│
├── src/                    # Source code
│   ├── utils.py           # Utility functions
│   ├── ingestion.py       # PDF reading + indexing
│   ├── query_engine.py    # Query engine
│   └── api.py             # FastAPI server
│
├── logs/                   # Log files (auto-created)
│
├── main.py                 # Main entry point
├── requirements.txt        # Dependencies
├── .env                    # API keys (SECRET!)
├── .env.example            # Template
└── README.md               # This file
```

---

## ⚙️ Configuration

Settings in `.env` file:

```env
# OpenAI
OPENAI_API_KEY=sk-proj-xxxxx
LLAMA_CLOUD_API_KEY=llx-xxxxx  # Optional (advanced table extraction)

# Model Settings
EMBEDDING_MODEL=text-embedding-3-small
LLM_MODEL=gpt-4o
LLM_TEMPERATURE=0.1

# Database
CHROMA_DB_PATH=./chroma_db
COLLECTION_NAME=engineering_standards

# API Server
API_HOST=0.0.0.0
API_PORT=8000

# Log Level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO
```

---

## 🧪 Test Scenarios

### 1. Simple Question

```
❓ Question: What should the grounding resistance be according to IS10101?
✅ Answer: According to Section 8.3, grounding resistance must be maximum 100 ohms.
```

### 2. Table Query

```
❓ Question: 2.5mm² copper cable, PVC insulation, 30°C ambient - current carrying capacity?
✅ Answer: According to Table 4.3.1, reference value is 24A. For 30°C the correction factor is 1.0, so capacity is 24A.
```

### 3. Complex Calculation

```
❓ Question: 4-cable group, 35°C ambient, conduit installation - correction factor?
✅ Answer: Two correction factors apply:
- Temperature (Table 5.2.1): 0.94
- Grouping (Table 5.3.1): 0.8
Total: 0.94 × 0.8 = 0.752
```

---

## 🐛 Troubleshooting

### Error: "Collection not found"

**Solution**: Index first
```powershell
python main.py ingest
```

### Error: "OpenAI API key not found"

**Solution**: Check `.env` file and add your API key

### Error: "No PDF files found"

**Solution**: Copy PDFs to `data/` folder

### Answers are wrong/irrelevant

**Solution 1**: Rebuild index with `force_reindex`
```powershell
python main.py ingest --force
```

**Solution 2**: Lower `LLM_TEMPERATURE` in `.env` (e.g., 0.0)

---

## 💡 Tips

1. **Question Quality**: Ask specific questions
   - ❌ "Tell me about cables"
   - ✅ "What is the current carrying capacity for 2.5mm² copper cable in conduit?"

2. **Table Names**: If you know the table number, mention it
   - "According to Table 5.2.1..."

3. **Context**: Specify the standard
   - "According to IS10101..."

4. **API Usage**: In production, limit `allow_origins` and use HTTPS

---

## 🔒 Security and Privacy

- ✅ **All PDFs stay local** (nothing uploaded)
- ✅ **Vector database is local** (ChromaDB on your computer)
- ⚠️ **OpenAI receives**: Only processed text chunks (at query time)
- ⚠️ **Entire document is NOT uploaded**: Only relevant 3-5 paragraphs are sent

---

## 📈 Performance

| Operation | Duration | Cost |
|-----------|----------|------|
| Initial Indexing (100 pages) | ~5-10 min | ~$0.50-2 |
| Query (API) | 2-5 sec | ~$0.01 |
| Reindexing | ~5-10 min | ~$0.50-2 |

---

## 🚧 Future Plans

- [x] Auto-Summary engine for large documents ✅ **COMPLETED**
- [x] Cross-Reference search across documents ✅ **COMPLETED**
- [x] Database Manager with visual tools ✅ **COMPLETED**
- [x] DeepSeek integration (90% cost reduction) ✅ **COMPLETED**
- [ ] LlamaParse integration (better table extraction)
- [ ] Chat history (conversation memory)
- [ ] Multi-modal (image + diagram analysis)
- [ ] Turkish embedding model support
- [ ] Batch processing (multiple document queries)
- [ ] Web UI (React interface)
- [ ] Quantity Takeoff (technical drawing analysis)

---

## 📝 License

This project is for educational and research purposes. Check OpenAI and other library licenses for commercial use.

---

## 🤝 Support

For questions:
1. Check logs: `logs/pyrag_YYYY-MM-DD.log`
2. Verify status: `python main.py stats`
3. Open an issue (if using GitHub)

---

## 🎉 Installation Verification

Run these commands in order:

```powershell
# 1. Test modules
python src/utils.py

# 2. Index PDFs
python main.py ingest

# 3. Test query
python main.py query "Test question"

# 4. Check statistics
python main.py stats
```

If all succeed 🎊 **Your system is ready!**

---

**Developer Notes**: This system uses "Document Summary Index" strategy for tables. For each table, LLM generates a summary during indexing. These summaries are used during semantic search, ensuring table contents match better.
