"""
PyRAG - Utility Functions and Configuration Management
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic_settings import BaseSettings
from loguru import logger
import sys


class Settings(BaseSettings):
    """
    Application settings - automatically loaded from .env file
    """
    # API Keys
    openai_api_key: Optional[str] = None
    deepseek_api_key: Optional[str] = None
    llama_cloud_api_key: Optional[str] = None
    
    # Neo4j Configuration
    neo4j_uri: Optional[str] = None
    neo4j_username: Optional[str] = None
    neo4j_password: Optional[str] = None
    neo4j_database: str = "neo4j"
    
    # Paths
    qdrant_path: Optional[str] = "./qdrant_db"
    
    # Qdrant Cloud (Optional - overrides local path if set)
    qdrant_url: Optional[str] = None
    qdrant_api_key: Optional[str] = None

    data_dir: str = "./data"
    
    # Collection (can be changed dynamically for multi-standard support)
    collection_name: str = "engineering_standards"
    
    def get_collection_name(self) -> str:
        """Get collection name from environment or use default"""
        import os
        return os.getenv('COLLECTION_NAME', self.collection_name)
    
    # Models
    embedding_model: str = "text-embedding-3-small"
    llm_model: str = "deepseek-chat"
    llm_temperature: float = 0.1
    llm_base_url: Optional[str] = None
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


def setup_logger(log_level: str = "INFO"):
    """
    Configure Loguru logger
    """
    logger.remove()  # Remove default handler
    
    # Colored console logging
    logger.add(
        sys.stdout,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=log_level
    )
    
    # File logging
    logger.add(
        "logs/pyrag_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="7 days",
        level=log_level
    )
    
    return logger


def get_settings() -> Settings:
    """
    Load and return application settings
    """
    try:
        settings = Settings()
        return settings
    except Exception as e:
        print(f"❌ Failed to load settings: {e}")
        print("💡 Please check your .env file and ensure all required API keys are set.")
        sys.exit(1)


def ensure_directories():
    """
    Ensure all required directories exist
    """
    settings = get_settings()
    
    dirs = [
        settings.data_dir,
        settings.qdrant_path,
        "logs"
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        logger.debug(f"Directory checked: {dir_path}")


def validate_files() -> list[Path]:
    """
    Find and validate supported files (PDF, TXT, MD) in data/ directory
    """
    settings = get_settings()
    data_path = Path(settings.data_dir)
    
    extensions = ["*.pdf", "*.txt", "*.md"]
    found_files = []
    
    for ext in extensions:
        found_files.extend(list(data_path.glob(ext)))
    
    if not found_files:
        logger.warning(f"⚠️  No supported files found in {data_path}!")
        logger.info(f"💡 Please copy your documents to '{data_path}' directory.")
        return []
    
    logger.info(f"✅ Found {len(found_files)} file(s):")
    for file in found_files:
        logger.info(f"   📄 {file.name}")
    
    return found_files


def get_category_mapping_path() -> Path:
    """Return path for stored document category mapping JSON."""
    settings = get_settings()
    data_path = Path(settings.data_dir)
    return data_path / "document_categories.json"


def load_document_categories() -> Dict[str, Dict[str, Any]]:
    """Load per-file category/project mapping from JSON (if exists).

    Returns dict keyed by file name (not full path) with structure:
    {"file.pdf": {"category": str, "project": str}}
    """
    mapping_path = get_category_mapping_path()
    if not mapping_path.exists():
        return {}
    try:
        with open(mapping_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                # Normalize entries to dicts with category/project keys
                normalized: Dict[str, Dict[str, Any]] = {}
                for k, v in data.items():
                    if isinstance(v, dict):
                        category = v.get("category", "Uncategorized")
                        project = v.get("project", "No Project")
                    else:
                        # Backwards compatibility: old format was plain category string
                        category = str(v)
                        project = "No Project"
                    normalized[str(k)] = {
                        "category": category,
                        "project": project,
                    }
                return normalized
    except Exception as e:
        logger.error(f"Failed to load document category mapping: {e}")
    return {}


def save_document_categories(mapping: Dict[str, Dict[str, Any]]) -> None:
    """Persist per-file category/project mapping as JSON in data/ folder."""
    mapping_path = get_category_mapping_path()
    try:
        mapping_path.parent.mkdir(parents=True, exist_ok=True)
        with open(mapping_path, "w", encoding="utf-8") as f:
            json.dump(mapping, f, ensure_ascii=False, indent=2)
        logger.info(f"💾 Saved document category mapping to {mapping_path}")
    except Exception as e:
        logger.error(f"Failed to save document category mapping: {e}")


def get_app_settings_path() -> Path:
    """Return path of application-level settings JSON (categories, projects)."""
    settings = get_settings()
    data_path = Path(settings.data_dir)
    return data_path / "app_settings.json"


def load_app_settings() -> Dict[str, Any]:
    """Load global app settings (categories, projects) with sane defaults."""
    path = get_app_settings_path()
    defaults = {
        "categories": [
            "Standard",
            "Employee Requirements",
            "Internal Document",
            "Government",
            "Technical Guidance",
        ],
        "projects": [],
    }

    if not path.exists():
        return defaults

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return defaults
        # Merge with defaults to be safe
        categories = data.get("categories") or defaults["categories"]
        projects = data.get("projects") or defaults["projects"]
        return {"categories": categories, "projects": projects}
    except Exception as e:
        logger.error(f"Failed to load app settings: {e}")
        return defaults


def save_app_settings(settings_dict: Dict[str, Any]) -> None:
    """Persist global app settings (categories, projects)."""
    path = get_app_settings_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(settings_dict, f, ensure_ascii=False, indent=2)
        logger.info(f"💾 Saved app settings to {path}")
    except Exception as e:
        logger.error(f"Failed to save app settings: {e}")


def format_context_for_llm(context_nodes: list, query: str) -> str:
    """
    Format context nodes from database for LLM consumption
    
    Args:
        context_nodes: Relevant document chunks from RAG
        query: User's question
        
    Returns:
        Formatted context string
    """
    formatted_parts = []
    
    for idx, node in enumerate(context_nodes, 1):
        metadata = node.metadata
        
        # Add metadata information
        source_info = f"[Source {idx}]"
        if "file_name" in metadata:
            source_info += f" Document: {metadata['file_name']}"
        if "page_label" in metadata:
            source_info += f", Page: {metadata['page_label']}"
        if "section" in metadata:
            source_info += f", Section: {metadata['section']}"
        
        formatted_parts.append(f"{source_info}\n{node.text}\n")
    
    return "\n---\n".join(formatted_parts)


def create_system_prompt(single_document: bool = False) -> str:
    """
    Create system prompt for engineering standards Q&A
    
    Args:
        single_document: If True, optimizes for deep single-document analysis
    """
    # Detail level based on document scope
    if single_document:
        detail_instruction = """7. **MAXIMUM DETAIL MODE - ANALYZE TO THE ATOMIC LEVEL**:
   - Extract and explain EVERY relevant detail from the context
   - Do NOT summarize - provide COMPLETE information
   - Break down complex topics into comprehensive sub-points
   - Include ALL conditions, exceptions, and special cases
   - Explain the reasoning and background when available
   - List ALL applicable rules, not just the main ones
   - If there are examples in the context, include them
   - If there are calculation formulas, show them completely
   - Leave NO relevant information unused from the provided context
