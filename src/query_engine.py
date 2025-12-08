"""
PyRAG - Query Engine (Search and Answer Engine)

Intelligent Q&A with hybrid search (Semantic + BM25) and reranking.
"""

from typing import List, Optional, Dict
import chromadb
from chromadb.config import Settings as ChromaSettings
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from llama_index.core import (
    VectorStoreIndex,
    StorageContext,
    Settings,
    get_response_synthesizer,
)
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.core.indices.postprocessor import MetadataReplacementPostProcessor
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.llms.deepseek import DeepSeek
from llama_index.vector_stores.chroma import ChromaVectorStore

from loguru import logger
from src.utils import get_settings, setup_logger, create_system_prompt
from src.semantic_cache import get_cache
from src.query_expansion import get_expander
from src.feedback_manager import get_feedback_manager
from src.feedback_postprocessor import get_feedback_postprocessor
from src.query_analyzer import get_query_analyzer
from src.bm25_searcher import get_bm25_searcher
from src.graph_retriever import get_graph_retriever
from src.response_cache import get_response_cache


class QueryEngine:
    """
    Processes user queries and generates answers
    """
    
    def __init__(self, use_cache: bool = True, use_expansion: bool = True, use_response_cache: bool = True):
        self.settings = get_settings()
        self.use_cache = use_cache
        self.use_expansion = use_expansion
        self.use_response_cache = use_response_cache
        self.cache = get_cache() if use_cache else None
        self.expander = get_expander() if use_expansion else None
        self.response_cache = get_response_cache() if use_response_cache else None
        self.feedback_manager = get_feedback_manager()
        self.query_analyzer = get_query_analyzer()
        self.bm25_searcher = get_bm25_searcher()
        self.graph_retriever = get_graph_retriever()
        self._setup_llama_index()
        self._load_index()
        self._index_bm25()  # Index documents for keyword search
        self._setup_query_engine()
    
    def _setup_llama_index(self):
        """Configure LlamaIndex global settings"""
        logger.info("🔧 Configuring Query Engine...")
        
        # Get system prompt
        system_prompt = create_system_prompt()
        
        # Determine which LLM to use based on model name
        if "deepseek" in self.settings.llm_model.lower():
            # DeepSeek native integration
            logger.info("📡 Using DeepSeek API (90% cheaper!)...")
            Settings.llm = DeepSeek(
                model=self.settings.llm_model,
                temperature=self.settings.llm_temperature,
                api_key=self.settings.deepseek_api_key,
                system_prompt=system_prompt
            )
        else:
            # Default to OpenAI
            logger.info("📡 Using OpenAI API...")
            Settings.llm = OpenAI(
                model=self.settings.llm_model,
                temperature=self.settings.llm_temperature,
                api_key=self.settings.openai_api_key,
                system_prompt=system_prompt
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
            self.chroma_collection = chroma_client.get_collection(
                name=collection_name
            )
            
            # Vector store
            vector_store = ChromaVectorStore(
                chroma_collection=self.chroma_collection
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
            
            node_count = self.chroma_collection.count()
            logger.success(f"✅ Index loaded ({node_count} nodes)")
            
        except Exception as e:
            logger.error(f"❌ Failed to load index: {e}")
            logger.warning("💡 Run ingestion first: python main.py ingest")
            raise
    
    def _index_bm25(self):
        """Index all documents for BM25 keyword search"""
        logger.info("🔑 Indexing documents for BM25 keyword search...")
        
        try:
            # Get all documents from ChromaDB
            all_docs = self.chroma_collection.get()
            
            if not all_docs or not all_docs.get('documents'):
                logger.warning("⚠️ No documents found for BM25 indexing")
                return
            
            # Prepare documents for BM25
            bm25_docs = []
            for i, doc_text in enumerate(all_docs['documents']):
                metadata = all_docs['metadatas'][i] if all_docs.get('metadatas') else {}
                bm25_docs.append({
                    'text': doc_text,
                    'metadata': metadata,
                    'id': all_docs['ids'][i] if all_docs.get('ids') else str(i)
                })
            
            # Index documents
            self.bm25_searcher.index_documents(bm25_docs)
            logger.success(f"✅ BM25 index ready with {len(bm25_docs)} documents")
            
        except Exception as e:
            logger.error(f"❌ Failed to index BM25: {e}")
            logger.warning("⚠️ BM25 search will not be available")
    
    def _setup_query_engine(self):
        """Configure query engine (Retriever + Synthesizer) with hierarchical context"""
        logger.info("🔧 Setting up query engine with hierarchical retrieval...")
        
        # Retriever: Fetches relevant nodes from database
        retriever = VectorIndexRetriever(
            index=self.index,
            similarity_top_k=15,  # Fetch more candidates for reranking
        )
        
        # Postprocessors:
        # 1. Feedback-based re-ranking (active learning)
        # 2. Replace child nodes with parent context (hierarchical chunking)
        node_postprocessors = [
            get_feedback_postprocessor(
                boost_factor=0.15,  # 15% boost for positive feedback
                penalty_factor=0.10  # 10% penalty for negative feedback
            ),
            MetadataReplacementPostProcessor(
                target_metadata_key="window"  # Replace with parent context
            )
        ]
        
        # Response Synthesizer: Combines nodes and sends to LLM
        response_synthesizer = get_response_synthesizer(
            response_mode="compact",
            structured_answer_filtering=False  # Don't filter, just answer
        )
        
        # Query Engine: With hierarchical context
        self.query_engine = RetrieverQueryEngine(
            retriever=retriever,
            response_synthesizer=response_synthesizer,
            node_postprocessors=node_postprocessors
        )
        
        logger.success("✅ Query engine ready with hierarchical context retrieval")
    
    def _expand_query(self, query: str) -> str:
        """
        Expand query with engineering synonyms for better retrieval
        """
        expansions = {
            "cable": "cable conductor wire",
            "impedance": "impedance resistance ohm",
            "voltage": "voltage potential V",
            "current": "current ampere amp A",
            "maximum": "maximum max limit",
            "minimum": "minimum min",
            "fire": "fire safety emergency evacuation",
            "alarm": "alarm detection warning system",
            "protection": "protection safety guard",
            "circuit": "circuit loop branch",
            "breaker": "breaker MCB MCCB RCD",
            "standard": "standard specification requirement code",
        }
        
        query_lower = query.lower()
        for key, expansion in expansions.items():
            if key in query_lower and expansion not in query_lower:
                # Add expansion but keep original query intact
                query = f"{query} ({expansion})"
                break  # Only expand once to avoid noise
        
        return query
    
    def query(
        self, 
        question: str,
        return_sources: bool = True,
        stream: bool = False,
        document_filter: Optional[str] = None,
        category_filter: Optional[str] = None,
        filters: Optional[Dict] = None
    ) -> Dict:
        """
        Main query function with optional filtering
        
        Args:
            question: User's question
            return_sources: Return source documents?
            stream: Streaming mode (currently False)
            document_filter: Filter by specific document name (e.g., "IS10101")
            category_filter: Filter by category (e.g., "Standard")
            filters: Dictionary of filters {'document': 'name', 'category': 'cat', 'project': 'proj'}
            
        Returns:
            {
                "answer": str,
                "sources": List[Dict],
                "metadata": Dict
            }
        """
        # Handle new filters dict format
        if filters:
            document_filter = filters.get('document', document_filter)
            category_filter = filters.get('category', category_filter)
            project_filter = filters.get('project')
        else:
            project_filter = None
        
        logger.info(f"🔍 Query: '{question}'")
        
        # Check response cache first (works with filters)
        if self.use_response_cache and self.response_cache:
            cache_filters = {
                'document': document_filter,
                'category': category_filter,
                'project': project_filter
            }
            cached_response = self.response_cache.get(question, cache_filters)
            if cached_response:
                logger.success(f"⚡ RESPONSE CACHE HIT! (age: {cached_response['metadata'].get('cache_age_seconds', 0):.0f}s)")
                return cached_response
        
        # Analyze query to determine optimal retrieval strategy
        query_analysis = self.query_analyzer.analyze(question)
        logger.info(f"   🧠 Intent: {query_analysis['intent'].value}")
        logger.info(f"   ⚖️ Weights: {query_analysis['weights']}")
        
        if document_filter:
            logger.info(f"   📄 Document filter: {document_filter}")
        if category_filter:
            logger.info(f"   🏷️ Category filter: {category_filter}")
        if project_filter:
            logger.info(f"   📁 Project filter: {project_filter}")
        
        # Check semantic cache (only if no filters applied)
        if self.use_cache and self.cache and not any([document_filter, category_filter, project_filter]):
            cached_result = self.cache.get(question)
            if cached_result:
                logger.success(f"⚡ CACHE HIT! Returning cached answer (similarity: {cached_result['similarity']:.3f})")
                return {
                    "response": cached_result["answer"],
                    "sources": cached_result.get("sources", []),
                    "metadata": {
                        "question": question,
                        "model": self.settings.llm_model,
                        "from_cache": True,
                        "cache_similarity": cached_result["similarity"],
                        "original_query": cached_result["query"]
                    }
                }
        
        # Query expansion: Add MEP-specific synonyms for better recall
        if self.use_expansion and self.expander:
            expanded_query = self.expander.expand(question)
        else:
            expanded_query = self._expand_query(question)  # Legacy expansion
        
        if expanded_query != question:
            logger.info(f"   ✨ Expanded: '{question}' → '{expanded_query}'")
        
        try:
            # Build metadata filters if provided
            from llama_index.core.vector_stores import MetadataFilters, MetadataFilter, FilterOperator
            
            metadata_filter_list = []
            if document_filter:
                # Use file_name with exact match (EQ operator)
                # document_filter should be the exact file_name value
                metadata_filter_list.append(
                    MetadataFilter(key="file_name", value=document_filter, operator=FilterOperator.EQ)
                )
            
            if category_filter:
                # Category filter - use EQ for exact match
                metadata_filter_list.append(MetadataFilter(key="categories", value=category_filter, operator=FilterOperator.EQ))
            
            if project_filter:
                metadata_filter_list.append(MetadataFilter(key="project_name", value=project_filter, operator=FilterOperator.EQ))
            
            # Hybrid Search: Parallel execution of semantic + keyword + graph
            query_to_use = expanded_query
            start_time = time.time()
            
            # Prepare semantic retriever
            if metadata_filter_list:
                metadata_filters = MetadataFilters(filters=metadata_filter_list)
                semantic_retriever = VectorIndexRetriever(
                    index=self.index,
                    similarity_top_k=15,  # More candidates
                    filters=metadata_filters
                )
            else:
                semantic_retriever = VectorIndexRetriever(
                    index=self.index,
                    similarity_top_k=15
                )
            
            # Step 1: Execute searches in parallel
            semantic_nodes = []
            bm25_results = []
            graph_info = None
            
            with ThreadPoolExecutor(max_workers=3) as executor:
                # Submit parallel tasks
                future_semantic = executor.submit(semantic_retriever.retrieve, query_to_use)
                future_bm25 = executor.submit(self.bm25_searcher.search, query_to_use, 15)
                future_graph = None
                if self.graph_retriever and self.graph_retriever.enabled:
                    future_graph = executor.submit(
                        self.graph_retriever.get_cross_references,
                        query_to_use,
                        2  # max_hops
                    )
                
                # Collect results as they complete
                for future in as_completed([f for f in [future_semantic, future_bm25, future_graph] if f]):
                    if future == future_semantic:
                        semantic_nodes = future.result()
                        logger.info(f"   🔍 Semantic search: {len(semantic_nodes)} nodes")
                    elif future == future_bm25:
                        bm25_results = future.result()
                        logger.info(f"   🔑 BM25 search: {len(bm25_results)} nodes")
                    elif future == future_graph:
                        graph_data = future.result()
                        if graph_data and graph_data.get('references'):
                            graph_info = graph_data
                            logger.info(f"   🕸️ Graph: {len(graph_info['references'])} cross-references found")
            
            parallel_time = time.time() - start_time
            logger.info(f"   ⚡ Parallel retrieval: {parallel_time:.3f}s")
            
            # Step 2: Adaptive blending based on query analysis
            blended_nodes = self._blend_results(
                semantic_nodes=semantic_nodes,
                bm25_results=bm25_results,
                weights=query_analysis['weights'],
                query=query_to_use
            )
            
            # Step 5: Create query engine with blended results
            response_synthesizer = get_response_synthesizer(
                response_mode="compact",
                structured_answer_filtering=False
            )
            
            # Create custom retriever from blended nodes
            from llama_index.core.schema import QueryBundle
            query_bundle = QueryBundle(query_str=query_to_use)
            
            # Get LLM response with blended context
            response = response_synthesizer.synthesize(
                query=query_bundle,
                nodes=blended_nodes[:10]  # Top 10 after blending
            )
            
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
                "response": answer_text,
                "sources": [],
                "metadata": {
                    "question": question,
                    "model": self.settings.llm_model,
                    "query_intent": query_analysis['intent'].value if hasattr(query_analysis['intent'], 'value') else str(query_analysis['intent']),
                    "query_weights": query_analysis['weights'],
                    "retrieval_info": {
                        "semantic_nodes": len(semantic_nodes),
                        "bm25_nodes": len(bm25_results),
                        "blended_nodes": len(blended_nodes)
                    },
                    "graph_info": graph_info if graph_info else None
                }
            }
            
            # Add source documents (parallel processing)
            if return_sources and hasattr(response, 'source_nodes'):
                def process_source(idx_node):
                    idx, node = idx_node
                    metadata = node.metadata
                    doc_name = metadata.get('document_name', metadata.get('file_name', 'Unknown'))
                    page_num = metadata.get('page_label', metadata.get('page', 'N/A'))
                    
                    return {
                        "rank": idx,
                        "document": doc_name,
                        "page": page_num,
                        "standard_no": metadata.get('standard_no', ''),
                        "date": metadata.get('date', ''),
                        "description": metadata.get('description', ''),
                        "text": node.text[:300] + "...",
                        "score": node.score if hasattr(node, 'score') else None,
                        "metadata": metadata
                    }
                
                # Process sources in parallel
                with ThreadPoolExecutor(max_workers=4) as executor:
                    sources = list(executor.map(
                        process_source,
                        enumerate(response.source_nodes, 1)
                    ))
                
                result["sources"] = sources
                logger.info(f"📚 Used {len(result['sources'])} source document(s)")
            
            # Cache the semantic result (only if no filters applied)
            if self.use_cache and self.cache and not any([document_filter, category_filter, project_filter]):
                self.cache.set(
                    query=question,
                    answer=answer_text,
                    sources=result.get("sources")
                )
            
            # Cache the complete response (works with filters)
            if self.use_response_cache and self.response_cache:
                cache_filters = {
                    'document': document_filter,
                    'category': category_filter,
                    'project': project_filter
                }
                self.response_cache.set(question, result, cache_filters)
            
            logger.success("✅ Answer generated")
            return result
            
        except Exception as e:
            logger.error(f"❌ Query error: {e}")
            return {
                "response": f"Sorry, an error occurred: {str(e)}",
                "sources": [],
                "metadata": {"error": str(e)},
                "error": str(e)
            }
    
    def switch_model(self, model_name: str):
        """
        Dynamically switch LLM model
        
        Args:
            model_name: Model name (e.g., 'deepseek-chat', 'gpt-4-turbo-preview', 'gpt-3.5-turbo')
        """
        logger.info(f"🔄 Switching to model: {model_name}")
        
        try:
            # Update settings
            self.settings.llm_model = model_name
            
            # Determine which LLM to use
            if "deepseek" in model_name.lower():
                logger.info("📡 Configuring DeepSeek API...")
                Settings.llm = DeepSeek(
                    model=model_name,
                    temperature=self.settings.llm_temperature,
                    api_key=self.settings.deepseek_api_key
                )
            else:
                logger.info("📡 Configuring OpenAI API...")
                Settings.llm = OpenAI(
                    model=model_name,
                    temperature=self.settings.llm_temperature,
                    api_key=self.settings.openai_api_key
                )
            
            # Reconfigure query engine with new LLM
            self._setup_query_engine()
            
            logger.success(f"✅ Successfully switched to {model_name}")
            
        except Exception as e:
            logger.error(f"❌ Failed to switch model: {e}")
            raise
    
    def _blend_results(
        self,
        semantic_nodes: List,
        bm25_results: List[Dict],
        weights: Dict[str, float],
        query: str
    ) -> List:
        """
        Blend semantic and BM25 results using adaptive weights
        
        Args:
            semantic_nodes: Nodes from semantic search (NodeWithScore)
            bm25_results: Results from BM25 search
            weights: Weight dict from query analysis
            query: Original query
            
        Returns:
            Blended and re-ranked nodes
        """
        from llama_index.core.schema import NodeWithScore
        
        # Get weights
        semantic_weight = weights.get('semantic', 0.5)
        keyword_weight = weights.get('keyword', 0.3)
        
        logger.info(f"   ⚖️ Blending: semantic={semantic_weight:.2f}, keyword={keyword_weight:.2f}")
        
        # Create a mapping of node_id -> combined_score
        node_scores = {}
        
        # Add semantic scores (already normalized 0-1)
        for node in semantic_nodes:
            node_id = node.node.id_
            node_scores[node_id] = {
                'node': node,
                'semantic_score': node.score,
                'keyword_score': 0.0
            }
        
        # Normalize BM25 scores to 0-1 range
        if bm25_results:
            max_bm25 = max(r['score'] for r in bm25_results)
            min_bm25 = min(r['score'] for r in bm25_results)
            bm25_range = max_bm25 - min_bm25 if max_bm25 > min_bm25 else 1.0
            
            for result in bm25_results:
                doc_id = result['doc'].get('id')
                normalized_bm25 = (result['score'] - min_bm25) / bm25_range
                
                if doc_id in node_scores:
                    # Update existing node
                    node_scores[doc_id]['keyword_score'] = normalized_bm25
                else:
                    # Create new node from BM25 (not in semantic results)
                    # Skip these for now - focus on semantic results
                    pass
        
        # Calculate final blended scores
        blended_nodes = []
        for node_id, scores in node_scores.items():
            semantic_score = scores['semantic_score']
            keyword_score = scores['keyword_score']
            
            # Weighted combination
            final_score = (semantic_weight * semantic_score + 
                          keyword_weight * keyword_score)
            
            # Create new NodeWithScore with blended score
            blended_node = NodeWithScore(
                node=scores['node'].node,
                score=final_score
            )
            blended_nodes.append(blended_node)
        
        # Sort by final blended score
        blended_nodes.sort(key=lambda x: x.score, reverse=True)
        
        if blended_nodes:
            logger.info(f"   🎯 Blended to {len(blended_nodes)} nodes, top score: {blended_nodes[0].score:.3f}")
        
        return blended_nodes
    
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
    
    def get_stats(self) -> Dict:
        """
        Get statistics about the vector database
        
        Returns:
            Dictionary with stats (total_nodes, db_path, collection_name)
        """
        try:
            # Get ChromaDB collection
            chroma_client = chromadb.PersistentClient(
                path=self.settings.chroma_db_path,
                settings=ChromaSettings(anonymized_telemetry=False)
            )
            
            collection_name = self.settings.get_collection_name()
            
            try:
                chroma_collection = chroma_client.get_collection(name=collection_name)
                node_count = chroma_collection.count()
            except:
                node_count = 0
            
            return {
                'total_nodes': node_count,
                'db_path': self.settings.chroma_db_path,
                'collection_name': collection_name
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {
                'total_nodes': 0,
                'db_path': self.settings.chroma_db_path,
                'collection_name': self.settings.get_collection_name()
            }
    
    def get_cache_stats(self) -> Dict:
        """Get semantic cache statistics"""
        if self.cache:
            return self.cache.get_stats()
        return {"error": "Cache not enabled"}
    
    def clear_cache(self):
        """Clear semantic cache"""
        if self.cache:
            self.cache.clear()
            logger.info("🗑️ Cache cleared successfully")
        else:
            logger.warning("Cache not enabled")
    
    def cleanup_cache(self):
        """Cleanup expired cache entries"""
        if self.cache:
            deleted = self.cache.cleanup_expired()
            logger.info(f"🧹 Cleaned up {deleted} expired cache entries")
            return deleted
        return 0
    
    def add_feedback(self, query: str, response: str, feedback_type: str, 
                    sources: List[Dict], comment: Optional[str] = None) -> int:
        """
        Add user feedback for active learning
        
        Args:
            query: User query
            response: AI response
            feedback_type: 'positive' or 'negative'
            sources: List of source documents
            comment: Optional user comment
            
        Returns:
            Feedback ID
        """
        return self.feedback_manager.add_feedback(
            query=query,
            response=response,
            feedback_type=feedback_type,
            sources=sources,
            comment=comment
        )
    
    def get_feedback_stats(self) -> Dict:
        """Get feedback statistics"""
        return self.feedback_manager.get_statistics()
    
    def get_recent_feedback(self, limit: int = 10) -> List[Dict]:
        """Get recent feedback entries"""
        return self.feedback_manager.get_recent_feedback(limit)


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
