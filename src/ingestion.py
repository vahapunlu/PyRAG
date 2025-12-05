"""
PyRAG - ETL Pipeline (Data Loading and Indexing)

This module reads PDFs, extracts tables, and indexes them into ChromaDB.
"""

import os
import re
from pathlib import Path
from typing import List, Optional, Dict, Tuple
import pymupdf4llm
import chromadb
from chromadb.config import Settings as ChromaSettings

from llama_index.core import (
    VectorStoreIndex,
    Document,
    StorageContext,
    Settings,
)
from llama_index.core.node_parser import (
    SentenceSplitter,
    SemanticSplitterNodeParser,
)
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.vector_stores.chroma import ChromaVectorStore

from loguru import logger
from src.utils import get_settings, setup_logger, validate_pdf_files


class DocumentIngestion:
    """
    Reads PDF documents, processes them, and loads into vector database
    """
    
    def __init__(self, collection_name: Optional[str] = None):
        self.settings = get_settings()
        
        # Override collection name if provided
        if collection_name:
            os.environ['COLLECTION_NAME'] = collection_name
            self.settings = get_settings()  # Reload to pick up new collection name
            
        self._setup_llama_index()
        self._setup_vector_store()
        
    def _setup_llama_index(self):
        """Configure LlamaIndex global settings"""
        logger.info("🔧 Configuring LlamaIndex...")
        
        # Determine which LLM to use based on model name
        if "deepseek" in self.settings.llm_model.lower():
            # DeepSeek uses OpenAI-compatible API
            logger.info("📡 Using DeepSeek API (90% cheaper!)...")
            Settings.llm = OpenAI(
                model=self.settings.llm_model,
                temperature=self.settings.llm_temperature,
                api_key=self.settings.deepseek_api_key,
                api_base="https://api.deepseek.com"
            )
        else:
            # Default to OpenAI
            logger.info("📡 Using OpenAI API...")
            Settings.llm = OpenAI(
                model=self.settings.llm_model,
                temperature=self.settings.llm_temperature,
                api_key=self.settings.openai_api_key
            )
        
        # Embedding settings (OpenAI text-embedding-3-large for best quality)
        Settings.embed_model = OpenAIEmbedding(
            model="text-embedding-3-large",
            api_key=self.settings.openai_api_key
        )
        
        # Chunk settings
        Settings.chunk_size = 1024
        Settings.chunk_overlap = 200
        
        logger.success("✅ LlamaIndex configured")
    
    def _setup_vector_store(self):
        """Prepare ChromaDB database"""
        logger.info("🔧 Connecting to ChromaDB...")
        
        # ChromaDB client
        self.chroma_client = chromadb.PersistentClient(
            path=self.settings.chroma_db_path,
            settings=ChromaSettings(
                anonymized_telemetry=False
            )
        )
        
        # Create or load collection (support dynamic collection names)
        try:
            collection_name = self.settings.get_collection_name()
            self.chroma_collection = self.chroma_client.get_or_create_collection(
                name=collection_name,
                metadata={"description": "Engineering Standards RAG Database"}
            )
            logger.success(f"✅ Collection '{collection_name}' ready")
        except Exception as e:
            logger.error(f"❌ ChromaDB collection error: {e}")
            raise
        
        # Vector store wrapper
        self.vector_store = ChromaVectorStore(
            chroma_collection=self.chroma_collection
        )
    
    def extract_section_info(self, text: str) -> Dict[str, str]:
        """
        Extract section number and heading from page text
        
        Looks for patterns like:
        - "1.2.3 Section Title"
        - "# 1.2.3 Section Title" (Markdown)
        - "Section 1.2.3: Title"
        
        Args:
            text: Page text content
            
        Returns:
            Dict with 'section_number' and 'section_title'
        """
        section_info = {"section_number": "", "section_title": ""}
        
        # Pattern 1: Markdown headings with section numbers (most common in pymupdf4llm)
        # Matches: "# 1.2.3 Cable Requirements" or "## 2.1 Specifications"
        pattern1 = r'^#{1,6}\s+(\d+(?:\.\d+)*)\s+(.+)$'
        
        # Pattern 2: Section number at start of line
        # Matches: "1.2.3 Cable Requirements" or "1.2.3. Cable Requirements"
        pattern2 = r'^(\d+(?:\.\d+)*)[\.:]?\s+([A-Z][^\n]{5,80})$'
        
        # Pattern 3: "Section X.Y:" or "Section X.Y -"
        pattern3 = r'Section\s+(\d+(?:\.\d+)*)\s*[:\-]?\s*(.+)$'
        
        lines = text.split('\n')[:10]  # Check first 10 lines only
        
        for line in lines:
            line = line.strip()
            
            # Try pattern 1 (Markdown headings)
            match = re.match(pattern1, line, re.MULTILINE)
            if match:
                section_info['section_number'] = match.group(1)
                section_info['section_title'] = match.group(2).strip()
                return section_info
            
            # Try pattern 2 (plain section numbers)
            match = re.match(pattern2, line)
            if match:
                section_info['section_number'] = match.group(1)
                section_info['section_title'] = match.group(2).strip()
                return section_info
            
            # Try pattern 3 ("Section X.Y")
            match = re.search(pattern3, line, re.IGNORECASE)
            if match:
                section_info['section_number'] = match.group(1)
                section_info['section_title'] = match.group(2).strip()
                return section_info
        
        return section_info
    
    def parse_pdf_with_tables(self, pdf_path: Path) -> List[Document]:
        """
        Read PDF and preserve tables in Markdown format
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of LlamaIndex Documents
        """
        logger.info(f"📖 Reading PDF: {pdf_path.name}")
        
        try:
            # Table-aware reading with PyMuPDF4LLM
            # This library converts tables to Markdown format
            md_text = pymupdf4llm.to_markdown(
                str(pdf_path),
                page_chunks=True,  # Chunk by page
                write_images=False,  # Skip images for now
                table_strategy="lines_strict"  # Use table lines
            )
            
            documents = []
            
            # Track last seen section for pages without explicit section
            last_section_num = ""
            last_section_title = ""
            
            # Create Document for each page
            for idx, page_data in enumerate(md_text):
                # PyMuPDF4LLM uses 0-based index, convert to 1-based page number
                page_num = idx + 1
                page_text = page_data.get("text", "")
                
                # Extract section information from page text
                section_info = self.extract_section_info(page_text)
                
                # Update tracking if new section found
                if section_info['section_number']:
                    last_section_num = section_info['section_number']
                    last_section_title = section_info['section_title']
                
                # Add metadata
                metadata = {
                    "file_name": pdf_path.name,
                    "file_path": str(pdf_path),
                    "page_label": str(page_num),
                    "page_number": page_num,
                    "source": pdf_path.stem,  # Use filename without extension
                    "section_number": last_section_num,
                    "section_title": last_section_title
                }
                
                doc = Document(
                    text=page_text,
                    metadata=metadata
                )
                
                documents.append(doc)
            
            logger.success(f"✅ Processed {len(documents)} pages: {pdf_path.name}")
            return documents
            
        except Exception as e:
            logger.error(f"❌ PDF reading error ({pdf_path.name}): {e}")
            return []
    
    def create_semantic_chunks(self, documents: List[Document]) -> List[Document]:
        """
        Semantically chunk documents
        Tables and paragraphs remain intact
        
        Args:
            documents: Raw document list
            
        Returns:
            Chunked nodes
        """
        logger.info("✂️  Creating semantic chunks...")
        
        # Use Semantic Splitter
        # This splits based on sentence similarity
        splitter = SemanticSplitterNodeParser(
            embed_model=Settings.embed_model,
            buffer_size=1,
            breakpoint_percentile_threshold=95  # Split when similarity drops below 95%
        )
        
        nodes = splitter.get_nodes_from_documents(documents, show_progress=True)
        
        logger.success(f"✅ {len(documents)} documents → {len(nodes)} nodes")
        return nodes
    
    def ingest_documents(self, force_reindex: bool = False) -> VectorStoreIndex:
        """
        Main ETL function: Read PDFs and load into database
        
        Args:
            force_reindex: If True, delete existing index and rebuild
            
        Returns:
            Created or loaded index
        """
        logger.info("🚀 Starting document ingestion...")
        
        # Check existing index
        existing_count = self.chroma_collection.count()
        
        if existing_count > 0 and not force_reindex:
            logger.info(f"ℹ️  Found existing index ({existing_count} nodes)")
            logger.info("💡 Use force_reindex=True to rebuild from scratch")
            
            # Load existing index
            storage_context = StorageContext.from_defaults(
                vector_store=self.vector_store
            )
            index = VectorStoreIndex.from_vector_store(
                self.vector_store,
                storage_context=storage_context
            )
            
            logger.success("✅ Existing index loaded")
            return index
        
        # Find PDF files
        pdf_files = validate_pdf_files()
        
        if not pdf_files:
            logger.error("❌ No PDF files found. Aborting.")
            return None
        
        # Read all PDFs
        all_documents = []
        for pdf_path in pdf_files:
            docs = self.parse_pdf_with_tables(pdf_path)
            all_documents.extend(docs)
        
        if not all_documents:
            logger.error("❌ No documents could be read!")
            return None
        
        logger.info(f"📚 Total {len(all_documents)} documents ready")
        
        # Create storage context
        storage_context = StorageContext.from_defaults(
            vector_store=self.vector_store
        )
        
        # Create index (embedding + write to database)
        logger.info("🔄 Creating vector index...")
        logger.info("⏱️  This may take several minutes (OpenAI API calls)...")
        
        index = VectorStoreIndex.from_documents(
            all_documents,
            storage_context=storage_context,
            show_progress=True
        )
        
        # Statistics
        final_count = self.chroma_collection.count()
        logger.success(f"✅ Indexing complete!")
        logger.info(f"📊 Total nodes: {final_count}")
        logger.info(f"📁 Database location: {self.settings.chroma_db_path}")
        
        return index
    
    def get_index_stats(self) -> dict:
        """Get information about current index"""
        try:
            count = self.chroma_collection.count()
            metadata = self.chroma_collection.metadata
            
            return {
                "collection_name": self.settings.collection_name,
                "total_nodes": count,
                "metadata": metadata,
                "db_path": self.settings.chroma_db_path
            }
        except Exception as e:
            logger.error(f"❌ Failed to get statistics: {e}")
            return {}


def main():
    """Direct execution for testing/debugging"""
    setup_logger("INFO")
    logger.info("=" * 60)
    logger.info("PyRAG - ETL Pipeline Test")
    logger.info("=" * 60)
    
    # Start ingestion
    ingestion = DocumentIngestion()
    
    # Show statistics
    stats = ingestion.get_index_stats()
    logger.info(f"📊 Current status: {stats}")
    
    # Index documents
    # Use force_reindex=True to start from scratch
    index = ingestion.ingest_documents(force_reindex=False)
    
    if index:
        logger.success("✅ ETL Pipeline completed successfully!")
    else:
        logger.error("❌ ETL Pipeline failed!")


if __name__ == "__main__":
    main()
