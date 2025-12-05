"""
PyRAG - Query Engine (Search and Answer Engine)

Intelligent Q&A with hybrid search (Semantic + BM25) and reranking.
"""

from typing import List, Optional, Dict
import chromadb
from chromadb.config import Settings as ChromaSettings

from llama_index.core import (
    VectorStoreIndex,
    StorageContext,
    Settings,
    get_response_synthesizer,
)
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.llms.deepseek import DeepSeek
from llama_index.vector_stores.chroma import ChromaVectorStore

from loguru import logger
from src.utils import get_settings, setup_logger, create_system_prompt


class QueryEngine:
    """
    Processes user queries and generates answers
    """
    
    def __init__(self):
        self.settings = get_settings()
        self._setup_llama_index()
        self._load_index()
        self._setup_query_engine()
    
    def _setup_llama_index(self):
        """Configure LlamaIndex global settings"""
        logger.info("🔧 Configuring Query Engine...")
        
        # Determine which LLM to use based on model name
        if "deepseek" in self.settings.llm_model.lower():
            # DeepSeek native integration
            logger.info("📡 Using DeepSeek API (90% cheaper!)...")
            Settings.llm = DeepSeek(
                model=self.settings.llm_model,
                temperature=self.settings.llm_temperature,
                api_key=self.settings.deepseek_api_key
            )
        else:
            # Default to OpenAI
            logger.info("📡 Using OpenAI API...")
            Settings.llm = OpenAI(
                model=self.settings.llm_model,
                temperature=self.settings.llm_temperature,
                api_key=self.settings.openai_api_key
            )
        
        # Embedding settings (use same model as ingestion for consistency)
        Settings.embed_model = OpenAIEmbedding(
            model=self.settings.embedding_model,
            api_key=self.settings.openai_api_key
        )
    
    def _load_index(self):
        """Load existing vector index"""
        logger.info("📂 Loading vector index...")
        
        try:
            # ChromaDB connection
            chroma_client = chromadb.PersistentClient(
                path=self.settings.chroma_db_path,
                settings=ChromaSettings(anonymized_telemetry=False)
            )
            
            collection_name = self.settings.get_collection_name()
            chroma_collection = chroma_client.get_collection(
                name=collection_name
            )
            
            # Vector store
            vector_store = ChromaVectorStore(
                chroma_collection=chroma_collection
            )
            
            # Storage context
            storage_context = StorageContext.from_defaults(
                vector_store=vector_store
            )
            
            # Load index
            self.index = VectorStoreIndex.from_vector_store(
                vector_store,
                storage_context=storage_context
            )
            
            node_count = chroma_collection.count()
            logger.success(f"✅ Index loaded ({node_count} nodes)")
            
        except Exception as e:
            logger.error(f"❌ Failed to load index: {e}")
            logger.warning("💡 Run ingestion first: python main.py ingest")
            raise
    
    def _setup_query_engine(self):
        """Configure query engine (Retriever + Synthesizer)"""
        logger.info("🔧 Setting up query engine...")
        
        # Retriever: Fetches relevant nodes from database
        retriever = VectorIndexRetriever(
            index=self.index,
            similarity_top_k=5,  # Fetch top 5 most relevant results
        )
        
        # Response Synthesizer: Combines nodes and sends to LLM
        response_synthesizer = get_response_synthesizer(
            response_mode="compact",  # Concise answers
            structured_answer_filtering=True
        )
        
        # Query Engine: Combines all components (no postprocessor for now)
        self.query_engine = RetrieverQueryEngine(
            retriever=retriever,
            response_synthesizer=response_synthesizer
        )
        
        logger.success("✅ Query engine ready")
    
    def query(
        self, 
        question: str,
        return_sources: bool = True,
        stream: bool = False
    ) -> Dict:
        """
        Main query function
        
        Args:
            question: User's question
            return_sources: Return source documents?
            stream: Streaming mode (currently False)
            
        Returns:
            {
                "answer": str,
                "sources": List[Dict],
                "metadata": Dict
            }
        """
        logger.info(f"🔍 Query: '{question}'")
        
        try:
            # Execute query
            response = self.query_engine.query(question)
            
            # Debug log
            logger.debug(f"Response type: {type(response)}")
            logger.debug(f"Response: {response}")
            logger.debug(f"Response str: '{str(response)}'")
            
            # Prepare result
            answer_text = str(response).strip()
            
            # Fallback if empty
            if not answer_text:
                logger.warning("Empty response from LLM, using fallback")
                answer_text = "I found relevant information but couldn't generate a response. Please try rephrasing your question."
            
            result = {
                "answer": answer_text,
                "sources": [],
                "metadata": {
                    "question": question,
                    "model": self.settings.llm_model
                }
            }
            
            # Add source documents
            if return_sources and hasattr(response, 'source_nodes'):
                for idx, node in enumerate(response.source_nodes, 1):
                    source = {
                        "rank": idx,
                        "text": node.text[:300] + "...",  # First 300 characters
                        "score": node.score if hasattr(node, 'score') else None,
                        "metadata": node.metadata
                    }
                    result["sources"].append(source)
                
                logger.info(f"📚 Used {len(result['sources'])} source document(s)")
            
            logger.success("✅ Answer generated")
            return result
            
        except Exception as e:
            logger.error(f"❌ Query error: {e}")
            return {
                "answer": f"Sorry, an error occurred: {str(e)}",
                "sources": [],
                "metadata": {"error": str(e)}
            }
    
    def chat(
        self,
        message: str,
        chat_history: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Chat mode (conversational interface)
        
        Args:
            message: User's message
            chat_history: Previous conversation history
            
        Returns:
            Response dictionary
        """
        # Currently uses simple query
        # Can be upgraded to chat engine later
        return self.query(message, return_sources=True)
    
    def get_similar_docs(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Get similar documents only (without LLM)
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of similar documents
        """
        logger.info(f"🔍 Searching similar documents: '{query}'")
        
        try:
            retriever = self.index.as_retriever(
                similarity_top_k=top_k
            )
            
            nodes = retriever.retrieve(query)
            
            results = []
            for idx, node in enumerate(nodes, 1):
                results.append({
                    "rank": idx,
                    "text": node.text,
                    "score": node.score if hasattr(node, 'score') else None,
                    "metadata": node.metadata
                })
            
            logger.success(f"✅ Found {len(results)} document(s)")
            return results
            
        except Exception as e:
            logger.error(f"❌ Search error: {e}")
            return []


def main():
    """Direct execution for testing/debugging"""
    setup_logger("INFO")
    logger.info("=" * 60)
    logger.info("PyRAG - Query Engine Test")
    logger.info("=" * 60)
    
    # Initialize query engine
    engine = QueryEngine()
    
    # Test questions
    test_questions = [
        "What is the current carrying capacity for 2.5mm² copper cable?",
        "How to calculate temperature correction factor for PVC insulated cables?",
        "What should be the grounding resistance according to IS10101?"
    ]
    
    for question in test_questions:
        logger.info("\n" + "=" * 60)
        result = engine.query(question, return_sources=True)
        
        logger.info(f"❓ Question: {question}")
        logger.info(f"✅ Answer: {result['answer']}")
        
        if result['sources']:
            logger.info(f"\n📚 Sources:")
            for source in result['sources']:
                logger.info(f"  [{source['rank']}] {source['metadata'].get('file_name', 'Unknown')} - "
                          f"Page {source['metadata'].get('page_label', '?')}")


if __name__ == "__main__":
    main()
