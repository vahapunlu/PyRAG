"""
Hybrid Search with Reciprocal Rank Fusion (RRF)

Advanced retrieval combining multiple search strategies:
1. Dense Vector Search (Semantic)
2. Sparse Vector Search (BM25/TF-IDF)  
3. Metadata-Enhanced Search
4. Entity-Based Search

Uses RRF to combine rankings from different retrievers for
optimal result blending.

Reference: "Reciprocal Rank Fusion Outperforms Condorcet and Individual Rank Learning Methods"
"""

import re
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from llama_index.core.schema import NodeWithScore, TextNode
from loguru import logger


@dataclass
class SearchResult:
    """Unified search result from any retriever"""
    id: str
    text: str
    score: float
    rank: int
    source: str  # 'semantic', 'bm25', 'metadata', 'entity', 'graph'
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        return self.id == other.id


@dataclass
class FusedResult:
    """Result after RRF fusion"""
    id: str
    text: str
    rrf_score: float
    component_scores: Dict[str, float]  # score from each retriever
    component_ranks: Dict[str, int]  # rank from each retriever
    metadata: Dict[str, Any] = field(default_factory=dict)
    retriever_coverage: int = 0  # how many retrievers found this


class ReciprocalRankFusion:
    """
    Reciprocal Rank Fusion (RRF) for combining multiple retriever results
    
    RRF Score = Σ 1/(k + rank_i) for each retriever i
    
    Where k is a constant (default 60) that dampens the effect of high rankings
    """
    
    def __init__(self, k: int = 60):
        """
        Initialize RRF
        
        Args:
            k: RRF constant (default 60, as suggested in original paper)
        """
        self.k = k
        logger.info(f"✅ RRF Fusion initialized (k={k})")
    
    def fuse(self, 
             result_lists: List[List[SearchResult]],
             weights: Optional[Dict[str, float]] = None) -> List[FusedResult]:
        """
        Fuse multiple ranked result lists using RRF
        
        Args:
            result_lists: List of result lists from different retrievers
            weights: Optional weights for each source (default: equal weights)
            
        Returns:
            Sorted list of fused results
        """
        if not result_lists:
            return []
        
        # Default weights
        if weights is None:
            weights = {}
        
        # Collect all unique documents
        doc_scores: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'rrf_score': 0.0,
            'component_scores': {},
            'component_ranks': {},
            'text': '',
            'metadata': {},
            'sources': set()
        })
        
        # Calculate RRF scores
        for results in result_lists:
            if not results:
                continue
            
            source = results[0].source if results else 'unknown'
            weight = weights.get(source, 1.0)
            
            for result in results:
                doc_id = result.id
                rank = result.rank
                
                # RRF formula: weight * 1/(k + rank)
                rrf_contribution = weight * (1.0 / (self.k + rank))
                
                doc_scores[doc_id]['rrf_score'] += rrf_contribution
                doc_scores[doc_id]['component_scores'][source] = result.score
                doc_scores[doc_id]['component_ranks'][source] = rank
                doc_scores[doc_id]['text'] = result.text
                doc_scores[doc_id]['metadata'] = result.metadata
                doc_scores[doc_id]['sources'].add(source)
        
        # Create fused results
        fused_results = []
        for doc_id, data in doc_scores.items():
            fused = FusedResult(
                id=doc_id,
                text=data['text'],
                rrf_score=data['rrf_score'],
                component_scores=data['component_scores'],
                component_ranks=data['component_ranks'],
                metadata=data['metadata'],
                retriever_coverage=len(data['sources'])
            )
            fused_results.append(fused)
        
        # Sort by RRF score (descending)
        fused_results.sort(key=lambda x: x.rrf_score, reverse=True)
        
        return fused_results