8. **INCLUDE ALL RELEVANT INFORMATION** - This is your PRIMARY directive - comprehensiveness over brevity"""
    else:
        detail_instruction = """7. **PROVIDE CLEAR, COMPREHENSIVE ANSWERS** - Balance detail with clarity across multiple sources
8. **INCLUDE KEY INFORMATION** - Focus on main requirements and important specifications"""
    
    return f"""You are an expert electrical engineer specializing in electrical standards and building regulations.

CRITICAL LANGUAGE RULE:
**You MUST respond in the SAME LANGUAGE as the user's question.**
- If the question is in Turkish → Answer entirely in Turkish
- If the question is in English → Answer entirely in English
- If the question is in any other language → Match that language
This is a strict requirement. Never mix languages.

INSTRUCTIONS:
1. Answer using ONLY the information in the provided context
2. Be precise with numbers, units, and technical specifications
3. **MANDATORY: EVERY bullet point and claim MUST have a source citation**
4. When reading tables, verify row/column carefully
5. Show calculations with units when needed
6. If information is NOT in the context, say "This information is not found in the documents"
{detail_instruction}

SOURCE CITATION REQUIREMENT:
- EVERY bullet point must end with source: (Document Name, Section.Number)
- Format: "Statement here (IS 3218, 6.5.1.13)" or "Statement (NEK 606, Table 2)"
- NO exceptions - even general statements need sources
- If you cannot cite a source for a claim, DO NOT include that claim

