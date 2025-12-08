"""
PyRAG - ETL Pipeline (Data Loading and Indexing)

This module reads PDFs, extracts tables, and indexes them into ChromaDB.
"""

import os
import re
import threading
from pathlib import Path
from typing import List, Optional, Dict, Tuple, Callable
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
    HierarchicalNodeParser,
    get_leaf_nodes,
    get_root_nodes,
)
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.vector_stores.chroma import ChromaVectorStore

from loguru import logger
from src.utils import get_settings, setup_logger, validate_files, load_document_categories


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
    
    def parse_file(self, file_path: Path, categories: Optional[List[str]] = None) -> List[Document]:
        """
        Read file (PDF, TXT, MD) and convert to Documents
        
        Args:
            file_path: Path to file
            categories: List of document categories for metadata
            
        Returns:
            List of LlamaIndex Documents
        """
        logger.info(f"📖 Reading file: {file_path.name}")

        # Try to override categories/projects from stored per-file mapping (by filename)
        stored_mapping = load_document_categories()
        file_key = file_path.name
        file_project = None
        if file_key in stored_mapping:
            entry = stored_mapping[file_key]
            file_category = entry.get("category")
            file_project = entry.get("project")
            categories = [file_category] if file_category else None
            logger.info(f"   Using stored category for {file_key}: {file_category}")
            if file_project:
                logger.info(f"   Using stored project for {file_key}: {file_project}")
        elif categories:
            logger.info(f"   Categories: {', '.join(categories)}")
        
        try:
            documents = []
            
            # Handle PDF files
            if file_path.suffix.lower() == '.pdf':
                # Table-aware reading with PyMuPDF4LLM
                md_text = pymupdf4llm.to_markdown(
                    str(file_path),
                    page_chunks=True,
                    write_images=False,
                    table_strategy="lines_strict"
                )
                
                last_section_num = ""
                last_section_title = ""
                
                for idx, page_data in enumerate(md_text):
                    page_num = idx + 1
                    page_text = page_data.get("text", "")
                    section_info = self.extract_section_info(page_text)
                    
                    if section_info['section_number']:
                        last_section_num = section_info['section_number']
                        last_section_title = section_info['section_title']
                    
                    metadata = {
                        "file_name": file_path.name,
                        "document_name": file_path.stem,
                        "file_path": str(file_path),
                        "page_label": str(page_num),
                        "page_number": page_num,
                        "source": file_path.stem,
                        "section_number": last_section_num,
                        "section_title": last_section_title,
                        "categories": ", ".join(categories) if categories else "Uncategorized",
                        "project_name": file_project or "N/A",
                    }
                    
                    documents.append(Document(text=page_text, metadata=metadata))
            
            # Handle Text and Markdown files
            elif file_path.suffix.lower() in ['.txt', '.md']:
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                
                metadata = {
                    "file_name": file_path.name,
                    "document_name": file_path.stem,
                    "file_path": str(file_path),
                    "source": file_path.stem,
                    "categories": ", ".join(categories) if categories else "Uncategorized",
                    "project_name": file_project or "N/A",
                }
                
                documents.append(Document(text=text, metadata=metadata))
            
            else:
                logger.warning(f"⚠️ Unsupported file type: {file_path.suffix}")
                return []
            
            logger.success(f"✅ Processed {len(documents)} chunks/pages: {file_path.name}")
            return documents
            
        except Exception as e:
            logger.error(f"❌ File reading error ({file_path.name}): {e}")
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
    
    def ingest_documents(self, force_reindex: bool = False, categories: Optional[List[str]] = None, 
                        progress_callback: Optional[Callable[[str, float], None]] = None,
                        stop_event: Optional[threading.Event] = None) -> VectorStoreIndex:
        """
        Main ETL function: Read files and load into database
        
        Args:
            force_reindex: If True, delete existing index and rebuild
            categories: List of document categories
            progress_callback: Function to call with (status_message, progress_percent)
            stop_event: Event to check for cancellation
            
        Returns:
            Created or loaded index
        """
        logger.info("🚀 Starting document ingestion...")
        
        if categories:
            logger.info(f"📋 Document categories: {', '.join(categories)}")
        
        # Check existing index
        existing_count = self.chroma_collection.count()
        
        if existing_count > 0 and not force_reindex:
            logger.info(f"ℹ️  Found existing index ({existing_count} nodes)")
            if progress_callback:
                progress_callback("Existing index found. Loading...", 100)
            
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
        
        # Find files
        files = validate_files()
        
        if not files:
            logger.error("❌ No supported files found. Aborting.")
            if progress_callback:
                progress_callback("No files found!", 0)
            return None
        
        # Read all files with categories
        all_documents = []
        total_files = len(files)
        
        for idx, file_path in enumerate(files):
            # Check for cancellation
            if stop_event and stop_event.is_set():
                logger.warning("🛑 Ingestion cancelled by user")
                if progress_callback:
                    progress_callback("Cancelled by user.", 0)
                return None
                
            # Update progress
            if progress_callback:
                percent = int((idx / total_files) * 50)  # First 50% is reading
                progress_callback(f"Reading {file_path.name} ({idx+1}/{total_files})...", percent)
            
            docs = self.parse_file(file_path, categories=categories)
            all_documents.extend(docs)
        
        if not all_documents:
            logger.error("❌ No documents could be read!")
            if progress_callback:
                progress_callback("Failed to read documents.", 0)
            return None
        
        logger.info(f"📚 Total {len(all_documents)} documents ready")
        
        if progress_callback:
            progress_callback(f"Creating hierarchical index from {len(all_documents)} chunks...", 60)
            
        # Check cancellation before expensive indexing
        if stop_event and stop_event.is_set():
            return None
            
        # Create hierarchical node parser with parent-child relationships
        logger.info("🔄 Creating hierarchical chunks (parent-child relationships)...")
        logger.info("   This preserves context by keeping track of document sections")
        
        # Hierarchical chunking: Large parent chunks + Small child chunks
        node_parser = HierarchicalNodeParser.from_defaults(
            chunk_sizes=[2048, 1024, 512],  # Parent -> Child -> Grandchild
            chunk_overlap=200
        )
        
        # Parse documents into hierarchical nodes
        nodes = node_parser.get_nodes_from_documents(all_documents, show_progress=True)
        
        # Get leaf nodes (smallest chunks) for indexing
        leaf_nodes = get_leaf_nodes(nodes)
        
        logger.info(f"📊 Created {len(nodes)} total nodes ({len(leaf_nodes)} leaf nodes for indexing)")
        logger.info(f"   Each leaf node has parent context for better retrieval!")
        
        # Create storage context
        storage_context = StorageContext.from_defaults(
            vector_store=self.vector_store
        )
        
        # Create index from leaf nodes (embedding + write to database)
        logger.info("🔄 Creating vector index with hierarchical structure...")
        logger.info("⏱️  This may take several minutes (OpenAI API calls)...")
        
        index = VectorStoreIndex(
            leaf_nodes,
            storage_context=storage_context,
            show_progress=True
        )
        
        if progress_callback:
            progress_callback("Indexing complete!", 100)
            
        # Statistics
        final_count = self.chroma_collection.count()
        logger.success(f"✅ Indexing complete!")
        logger.info(f"📊 Total nodes: {final_count}")
        logger.info(f"📁 Database location: {self.settings.chroma_db_path}")
        
        return index
    
    def ingest_single_file(self, file_path: str, category: str = "Uncategorized", 
                          project: str = "N/A", standard_no: str = "", 
                          date: str = "", description: str = "") -> dict:
        """
        Index a single file into the existing collection with hierarchical chunking
        
        Args:
            file_path: Path to the file to index
            category: Document category
            project: Project name
            standard_no: Standard number (e.g., IEC 60364-5-52)
            date: Document date (e.g., 2024-03)
            description: Brief description of the document
            
        Returns:
            Dict with success status and chunk count: {"success": bool, "chunks": int, "leaf_chunks": int}
        """
        try:
            path = Path(file_path)
            logger.info(f"📄 Indexing single file: {path.name}")
            
            # Parse file with category
            docs = self.parse_file(path, categories=[category])
            
            if not docs:
                logger.error(f"❌ Failed to parse {path.name}")
                return {"success": False, "chunks": 0, "leaf_chunks": 0}
            
            # Add metadata to all documents
            for doc in docs:
                doc.metadata["project_name"] = project
                if standard_no:
                    doc.metadata["standard_no"] = standard_no
                if date:
                    doc.metadata["date"] = date
                if description:
                    doc.metadata["description"] = description
            
            original_count = len(docs)
            logger.info(f"📚 Parsed {original_count} pages from {path.name}")
            
            # Create hierarchical chunks (same as bulk ingestion)
            logger.info("🔄 Creating hierarchical chunks...")
            node_parser = HierarchicalNodeParser.from_defaults(
                chunk_sizes=[2048, 1024, 512],  # Parent -> Child -> Grandchild
                chunk_overlap=200
            )
            
            # Parse into hierarchical nodes
            nodes = node_parser.get_nodes_from_documents(docs, show_progress=False)
            leaf_nodes = get_leaf_nodes(nodes)
            
            logger.info(f"📊 Created {len(nodes)} total nodes ({len(leaf_nodes)} leaf nodes)")
            
            # Create storage context
            storage_context = StorageContext.from_defaults(
                vector_store=self.vector_store
            )
            
            # Load existing index
            existing_index = VectorStoreIndex.from_vector_store(
                self.vector_store,
                storage_context=storage_context
            )
            
            # Insert leaf nodes (with parent context) into existing index
            logger.info("🔄 Adding hierarchical nodes to vector index...")
            for node in leaf_nodes:
                existing_index.insert_nodes([node])
            
            logger.success(f"✅ Successfully indexed {path.name}")
            logger.info(f"   Original pages: {original_count}")
            logger.info(f"   Hierarchical nodes: {len(nodes)}")
            logger.info(f"   Indexed leaf nodes: {len(leaf_nodes)}")
            
            return {
                "success": True, 
                "chunks": len(nodes),
                "leaf_chunks": len(leaf_nodes)
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to index {file_path}: {e}")
            return {"success": False, "chunks": 0, "leaf_chunks": 0}
    
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
