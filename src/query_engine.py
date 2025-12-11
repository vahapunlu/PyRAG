"""
PyRAG - Query Engine (Search and Answer Engine)

Intelligent Q&A with hybrid search (Semantic + BM25) and reranking.
"""

from typing import List, Optional, Dict
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
from llama_index.llms.deepseek import DeepSeek
from llama_index.vector_stores.qdrant import QdrantVectorStore
import qdrant_client

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
from src.query_history import get_query_history
from src.export_manager import get_export_manager
from src.graph_visualizer import get_graph_visualizer
from src.hybrid_search import get_hybrid_search_engine, HybridSearchEngine
from src.graph_rag import get_graph_rag, GraphRAG
from src.error_handler import (
    get_error_handler, 
    ErrorCategory, 
    ErrorSeverity, 
    with_retry, 
    with_fallback, 
    safe_execute,
    validate_input
)
from src.health_check import get_health_check, HealthStatus


class QueryEngine:
    """
    Processes user queries and generates answers
    """
    
    def __init__(self, use_cache: bool = True, use_expansion: bool = True, use_response_cache: bool = True):
        self.settings = get_settings()
        self.use_cache = use_cache
        self.use_expansion = use_expansion
        self.use_response_cache = use_response_cache
        self.error_handler = get_error_handler()
        
        # Initialize components with error handling
        self.cache = safe_execute(get_cache, error_handler=self.error_handler, 
                                  category=ErrorCategory.DATABASE) if use_cache else None
        self.expander = safe_execute(get_expander, error_handler=self.error_handler,
                                    category=ErrorCategory.PROCESSING) if use_expansion else None
        self.response_cache = safe_execute(get_response_cache, error_handler=self.error_handler,
                                          category=ErrorCategory.DATABASE) if use_response_cache else None
        self.feedback_manager = safe_execute(get_feedback_manager, error_handler=self.error_handler,
                                            category=ErrorCategory.DATABASE)
        self.query_analyzer = safe_execute(get_query_analyzer, error_handler=self.error_handler,
                                          category=ErrorCategory.PROCESSING)
        self.bm25_searcher = safe_execute(get_bm25_searcher, error_handler=self.error_handler,
                                         category=ErrorCategory.PROCESSING)
        self.graph_retriever = safe_execute(get_graph_retriever, error_handler=self.error_handler,
                                           category=ErrorCategory.NETWORK)
        self.query_history = safe_execute(get_query_history, error_handler=self.error_handler,
                                         category=ErrorCategory.DATABASE)
        self.export_manager = safe_execute(get_export_manager, error_handler=self.error_handler,
                                          category=ErrorCategory.PROCESSING)
        # Graph visualizer initialized on-demand (requires Neo4j credentials)
        self.graph_visualizer = None
        
        # Health monitoring
        self.health_check = get_health_check()
        self._register_health_checks()
        
        self._setup_llama_index()
        self._load_index()
        self._index_bm25()  # Index documents for keyword search
        self._setup_query_engine()
    
    def _register_health_checks(self):
        """Register component health checks"""
        # Register cache
        if self.cache:
            self.health_check.register_component('semantic_cache', 
                lambda: self.cache is not None)
        
        # Register response cache
        if self.response_cache:
            self.health_check.register_component('response_cache',
                lambda: self.response_cache is not None)
        
        # Register BM25
        if self.bm25_searcher:
            self.health_check.register_component('bm25_search',
                lambda: self.bm25_searcher is not None)
        
        # Register graph
        if self.graph_retriever and self.graph_retriever.enabled:
            self.health_check.register_component('graph_retriever',
                lambda: self.graph_retriever.enabled)

    def close(self):
        """Close connections and release resources"""
        try:
            if hasattr(self, 'client') and self.client:
                self.client.close()
                logger.info("🔒 Qdrant client closed")
        except Exception as e:
            logger.warning(f"Error closing Qdrant client: {e}")
    
    def _setup_llama_index(self):
        """Configure LlamaIndex global settings"""
        logger.info("🔧 Configuring Query Engine...")
        
        try:
            # Get system prompt
            system_prompt = create_system_prompt()
            
            # Use DeepSeek API
            logger.info("📡 Using DeepSeek API...")
            Settings.llm = DeepSeek(
                model=self.settings.llm_model,
                temperature=self.settings.llm_temperature,
                api_key=self.settings.deepseek_api_key,
                system_prompt=system_prompt
            )
            
            # Embedding settings (use same model as ingestion for consistency)
            Settings.embed_model = OpenAIEmbedding(
                model=self.settings.embedding_model,
                api_key=self.settings.openai_api_key
            )
            
        except Exception as e:
            self.error_handler.log_error(e, ErrorCategory.CONFIGURATION, ErrorSeverity.CRITICAL,
                                        {'model': self.settings.llm_model})
            logger.critical(f"💥 Failed to setup LLM: {e}")
            raise
    
    def _load_index(self):
        """Load existing vector index from Qdrant"""
        logger.info("📂 Loading vector index...")
        
        try:
            collection_name = self.settings.get_collection_name()
            
            # Qdrant Setup
            self.client = qdrant_client.QdrantClient(
                path=self.settings.qdrant_path
            )
            
            vector_store = QdrantVectorStore(
                client=self.client,
                collection_name=collection_name
            )
            
            try:
                node_count = self.client.count(collection_name=collection_name).count
            except:
                node_count = 0
            
            # Storage context
            storage_context = StorageContext.from_defaults(
                vector_store=vector_store
            )
            
            # Load index
            self.index = VectorStoreIndex.from_vector_store(
                vector_store,
                storage_context=storage_context
            )
            
            logger.success(f"✅ Index loaded ({node_count} nodes)")
            
        except Exception as e:
            logger.error(f"❌ Failed to load index: {e}")
            logger.warning("💡 Run ingestion first: python main.py ingest")
            # Allow continuing even if index load fails (e.g. first run)
            self.index = None
    
    def _index_bm25(self):
        """Index all documents for BM25 keyword search"""
        logger.info("🔑 Indexing documents for BM25 keyword search...")
        
        try:
            bm25_docs = []
            
            # Qdrant BM25 indexing
            if hasattr(self, 'client'):
                try:
                    # Scroll through all points
                    collection_name = self.settings.get_collection_name()
                    offset = None
                    while True:
                        points, next_offset = self.client.scroll(
                            collection_name=collection_name,
                            limit=100,
                            offset=offset,
                            with_payload=True,
                            with_vectors=False
                        )
                        
                        for point in points:
                            payload = point.payload or {}
                            # LlamaIndex stores text in 'text' or '_node_content'
                            text = payload.get('text')
                            
                            if not text:
                                node_content = payload.get('_node_content')
                                if isinstance(node_content, str):
                                    import json
                                    try:
                                        node_content = json.loads(node_content)
                                    except:
                                        node_content = {}
                                
                                if isinstance(node_content, dict):
                                    text = node_content.get('text', '')
                            
                            if text:
                                bm25_docs.append({
                                    'text': text,
                                    'metadata': payload,
                                    'id': str(point.id)
                                })
                        
                        offset = next_offset
                        if offset is None:
                            break
                except Exception as e:
                    logger.warning(f"⚠️ Could not fetch documents from Qdrant for BM25: {e}")
            
            if not bm25_docs:
                logger.warning("⚠️ No documents found for BM25 indexing")
                return
            
            # Index documents
            self.bm25_searcher.index_documents(bm25_docs)
            logger.success(f"✅ BM25 index ready with {len(bm25_docs)} documents")
            
        except Exception as e:
            logger.error(f"❌ Failed to index BM25: {e}")
            logger.warning("⚠️ BM25 search will not be available")
    
    def _setup_hybrid_search(self):
        """Initialize advanced hybrid search engine with RRF fusion"""
        try:
            # Create base retriever for hybrid engine
            base_retriever = VectorIndexRetriever(
                index=self.index,
                similarity_top_k=20
            )
            
            # Initialize hybrid search engine
            self.hybrid_engine = get_hybrid_search_engine(
                semantic_retriever=base_retriever,
                bm25_searcher=self.bm25_searcher,
                qdrant_client=self.client,
                collection_name=self.settings.get_collection_name()
            )
            
            logger.success("✅ Hybrid Search Engine ready (RRF fusion enabled)")
        except Exception as e:
            logger.warning(f"⚠️ Hybrid search engine not available: {e}")
            self.hybrid_engine = None
    
    def _setup_query_engine(self):
        """Configure query engine (Retriever + Synthesizer) with hierarchical context"""
        logger.info("🔧 Setting up query engine with hierarchical retrieval...")
        
        # Retriever: Fetches relevant nodes from database
        retriever = VectorIndexRetriever(
            index=self.index,
            similarity_top_k=15,  # Fetch more candidates for reranking
        )
        
        # Initialize hybrid search engine for advanced retrieval
        self._setup_hybrid_search()
        
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
        # Input validation
        try:
            validate_input(question, str, allow_none=False, min_length=1, max_length=5000)
        except ValueError as e:
            self.error_handler.log_error(e, ErrorCategory.VALIDATION, ErrorSeverity.MEDIUM, 
                                        {'question': question})
            return {
                "response": f"Invalid query: {str(e)}",
                "sources": [],
                "metadata": {"error": "validation_error", "message": str(e)},
                "error": str(e)
            }
        
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
                
                # Save cache hit to history
                history_metadata = {
                    'cache_hit': True,
                    'cache_age': cached_response['metadata'].get('cache_age_seconds', 0),
                    'filters': cache_filters
                }
                self.query_history.add_query(
                    query=question,
                    response=cached_response['response'],
                    sources=cached_response.get('sources', []),
                    metadata=history_metadata,
                    duration=0.001  # Instant from cache
                )
                
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
            
            # Save to query history
            query_duration = time.time() - start_time
            query_analysis = self.query_analyzer.analyze(question) if self.query_analyzer else {}
            query_intent = query_analysis.get('intent')
            history_metadata = {
                'cache_hit': False,
                'filters': cache_filters if self.use_response_cache else None,
                'query_type': query_intent.value if query_intent else None
            }
            self.query_history.add_query(
                query=question,
                response=answer_text,
                sources=result.get("sources", []),
                metadata=history_metadata,
                duration=query_duration
            )
            
            logger.success("✅ Answer generated")
            return result
            
        except Exception as e:
            # Log error with context
            self.error_handler.log_error(
                error=e,
                category=ErrorCategory.PROCESSING,
                severity=ErrorSeverity.HIGH,
                context={
                    'query': question,
                    'filters': {
                        'document': document_filter,
                        'category': category_filter,
                        'project': project_filter
                    },
                    'return_sources': return_sources
                }
            )
            
            # Save error to history
            error_metadata = {
                'error': True,
                'error_type': type(e).__name__,
                'error_message': str(e)
            }
            if self.query_history:
                try:
                    self.query_history.add_query(
                        query=question,
                        response=f"Error: {str(e)}",
                        sources=[],
                        metadata=error_metadata,
                        duration=time.time() - start_time if 'start_time' in locals() else 0
                    )
                except:
                    pass  # Don't fail on history save
            
            logger.error(f"❌ Query error: {e}")
            
            # Return user-friendly error message
            return {
                "response": "I apologize, but I encountered an error processing your query. Please try again or rephrase your question.",
                "sources": [],
                "metadata": {
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "suggestion": "Try simplifying your query or check your filters"
                },
                "error": str(e)
            }
    
    def advanced_query(
        self,
        question: str,
        return_sources: bool = True,
        use_rrf: bool = True,
        filters: Optional[Dict] = None
    ) -> Dict:
        """
        Advanced query using RRF-based hybrid search
        
        This method uses Reciprocal Rank Fusion to combine results from:
        - Semantic search (dense vectors)
        - BM25 search (keyword matching)
        - Metadata search (standards, sections)
        - Entity search (specifications, values)
        
        Args:
            question: User's question
            return_sources: Return source documents
            use_rrf: Use RRF fusion (True) or fallback to standard blend (False)
            filters: Optional filters {'document', 'category', 'project'}
            
        Returns:
            Response dictionary with answer and sources
        """
        logger.info(f"🔍 Advanced Query (RRF): '{question}'")
        
        # Analyze query
        query_analysis = self.query_analyzer.analyze(question)
        logger.info(f"   🧠 Intent: {query_analysis['intent'].value}")
        
        # Expand query
        if self.use_expansion and self.expander:
            expanded_query = self.expander.expand(question)
        else:
            expanded_query = question
        
        if expanded_query != question:
            logger.info(f"   ✨ Expanded query")
        
        start_time = time.time()
        
        try:
            # Use RRF-based hybrid search if available
            if use_rrf and hasattr(self, 'hybrid_engine') and self.hybrid_engine:
                # Perform adaptive hybrid search
                fused_results = self.hybrid_engine.adaptive_search(
                    query=expanded_query,
                    query_analysis=query_analysis,
                    top_k=15
                )
                
                if fused_results:
                    logger.info(f"   ✅ RRF fusion: {len(fused_results)} results")
                    logger.info(f"   📊 Top result coverage: {fused_results[0].retriever_coverage} retrievers")
                    
                    # Convert to NodeWithScore for LLM
                    from llama_index.core.schema import NodeWithScore, TextNode
                    
                    blended_nodes = []
                    for result in fused_results:
                        # Get original text (without context prefix for display)
                        original_text = result.metadata.get('original_text', result.text)
                        
                        node = TextNode(
                            text=result.text,
                            metadata=result.metadata,
                            id_=result.id
                        )
                        node_with_score = NodeWithScore(
                            node=node,
                            score=result.rrf_score
                        )
                        blended_nodes.append(node_with_score)
                else:
                    # Fallback to standard search
                    logger.warning("   ⚠️ RRF returned no results, falling back to standard search")
                    return self.query(question, return_sources, filters=filters)
            else:
                # Fallback to standard query
                return self.query(question, return_sources, filters=filters)
            
            # Generate response using LLM
            response_synthesizer = get_response_synthesizer(
                response_mode="compact",
                structured_answer_filtering=False
            )
            
            from llama_index.core.schema import QueryBundle
            query_bundle = QueryBundle(query_str=expanded_query)
            
            response = response_synthesizer.synthesize(
                query=query_bundle,
                nodes=blended_nodes[:10]
            )
            
            query_time = time.time() - start_time
            
            answer_text = str(response).strip()
            
            if not answer_text:
                answer_text = "I found relevant information but couldn't generate a response. Please try rephrasing."
            
            # Build result
            result = {
                "response": answer_text,
                "sources": [],
                "metadata": {
                    "question": question,
                    "model": self.settings.llm_model,
                    "query_intent": str(query_analysis['intent'].value),
                    "search_type": "rrf_hybrid",
                    "query_time": query_time,
                    "retrieval_info": {
                        "total_results": len(fused_results),
                        "top_rrf_score": fused_results[0].rrf_score if fused_results else 0,
                        "retriever_coverage": fused_results[0].retriever_coverage if fused_results else 0
                    }
                }
            }
            
            # Add sources
            if return_sources and blended_nodes:
                for idx, node in enumerate(blended_nodes[:10], 1):
                    metadata = node.node.metadata
                    
                    # Get display text (original without context prefix)
                    display_text = metadata.get('original_text', node.node.text)[:300]
                    
                    result["sources"].append({
                        "rank": idx,
                        "document": metadata.get('document_name', metadata.get('file_name', 'Unknown')),
                        "page": metadata.get('page_label', 'N/A'),
                        "section": metadata.get('section_number', ''),
                        "section_title": metadata.get('section_title', ''),
                        "text": display_text + "...",
                        "score": node.score,
                        "has_table": metadata.get('has_table', False),
                        "referenced_standards": metadata.get('referenced_standards', []),
                        "metadata": metadata
                    })
            
            logger.success(f"✅ Advanced query completed in {query_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"❌ Advanced query failed: {e}")
            # Fallback to standard query
            return self.query(question, return_sources, filters=filters)
    
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
            collection_name = self.settings.get_collection_name()
            node_count = 0
            db_path = ""
            
            # Check if we have a Qdrant client (preferred method)
            if hasattr(self, 'client') and self.client is not None:
                try:
                    node_count = self.client.count(collection_name=collection_name).count
                    db_path = self.settings.qdrant_path
                except Exception as e:
                    logger.debug(f"Could not get count from existing client: {e}")
                    node_count = 0
            else:
                # Fallback: try to create a new Qdrant client
                try:
                    client = qdrant_client.QdrantClient(path=self.settings.qdrant_path)
                    node_count = client.count(collection_name=collection_name).count
                    db_path = self.settings.qdrant_path
                    client.close()
                except Exception as e:
                    logger.debug(f"Could not create Qdrant client for stats: {e}")
                    node_count = 0
            
            return {
                'total_nodes': node_count,
                'db_path': db_path,
                'collection_name': collection_name
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {
                'total_nodes': 0,
                'db_path': self.settings.qdrant_path,
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
    
    # Query History Methods
    def get_query_history(self, limit: int = 20) -> List[Dict]:
        """Get recent query history"""
        return self.query_history.get_recent(limit)
    
    def search_history(self, search_term: str, limit: int = 20) -> List[Dict]:
        """Search query history"""
        return self.query_history.search(search_term, limit)
    
    def clear_history(self):
        """Clear all query history"""
        self.query_history.clear_all()
    
    def get_history_statistics(self) -> Dict:
        """Get history statistics"""
        return self.query_history.get_statistics()
    
    # Export Methods
    def export_result(self, query: str, response: str, sources: List[Dict],
                     format: str = 'markdown', metadata: Dict = None) -> Optional[str]:
        """
        Export query result to file
        
        Args:
            query: User query
            response: System response
            sources: Source documents
            format: 'markdown', 'pdf', or 'word'
            metadata: Additional metadata
            
        Returns:
            Path to exported file
        """
        if format == 'markdown':
            return self.export_manager.export_to_markdown(query, response, sources, metadata)
        elif format == 'pdf':
            return self.export_manager.export_to_pdf(query, response, sources, metadata)
        elif format == 'word':
            return self.export_manager.export_to_word(query, response, sources, metadata)
        else:
            logger.error(f"❌ Unknown export format: {format}")
            return None
    
    def export_all_formats(self, query: str, response: str, sources: List[Dict],
                          metadata: Dict = None) -> Dict[str, Optional[str]]:
        """Export to all available formats"""
        return self.export_manager.export_all_formats(query, response, sources, metadata)
    
    # Graph Visualization Methods
    def init_graph_visualizer(self):
        """Initialize graph visualizer (requires Neo4j)"""
        if not self.graph_visualizer:
            self.graph_visualizer = get_graph_visualizer(
                neo4j_uri=self.settings.neo4j_uri,
                neo4j_user=self.settings.neo4j_user,
                neo4j_password=self.settings.neo4j_password
            )
    
    def visualize_graph(self, limit: int = 100) -> Optional[str]:
        """
        Create graph visualization
        
        Args:
            limit: Maximum nodes to include
            
        Returns:
            Path to saved image
        """
        if not self.graph_visualizer:
            self.init_graph_visualizer()
        
        if self.graph_visualizer:
            return self.graph_visualizer.visualize_graph(limit)
        return None
    
    def visualize_query_context(self, query: str, sources: List[Dict]) -> Optional[str]:
        """
        Visualize query context (query + sources)
        
        Args:
            query: User query
            sources: Source documents
            
        Returns:
            Path to saved image
        """
        if not self.graph_visualizer:
            self.init_graph_visualizer()
        
        if self.graph_visualizer:
            return self.graph_visualizer.visualize_query_context(query, sources)
        return None
    
    def get_graph_statistics(self) -> Dict:
        """Get graph statistics"""
        if not self.graph_visualizer:
            self.init_graph_visualizer()
        
        if self.graph_visualizer:
            return self.graph_visualizer.get_graph_statistics()
        return {}
    
    # Health & Monitoring Methods
    def get_system_health(self) -> Dict:
        """Get overall system health"""
        return self.health_check.get_system_health()
    
    def get_error_statistics(self) -> Dict:
        """Get error statistics"""
        return self.error_handler.get_error_stats()
    
    def get_component_status(self, component_name: str) -> str:
        """Get specific component status"""
        status = self.health_check.check_component(component_name)
        return status.value if status else "unknown"
    
    def is_degraded_mode(self) -> bool:
        """Check if system is running in degraded mode"""
        health = self.health_check.get_system_health()
        return health['overall_status'] in [HealthStatus.DEGRADED, HealthStatus.UNHEALTHY]
    
    # =====================
    # GraphRAG Integration
    # =====================
    
    def _setup_graph_rag(self):
        """Initialize GraphRAG for graph-enhanced retrieval"""
        try:
            graph_rag = get_graph_rag(
                neo4j_uri=self.settings.neo4j_uri,
                neo4j_user=self.settings.neo4j_user,
                neo4j_password=self.settings.neo4j_password,
                qdrant_client=self.client,
                collection_name=self.settings.get_collection_name()
            )
            
            if graph_rag and graph_rag.is_available():
                self.graph_rag = graph_rag
                logger.success("✅ GraphRAG ready (vector + graph fusion)")
            else:
                self.graph_rag = None
                logger.warning("⚠️ GraphRAG not available (Neo4j connection required)")
                
        except Exception as e:
            logger.warning(f"⚠️ GraphRAG initialization failed: {e}")
            self.graph_rag = None
    
    def graph_query(
        self,
        question: str,
        max_hops: int = 2,
        return_reasoning: bool = True,
        filters: Optional[Dict] = None
    ) -> Dict:
        """
        GraphRAG-enhanced query combining vector search with knowledge graph
        
        This method uses the knowledge graph for:
        - Multi-hop reasoning across related standards
        - Entity-based retrieval (specifications, requirements)
        - Cross-reference discovery between documents
        - Reasoning chain generation
        
        Args:
            question: User's question
            max_hops: Maximum graph traversal depth
            return_reasoning: Include reasoning chain in response
            filters: Optional document/category filters
            
        Returns:
            Response dict with answer, sources, and reasoning chain
        """
        logger.info(f"🔍 GraphRAG Query: '{question}'")
        
        # Initialize GraphRAG if not done
        if not hasattr(self, 'graph_rag') or self.graph_rag is None:
            self._setup_graph_rag()
        
        # Check availability
        if not hasattr(self, 'graph_rag') or self.graph_rag is None:
            logger.warning("⚠️ GraphRAG not available, falling back to advanced_query")
            return self.advanced_query(question, return_sources=True, filters=filters)
        
        start_time = time.time()
        
        try:
            # Analyze query
            query_analysis = self.query_analyzer.analyze(question)
            logger.info(f"   🧠 Intent: {query_analysis['intent'].value}")
            
            # Get GraphRAG response
            graph_result = self.graph_rag.get_answer_with_graph(
                query=question,
                max_hops=max_hops
            )
            
            query_time = time.time() - start_time
            
            # Build result
            result = {
                "response": graph_result.answer,
                "sources": [],
                "metadata": {
                    "question": question,
                    "model": self.settings.llm_model,
                    "query_intent": str(query_analysis['intent'].value),
                    "search_type": "graph_rag",
                    "query_time": query_time,
                    "graph_info": {
                        "entities_found": len(graph_result.entities),
                        "paths_traversed": len(graph_result.paths),
                        "vector_results": len(graph_result.vector_results),
                        "graph_results": len(graph_result.graph_results)
                    }
                }
            }
            
            # Add reasoning chain
            if return_reasoning and graph_result.reasoning_chain:
                result["reasoning_chain"] = graph_result.reasoning_chain
                logger.info(f"   🔗 Reasoning chain: {len(graph_result.reasoning_chain)} steps")
            
            # Build sources from combined results
            combined_nodes = graph_result.combined_context[:10]
            for idx, node in enumerate(combined_nodes, 1):
                metadata = node.metadata if hasattr(node, 'metadata') else {}
                text = node.text if hasattr(node, 'text') else str(node)
                
                result["sources"].append({
                    "rank": idx,
                    "document": metadata.get('document_name', metadata.get('file_name', 'Unknown')),
                    "page": metadata.get('page_label', 'N/A'),
                    "section": metadata.get('section_number', ''),
                    "section_title": metadata.get('section_title', ''),
                    "text": text[:300] + "..." if len(text) > 300 else text,
                    "source_type": metadata.get('source_type', 'vector'),
                    "metadata": metadata
                })
            
            # Add discovered entities
            if graph_result.entities:
                result["discovered_entities"] = [
                    {
                        "name": e.name,
                        "type": e.type,
                        "properties": e.properties
                    }
                    for e in graph_result.entities[:10]
                ]
            
            # Add relationship paths
            if graph_result.paths:
                result["graph_paths"] = [
                    {
                        "from": p.source,
                        "relationship": p.relationship,
                        "to": p.target,
                        "strength": p.strength
                    }
                    for p in graph_result.paths[:10]
                ]
            
            logger.success(f"✅ GraphRAG query completed in {query_time:.2f}s")
            logger.info(f"   📊 Found {len(graph_result.entities)} entities, {len(graph_result.paths)} relationships")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ GraphRAG query failed: {e}")
            logger.info("   ↩️ Falling back to advanced_query")
            return self.advanced_query(question, return_sources=True, filters=filters)
    
    def get_entity_context(
        self,
        entity_name: str,
        entity_type: str = "STANDARD",
        max_hops: int = 2
    ) -> Dict:
        """
        Get all context related to a specific entity from the knowledge graph
        
        Useful for exploring relationships of a specific standard, specification,
        or requirement without asking a question.
        
        Args:
            entity_name: Name of the entity (e.g., "IS10101", "2.5mm² cable")
            entity_type: Type of entity (STANDARD, SPECIFICATION, REQUIREMENT, etc.)
            max_hops: Maximum relationship depth to explore
            
        Returns:
            Dict with entity info, related entities, and relevant chunks
        """
        logger.info(f"🔍 Getting context for entity: {entity_name} ({entity_type})")
        
        if not hasattr(self, 'graph_rag') or self.graph_rag is None:
            self._setup_graph_rag()
        
        if not hasattr(self, 'graph_rag') or self.graph_rag is None:
            return {
                "entity": entity_name,
                "error": "GraphRAG not available",
                "related_entities": [],
                "relevant_chunks": []
            }
        
        try:
            # Get graph context
            context = self.graph_rag.get_entity_context(
                entity_name=entity_name,
                entity_type=entity_type,
                max_hops=max_hops
            )
            
            return context
            
        except Exception as e:
            logger.error(f"❌ Failed to get entity context: {e}")
            return {
                "entity": entity_name,
                "error": str(e),
                "related_entities": [],
                "relevant_chunks": []
            }
    
    def discover_cross_references(
        self,
        document_name: str,
        relationship_types: Optional[List[str]] = None
    ) -> Dict:
        """
        Discover all cross-references from a document using the knowledge graph
        
        Args:
            document_name: Document to analyze
            relationship_types: Filter specific relationship types
                              (REFERENCES, SUPERSEDES, CONFLICTS, REQUIRES)
            
        Returns:
            Dict with incoming and outgoing references
        """
        logger.info(f"🔍 Discovering cross-references for: {document_name}")
        
        if not hasattr(self, 'graph_rag') or self.graph_rag is None:
            self._setup_graph_rag()
        
        if not hasattr(self, 'graph_rag') or self.graph_rag is None:
            return {
                "document": document_name,
                "error": "GraphRAG not available",
                "references": {"outgoing": [], "incoming": []}
            }
        
        try:
            references = self.graph_rag.discover_cross_references(
                document_name=document_name,
                relationship_types=relationship_types
            )
            
            return {
                "document": document_name,
                "references": references,
                "total_outgoing": len(references.get("outgoing", [])),
                "total_incoming": len(references.get("incoming", []))
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to discover cross-references: {e}")
            return {
                "document": document_name,
                "error": str(e),
                "references": {"outgoing": [], "incoming": []}
            }


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