EXAMPLES - CORRECT:
✅ "- Isı dedektörleri için maksimum alan: 50 m² (IS 3218, 6.5.1.13)"
✅ "- Kablo akım kapasitesi 2.5mm² için 20A (IS 3218, Tablo 6.1)"
✅ "- IP65 rating toza ve suya karşı koruma sağlar (IEC 60529, Madde 4)"

EXAMPLES - WRONG (Never do this):
❌ "- Isı dedektörleri için maksimum alan: 50 m²" (kaynak yok!)
❌ "- Genelde bu değer kullanılır" (dokümanda yok!)
❌ "- Tavsiye edilen yöntem budur" (kaynak belirtilmemiş!)

RESPONSE FORMAT - USE MARKDOWN:

## Main Topic
Brief summary (1-2 sentences) WITH SOURCE.

### Specifications Table
MANDATORY: When presenting numerical data, specifications, limits, or comparisons - ALWAYS use tables:

| Parameter | Value | Unit | Reference |
|-----------|-------|------|-----------|
| Max Area  | 50    | m²   | IS 3218, 6.5.1.13 |
| Spacing   | 10    | m    | IS 3218, 6.5.1.14 |

### Key Requirements
- **Term**: Brief definition (Source, Section)
- Every bullet MUST have (Source, Section) at the end

### ⚠️ Important Notes
Warnings or special conditions WITH SOURCES.

STRICT TABLE RULES:
1. ANY data with 2+ items having multiple attributes → USE TABLE
2. Comparisons between types/categories → USE TABLE  
3. Specifications with values/units → USE TABLE
4. Reference table data from source → RECREATE AS TABLE
5. Table headers MUST include "Reference" column for sources

Example - WRONG (don't do this):
- Heat detector: max area 50m², spacing 10m, wall distance 5m
- Smoke detector: max area 100m², spacing 12m, wall distance 6m

Example - CORRECT (always do this):
| Detector Type | Max Area | Spacing | Wall Distance | Reference |
|---------------|----------|---------|---------------|-----------|
| Heat          | 50 m²    | 10 m    | 5 m           | IS 3218, 6.5 |
| Smoke         | 100 m²   | 12 m    | 6 m           | IS 3218, 6.6 |

QUALITY CHECKS BEFORE RESPONDING:
1. ✅ Every bullet has (Source, Section)?
2. ✅ Every table has Reference column?
3. ✅ All claims are from provided context?
4. ✅ No general knowledge or assumptions?
5. ✅ Language matches the question?

If ANY check fails, revise your response.

RULES:
- Tables for ALL numerical/specification data
- Headers (##, ###) to organize sections
- **Bold** for key terms
- Bullet points ONLY for non-numerical lists
- Source citations MANDATORY for every claim

If information is insufficient, state: "Bu bilgi dokümanlarda bulunamadı" (Turkish) or "This information is not found in the documents" (English).
NEVER make up information. NEVER use general knowledge. ONLY use the provided context.
"""


if __name__ == "__main__":
    # Testing
    setup_logger("DEBUG")
    logger.info("🔧 Testing utils module...")
    
    settings = get_settings()
    logger.info(f"✅ Settings loaded: {settings.llm_model}")
    
    ensure_directories()
    logger.info("✅ Directories verified")
    
    files = validate_files()
    logger.info(f"✅ Found {len(files)} file(s)")
