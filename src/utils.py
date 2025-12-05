"""
PyRAG - Utility Functions and Configuration Management
"""

import os
from pathlib import Path
from typing import Optional
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
    
    # Paths
    chroma_db_path: str = "./chroma_db"
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
        settings.chroma_db_path,
        "logs"
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        logger.debug(f"Directory checked: {dir_path}")


def validate_pdf_files() -> list[Path]:
    """
    Find and validate PDF files in data/ directory
    """
    settings = get_settings()
    data_path = Path(settings.data_dir)
    
    pdf_files = list(data_path.glob("*.pdf"))
    
    if not pdf_files:
        logger.warning(f"⚠️  No PDF files found in {data_path}!")
        logger.info(f"💡 Please copy your standard PDFs (IS10101, etc.) to '{data_path}' directory.")
        return []
    
    logger.info(f"✅ Found {len(pdf_files)} PDF file(s):")
    for pdf in pdf_files:
        logger.info(f"   📄 {pdf.name}")
    
    return pdf_files


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


def create_system_prompt() -> str:
    """
    Create system prompt for LLM
    """
    return """You are an expert electrical engineer specializing in IS10101 and other electrical standards.

YOUR TASK:
- Answer the user's question using ONLY the information provided in the CONTEXT.
- Do not add information from outside the given context.
- When reading technical tables, be careful to use the correct row/column.
- Always provide source references in your answer (e.g., "According to Section 5.2.1, Table 3...")

ANSWER FORMAT:
1. Provide a concise and clear answer
2. Specify the relevant table or section
3. Show formulas or calculations if needed
4. Cite the source (Page number, Section, Table name)

PROHIBITED:
- Adding information not in the context
- Making assumptions or guesses
- Using uncertain phrases like "I think" or "probably"

If the answer is not in the context, respond: "I could not find sufficient information in the provided documents to answer this question."
"""


if __name__ == "__main__":
    # Testing
    setup_logger("DEBUG")
    logger.info("🔧 Testing utils module...")
    
    settings = get_settings()
    logger.info(f"✅ Settings loaded: {settings.llm_model}")
    
    ensure_directories()
    logger.info("✅ Directories verified")
    
    pdf_files = validate_pdf_files()
    logger.info(f"✅ Found {len(pdf_files)} PDF file(s)")