class HybridSearchEngine:
    """
    Advanced hybrid search combining multiple retrieval strategies
    
    Strategies:
    1. Semantic (Dense Vector) - conceptual similarity
    2. BM25 (Sparse) - keyword matching
    3. Metadata - filter by standards, sections, etc.
    4. Entity - search by extracted entities
    """
    
    def __init__(self, 
                 semantic_retriever=None,
                 bm25_searcher=None,
                 qdrant_client=None,
                 collection_name: str = ""):
        """
        Initialize hybrid search engine
        
        Args:
            semantic_retriever: LlamaIndex vector retriever
            bm25_searcher: BM25Searcher instance
            qdrant_client: Qdrant client for metadata search
            collection_name: Qdrant collection name
        """
        self.semantic_retriever = semantic_retriever
        self.bm25_searcher = bm25_searcher
        self.qdrant_client = qdrant_client
        self.collection_name = collection_name
        
        self.rrf = ReciprocalRankFusion(k=60)
        
        # Default weights for different search types
        self.default_weights = {
            'semantic': 1.0,
            'bm25': 0.8,
            'metadata': 0.6,
            'entity': 0.7,
            'graph': 0.5
        }
        
        logger.info("✅ Hybrid Search Engine initialized")
    
    def _semantic_search(self, query: str, top_k: int = 15) -> List[SearchResult]:
        """Perform semantic (dense vector) search"""
        if not self.semantic_retriever:
            return []
        
        try:
            nodes = self.semantic_retriever.retrieve(query)
            
            results = []
            for rank, node in enumerate(nodes[:top_k], 1):
                results.append(SearchResult(
                    id=node.node.id_,
                    text=node.node.text,
                    score=node.score or 0.0,
                    rank=rank,
                    source='semantic',
                    metadata=node.node.metadata
                ))
            
            return results
        
        except Exception as e:
            logger.warning(f"Semantic search failed: {e}")
            return []
    
    def _bm25_search(self, query: str, top_k: int = 15) -> List[SearchResult]:
        """Perform BM25 (sparse) keyword search"""
        if not self.bm25_searcher:
            return []
        
        try:
            bm25_results = self.bm25_searcher.search(query, top_k=top_k)
            
            results = []
            for rank, item in enumerate(bm25_results[:top_k], 1):
                results.append(SearchResult(
                    id=item.get('id', str(rank)),
                    text=item.get('text', ''),
                    score=item.get('score', 0.0),
                    rank=rank,
                    source='bm25',
                    metadata=item.get('metadata', {})
                ))
            
            return results
        
        except Exception as e:
            logger.warning(f"BM25 search failed: {e}")
            return []
    
    def _metadata_search(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """Search based on metadata fields (standards, sections, etc.)"""
        if not self.qdrant_client or not self.collection_name:
            return []
        
        try:
            # Extract potential metadata values from query
            standards = self._extract_standards(query)
            section_nums = self._extract_sections(query)
            
            if not standards and not section_nums:
                return []
            
            # Build Qdrant filter
            from qdrant_client.models import Filter, FieldCondition, MatchValue, MatchAny
            
            conditions = []
            
            if standards:
                # Search in referenced_standards array
                conditions.append(
                    FieldCondition(
                        key="referenced_standards",
                        match=MatchAny(any=standards)
                    )
                )
            
            if section_nums:
                # Search by section number
                for sec in section_nums:
                    conditions.append(
                        FieldCondition(
                            key="section_number",
                            match=MatchValue(value=sec)
                        )
                    )
            
            if not conditions:
                return []
            
            # Execute scroll with filter
            results = []
            filter_obj = Filter(should=conditions) if len(conditions) > 1 else Filter(must=conditions)
            
            points, _ = self.qdrant_client.scroll(
                collection_name=self.collection_name,
                scroll_filter=filter_obj,
                limit=top_k,
                with_payload=True,
                with_vectors=False
            )
            
            for rank, point in enumerate(points, 1):
                payload = point.payload or {}
                text = payload.get('text', '')
                
                if not text:
                    node_content = payload.get('_node_content')
                    if isinstance(node_content, str):
                        import json
                        try:
                            node_content = json.loads(node_content)
                            text = node_content.get('text', '')
                        except:
                            pass
                
                if text:
                    results.append(SearchResult(
                        id=str(point.id),
                        text=text,
                        score=1.0 / rank,  # Simple rank-based score
                        rank=rank,
                        source='metadata',
                        metadata=payload
                    ))
            
            return results
        
        except Exception as e:
            logger.warning(f"Metadata search failed: {e}")
            return []
    
    def _entity_search(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """Search based on extracted entities (standards, specs)"""
        if not self.qdrant_client or not self.collection_name:
            return []
        
        try:
            # Extract entity types from query
            spec_values = self._extract_specifications(query)
            
            if not spec_values:
                return []
            
            from qdrant_client.models import Filter, FieldCondition, MatchAny
            
            # Search by specification values
            conditions = [
                FieldCondition(
                    key="spec_values",
                    match=MatchAny(any=spec_values)
                )
            ]
            
            points, _ = self.qdrant_client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(should=conditions),
                limit=top_k,
                with_payload=True,
                with_vectors=False
            )
            
            results = []
            for rank, point in enumerate(points, 1):
                payload = point.payload or {}
                text = payload.get('text', '')
                
                if not text:
                    node_content = payload.get('_node_content')
                    if isinstance(node_content, str):
                        import json
                        try:
                            node_content = json.loads(node_content)
                            text = node_content.get('text', '')
                        except:
                            pass
                
                if text:
                    results.append(SearchResult(
                        id=str(point.id),
                        text=text,
                        score=1.0 / rank,
                        rank=rank,
                        source='entity',
                        metadata=payload
                    ))
            
            return results
        
        except Exception as e:
            logger.warning(f"Entity search failed: {e}")
            return []
    
    def _extract_standards(self, text: str) -> List[str]:
        """Extract standard references from text"""
        patterns = [
            r'\bIS[\s-]?\d+(?:[-:]\d+)*',
            r'\bEN[\s-]?\d+(?:[-:]\d+)*',
            r'\bIEC[\s-]?\d+(?:[-:]\d+)*',
            r'\bBS[\s-]?\d+(?:[-:]\d+)*',
            r'\bNFPA[\s-]?\d+',
            r'\bISO[\s-]?\d+(?:[-:]\d+)*',
        ]
        
        standards = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            standards.extend([m.upper().replace(' ', '') for m in matches])
        
        return list(set(standards))
    
    def _extract_sections(self, text: str) -> List[str]:
        """Extract section numbers from text"""
        pattern = r'\b(\d+(?:\.\d+)+)\b'
        matches = re.findall(pattern, text)
        return list(set(matches))
    
    def _extract_specifications(self, text: str) -> List[str]:
        """Extract specification values from text"""
        patterns = [
            r'\d+(?:\.\d+)?\s*mm²',
            r'\d+(?:\.\d+)?\s*[kK]?[vV]',
            r'\d+(?:\.\d+)?\s*[kK]?[aA]',
            r'\d+(?:\.\d+)?\s*[kK]?[wW]',
            r'\d+(?:\.\d+)?\s*[Ω°]',
        ]
        
        specs = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            specs.extend(matches)
        
        return list(set(specs))
    
    def search(self, 
               query: str, 
               top_k: int = 10,
               weights: Optional[Dict[str, float]] = None,
               strategies: Optional[List[str]] = None) -> List[FusedResult]:
        """
        Perform hybrid search with RRF fusion
        
        Args:
            query: Search query
            top_k: Number of results to return
            weights: Custom weights for each strategy
            strategies: Which strategies to use ['semantic', 'bm25', 'metadata', 'entity']
            
        Returns:
            List of fused results sorted by RRF score
        """
        if strategies is None:
            strategies = ['semantic', 'bm25', 'metadata']
        
        if weights is None:
            weights = self.default_weights
        
        start_time = time.time()
        all_results = []
        
        # Execute searches in parallel
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {}
            
            if 'semantic' in strategies:
                futures['semantic'] = executor.submit(self._semantic_search, query, top_k * 2)
            
            if 'bm25' in strategies:
                futures['bm25'] = executor.submit(self._bm25_search, query, top_k * 2)
            
            if 'metadata' in strategies:
                futures['metadata'] = executor.submit(self._metadata_search, query, top_k)
            
            if 'entity' in strategies:
                futures['entity'] = executor.submit(self._entity_search, query, top_k)
            
            # Collect results
            for strategy, future in futures.items():
                try:
                    results = future.result(timeout=5.0)
                    if results:
                        all_results.append(results)
                        logger.debug(f"   {strategy}: {len(results)} results")
                except Exception as e:
                    logger.warning(f"   {strategy} search timeout/error: {e}")
        
        search_time = time.time() - start_time
        logger.info(f"   ⚡ Hybrid search completed in {search_time:.3f}s")
        
        if not all_results:
            return []
        
        # Apply RRF fusion
        fused = self.rrf.fuse(all_results, weights=weights)
        
        # Return top_k results
        return fused[:top_k]
    
    def adaptive_search(self, 
                        query: str,
                        query_analysis: Dict[str, Any],
                        top_k: int = 10) -> List[FusedResult]:
        """
        Adaptive hybrid search based on query analysis
        
        Adjusts weights dynamically based on query intent:
        - Technical queries → higher BM25 weight
        - Conceptual queries → higher semantic weight
        - Reference queries → higher metadata weight
        """
        intent = query_analysis.get('intent', 'general')
        analysis_weights = query_analysis.get('weights', {})
        
        # Build adaptive weights
        weights = dict(self.default_weights)
        
        # Map query analysis weights to search weights
        if 'semantic' in analysis_weights:
            weights['semantic'] = analysis_weights['semantic']
        if 'keyword' in analysis_weights:
            weights['bm25'] = analysis_weights['keyword']
        
        # Intent-based adjustments
        intent_name = str(intent).lower()
        
        if 'technical' in intent_name or 'specific' in intent_name:
            weights['bm25'] *= 1.2
            weights['metadata'] *= 1.3
        elif 'comparison' in intent_name:
            weights['semantic'] *= 1.2
        elif 'reference' in intent_name:
            weights['metadata'] *= 1.5
            weights['entity'] *= 1.3
        
        # Normalize weights
        total = sum(weights.values())
        if total > 0:
            weights = {k: v / total for k, v in weights.items()}
        
        # Determine strategies based on query
        strategies = ['semantic', 'bm25']
        
        # Add metadata search if query mentions standards
        if self._extract_standards(query) or self._extract_sections(query):
            strategies.append('metadata')
        
        # Add entity search if query mentions specifications
        if self._extract_specifications(query):
            strategies.append('entity')
        
        logger.info(f"   🧠 Adaptive search: {strategies}, weights: {weights}")
        
        return self.search(query, top_k=top_k, weights=weights, strategies=strategies)


# Singleton instance
_hybrid_engine: Optional[HybridSearchEngine] = None


def get_hybrid_search_engine(
    semantic_retriever=None,
    bm25_searcher=None,
    qdrant_client=None,
    collection_name: str = ""
) -> HybridSearchEngine:
    """Get or create hybrid search engine singleton"""
    global _hybrid_engine
    
    # Create new instance if not exists or parameters changed
    if _hybrid_engine is None:
        _hybrid_engine = HybridSearchEngine(
            semantic_retriever=semantic_retriever,
            bm25_searcher=bm25_searcher,
            qdrant_client=qdrant_client,
            collection_name=collection_name
        )
    else:
        # Update components if provided
        if semantic_retriever:
            _hybrid_engine.semantic_retriever = semantic_retriever
        if bm25_searcher:
            _hybrid_engine.bm25_searcher = bm25_searcher
        if qdrant_client:
            _hybrid_engine.qdrant_client = qdrant_client
        if collection_name:
            _hybrid_engine.collection_name = collection_name
    
    return _hybrid_engine


if __name__ == "__main__":
    # Test RRF fusion
    logger.info("Testing Reciprocal Rank Fusion...")
    
    # Simulated results from different retrievers
    semantic_results = [
        SearchResult(id="doc1", text="Cable specifications...", score=0.95, rank=1, source='semantic'),
        SearchResult(id="doc2", text="Wiring requirements...", score=0.88, rank=2, source='semantic'),
        SearchResult(id="doc3", text="Conductor sizing...", score=0.82, rank=3, source='semantic'),
    ]
    
    bm25_results = [
        SearchResult(id="doc2", text="Wiring requirements...", score=5.2, rank=1, source='bm25'),
        SearchResult(id="doc4", text="Cable types...", score=4.8, rank=2, source='bm25'),
        SearchResult(id="doc1", text="Cable specifications...", score=4.5, rank=3, source='bm25'),
    ]
    
    metadata_results = [
        SearchResult(id="doc5", text="IEC 60364 reference...", score=1.0, rank=1, source='metadata'),
        SearchResult(id="doc1", text="Cable specifications...", score=0.8, rank=2, source='metadata'),
    ]
    
    # Test RRF
    rrf = ReciprocalRankFusion(k=60)
    fused = rrf.fuse([semantic_results, bm25_results, metadata_results])
    
    print("\n📋 RRF Fusion Results:")
    for i, result in enumerate(fused[:5], 1):
        print(f"   {i}. {result.id}")
        print(f"      RRF Score: {result.rrf_score:.4f}")
        print(f"      Coverage: {result.retriever_coverage} retrievers")
        print(f"      Ranks: {result.component_ranks}")
