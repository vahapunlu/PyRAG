"""
GraphRAG - Graph-Enhanced Retrieval Augmented Generation

Combines vector search with knowledge graph traversal for:
- Multi-hop reasoning across documents
- Related entity discovery
- Conflict detection
- Comprehensive answer synthesis

This approach dramatically improves answer quality for complex queries
that span multiple documents and require understanding relationships.
"""

from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import time

from loguru import logger


@dataclass
class GraphNode:
    """Represents a node in the traversal result"""
    id: str
    type: str  # 'document', 'section', 'standard', 'requirement', 'specification'
    name: str
    properties: Dict[str, Any] = field(default_factory=dict)
    depth: int = 0
    path: List[str] = field(default_factory=list)  # Path from query to this node


@dataclass
class GraphPath:
    """Represents a path through the knowledge graph"""
    source: str
    target: str
    relationship: str
    strength: float = 1.0
    nodes: List[GraphNode] = field(default_factory=list)
    total_depth: int = 1


@dataclass
class GraphRAGResult:
    """Result from GraphRAG retrieval"""
    query: str
    answer: str
    vector_results: List[Any]  # TextNodes or dicts
    graph_results: List[GraphNode]
    entities: List[GraphNode]  # Discovered entities
    paths: List[GraphPath]  # Relationship paths
    combined_context: List[Any]  # Combined nodes for context
    reasoning_chain: List[str]


class GraphRAG:
    """
    Graph-Enhanced RAG combining vector search with graph traversal
    
    Process:
    1. Vector search to find initial relevant chunks
    2. Extract entities from query and results
    3. Graph traversal from entities to find related context
    4. Combine and rank all context sources
    5. Generate comprehensive answer
    """
    
    def __init__(self, 
                 graph_manager=None,
                 vector_searcher=None,
                 max_hops: int = 2,
                 max_graph_results: int = 20):
        """
        Initialize GraphRAG
        
        Args:
            graph_manager: Neo4j graph manager
            vector_searcher: Vector search engine (QueryEngine or HybridSearchEngine)
            max_hops: Maximum graph traversal depth
            max_graph_results: Maximum results from graph
        """
        self.graph_manager = graph_manager
        self.vector_searcher = vector_searcher
        self.max_hops = max_hops
        self.max_graph_results = max_graph_results
        
        # Entity extraction patterns
        self.standard_pattern = r'\b(IS|EN|IEC|BS|NFPA|IEEE|ISO|ASTM)[\s-]?\d+(?:[-:]\d+)*'
        
        logger.info(f"✅ GraphRAG initialized (max_hops={max_hops})")
    
    def is_available(self) -> bool:
        """Check if GraphRAG is available (has graph_manager)"""
        return self.graph_manager is not None
    
    @property
    def enabled(self) -> bool:
        """Check if GraphRAG is enabled"""
        return self.graph_manager is not None
    
    def retrieve(self, 
                 query: str,
                 top_k: int = 10,
                 use_graph: bool = True,
                 expand_standards: bool = True) -> GraphRAGResult:
        """
        Perform GraphRAG retrieval
        
        Args:
            query: User query
            top_k: Number of vector results
            use_graph: Whether to use graph traversal
            expand_standards: Expand standard references to related sections
            
        Returns:
            GraphRAGResult with combined context
        """
        start_time = time.time()
        
        # Step 1: Vector search
        vector_results = self._vector_search(query, top_k)
        logger.info(f"   📊 Vector search: {len(vector_results)} results")
        
        # Step 2: Extract entities from query and results
        query_entities = self._extract_entities(query)
        result_entities = set()
        for result in vector_results:
            text = result.get('text', '')
            result_entities.update(self._extract_entities(text))
        
        all_entities = query_entities | result_entities
        logger.info(f"   🏷️ Entities found: {len(all_entities)}")
        
        # Step 3: Graph traversal (if enabled)
        graph_results = []
        paths = []
        related_standards = []
        cross_references = []
        
        if use_graph and self.enabled and all_entities:
            graph_data = self._graph_traverse(all_entities)
            graph_results = graph_data.get('nodes', [])
            paths = graph_data.get('paths', [])
            related_standards = graph_data.get('standards', [])
            cross_references = graph_data.get('cross_refs', [])
            logger.info(f"   🕸️ Graph traversal: {len(graph_results)} nodes, {len(paths)} paths")
        
        # Step 4: Build combined context
        combined_context = self._build_combined_context(
            vector_results, graph_results, paths
        )
        
        # Step 5: Build entity summary
        entity_summary = self._build_entity_summary(all_entities, graph_results)
        
        # Step 6: Generate reasoning chain
        reasoning_chain = self._generate_reasoning_chain(
            query, vector_results, graph_results, paths
        )
        
        total_time = time.time() - start_time
        logger.info(f"   ⚡ GraphRAG completed in {total_time:.3f}s")
        
        return GraphRAGResult(
            query=query,
            vector_results=vector_results,
            graph_results=graph_results,
            paths=paths,
            combined_context=combined_context,
            entity_summary=entity_summary,
            related_standards=related_standards,
            cross_references=cross_references,
            reasoning_chain=reasoning_chain
        )
    
    def _vector_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Perform vector search"""
        if not self.vector_searcher:
            return []
        
        try:
            # Try different vector searcher interfaces
            if hasattr(self.vector_searcher, 'search'):
                # HybridSearchEngine
                results = self.vector_searcher.search(query, top_k=top_k)
                return [{'id': r.id, 'text': r.text, 'score': r.rrf_score, 
                        'metadata': r.metadata} for r in results]
            elif hasattr(self.vector_searcher, 'query'):
                # QueryEngine
                response = self.vector_searcher.query(query)
                if hasattr(response, 'source_nodes'):
                    return [{'id': n.node.id_, 'text': n.node.text, 
                            'score': n.score, 'metadata': n.node.metadata}
                           for n in response.source_nodes]
            return []
        except Exception as e:
            logger.warning(f"Vector search failed: {e}")
            return []
    
    def _extract_entities(self, text: str) -> Set[str]:
        """Extract entities (standards, sections) from text"""
        import re
        entities = set()
        
        # Extract standards
        matches = re.findall(self.standard_pattern, text, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                match = match[0] if match else ''
            # Get full match including number
            full_matches = re.findall(
                r'\b' + re.escape(match) + r'[\s-]?\d+(?:[-:]\d+)*',
                text, re.IGNORECASE
            )
            entities.update(m.upper().replace(' ', '') for m in full_matches)
        
        # Extract section numbers
        section_matches = re.findall(r'\b(\d+(?:\.\d+){1,4})\b', text)
        entities.update(f"section_{s}" for s in section_matches)
        
        return entities
    
    def _graph_traverse(self, entities: Set[str]) -> Dict[str, Any]:
        """Traverse graph from entities"""
        if not self.graph_manager:
            return {'nodes': [], 'paths': [], 'standards': [], 'cross_refs': []}
        
        nodes = []
        paths = []
        standards = []
        cross_refs = []
        
        try:
            # Query for each entity
            for entity in list(entities)[:10]:  # Limit entities
                if entity.startswith('section_'):
                    # Section-based traversal
                    section_num = entity.replace('section_', '')
                    section_nodes = self._get_section_context(section_num)
                    nodes.extend(section_nodes)
                else:
                    # Standard-based traversal
                    standard_nodes = self._get_standard_context(entity)
                    nodes.extend(standard_nodes)
                    standards.append(entity)
                    
                    # Get cross-references
                    refs = self._get_cross_references(entity)
                    cross_refs.extend(refs)
            
            # Deduplicate
            seen_ids = set()
            unique_nodes = []
            for node in nodes:
                if node.id not in seen_ids:
                    seen_ids.add(node.id)
                    unique_nodes.append(node)
            
            return {
                'nodes': unique_nodes[:self.max_graph_results],
                'paths': paths,
                'standards': list(set(standards)),
                'cross_refs': cross_refs
            }
            
        except Exception as e:
            logger.warning(f"Graph traversal failed: {e}")
            return {'nodes': [], 'paths': [], 'standards': [], 'cross_refs': []}
    
    def _get_section_context(self, section_num: str) -> List[GraphNode]:
        """Get context for a section from graph"""
        nodes = []
        
        try:
            # Find documents containing this section
            query = """
            MATCH (d:Document)-[:CONTAINS]->(s:Section {number: $section_num})
            RETURN d.name as doc_name, s.title as section_title, s.number as section_number
            LIMIT 5
            """
            result = self.graph_manager._run_query(query, {'section_num': section_num})
            
            for record in result:
                nodes.append(GraphNode(
                    id=f"doc_{record['doc_name']}_{record['section_number']}",
                    type='section',
                    name=f"{record['doc_name']} - {record['section_title']}",
                    properties={
                        'document': record['doc_name'],
                        'section': record['section_number'],
                        'title': record['section_title']
                    },
                    depth=1
                ))
                
        except Exception as e:
            logger.debug(f"Section context query failed: {e}")
        
        return nodes
    
    def _get_standard_context(self, standard: str) -> List[GraphNode]:
        """Get context for a standard from graph"""
        nodes = []
        
        try:
            # Find documents and sections referencing this standard
            query = """
            MATCH (s:Standard {name: $standard})<-[:REFERS_TO]-(d:Document)
            OPTIONAL MATCH (d)-[:CONTAINS]->(sec:Section)
            RETURN d.name as doc_name, collect(DISTINCT sec.number) as sections
            LIMIT 10
            """
            result = self.graph_manager._run_query(query, {'standard': standard})
            
            for record in result:
                nodes.append(GraphNode(
                    id=f"std_ref_{record['doc_name']}_{standard}",
                    type='standard_reference',
                    name=f"{record['doc_name']} references {standard}",
                    properties={
                        'document': record['doc_name'],
                        'standard': standard,
                        'sections': record['sections']
                    },
                    depth=1
                ))
                
        except Exception as e:
            logger.debug(f"Standard context query failed: {e}")
        
        return nodes
    
    def _get_cross_references(self, standard: str) -> List[Dict[str, str]]:
        """Get cross-references for a standard"""
        refs = []
        
        try:
            # Find related standards
            query = """
            MATCH (s1:Standard {name: $standard})<-[:REFERS_TO]-(d:Document)-[:REFERS_TO]->(s2:Standard)
            WHERE s1 <> s2
            RETURN DISTINCT s2.name as related_standard, d.name as via_document
            LIMIT 10
            """
            result = self.graph_manager._run_query(query, {'standard': standard})
            
            for record in result:
                refs.append({
                    'source': standard,
                    'target': record['related_standard'],
                    'via': record['via_document'],
                    'type': 'co-reference'
                })
                
        except Exception as e:
            logger.debug(f"Cross-reference query failed: {e}")
        
        return refs
    
    def _build_combined_context(self, 
                                 vector_results: List[Dict],
                                 graph_results: List[GraphNode],
                                 paths: List[GraphPath]) -> str:
        """Build combined context from all sources"""
        context_parts = []
        
        # Add vector search context
        if vector_results:
            context_parts.append("=== Relevant Document Sections ===")
            for i, result in enumerate(vector_results[:5], 1):
                doc = result.get('metadata', {}).get('document_name', 'Unknown')
                section = result.get('metadata', {}).get('section_number', '')
                text = result.get('text', '')[:500]
                context_parts.append(f"\n[{i}] {doc} (Section {section})")
                context_parts.append(text)
        
        # Add graph context
        if graph_results:
            context_parts.append("\n\n=== Related Information from Knowledge Graph ===")
            for node in graph_results[:5]:
                context_parts.append(f"\n• {node.name}")
                if node.properties:
                    props = [f"{k}: {v}" for k, v in node.properties.items() 
                            if v and k not in ['id']]
                    if props:
                        context_parts.append(f"  ({', '.join(props[:3])})")
        
        return '\n'.join(context_parts)
    
    def _build_entity_summary(self, 
                               entities: Set[str],
                               graph_results: List[GraphNode]) -> Dict[str, List[str]]:
        """Build summary of entities found"""
        summary = {
            'standards': [],
            'sections': [],
            'documents': []
        }
        
        for entity in entities:
            if entity.startswith('section_'):
                summary['sections'].append(entity.replace('section_', ''))
            elif any(entity.startswith(p) for p in ['IS', 'EN', 'IEC', 'BS', 'NFPA', 'IEEE', 'ISO']):
                summary['standards'].append(entity)
        
        for node in graph_results:
            if node.type == 'standard_reference':
                doc = node.properties.get('document', '')
                if doc and doc not in summary['documents']:
                    summary['documents'].append(doc)
        
        return summary
    
    def _generate_reasoning_chain(self,
                                   query: str,
                                   vector_results: List[Dict],
                                   graph_results: List[GraphNode],
                                   paths: List[GraphPath]) -> List[str]:
        """Generate reasoning chain for transparency"""
        chain = []
        
        # Step 1: Query understanding
        entities = self._extract_entities(query)
        if entities:
            chain.append(f"Identified entities in query: {', '.join(list(entities)[:5])}")
        else:
            chain.append("No specific standards/sections identified in query")
        
        # Step 2: Vector search
        if vector_results:
            top_docs = set()
            for r in vector_results[:3]:
                doc = r.get('metadata', {}).get('document_name', '')
                if doc:
                    top_docs.add(doc)
            chain.append(f"Found relevant content in: {', '.join(top_docs)}")
        
        # Step 3: Graph expansion
        if graph_results:
            standards_found = set()
            for node in graph_results:
                if node.type == 'standard_reference':
                    std = node.properties.get('standard', '')
                    if std:
                        standards_found.add(std)
            if standards_found:
                chain.append(f"Related standards identified: {', '.join(standards_found)}")
        
        # Step 4: Cross-references
        if paths:
            chain.append(f"Found {len(paths)} cross-document relationships")
        
        return chain
    
    def get_answer_with_graph(self, 
                               query: str,
                               llm=None,
                               top_k: int = 10,
                               max_hops: int = 2) -> GraphRAGResult:
        """
        Get comprehensive answer using GraphRAG
        
        Args:
            query: User query
            llm: LLM for answer generation (optional)
            top_k: Number of results
            max_hops: Max graph traversal depth
            
        Returns:
            GraphRAGResult with answer, sources, and reasoning
        """
        start_time = time.time()
        
        # Step 1: Vector search
        vector_results = self._vector_search(query, top_k)
        logger.info(f"   📊 Vector search: {len(vector_results)} results")
        
        # Step 2: Extract entities
        query_entities = self._extract_entities(query)
        result_entities = set()
        for result in vector_results:
            text = result.get('text', '')
            result_entities.update(self._extract_entities(text))
        
        all_entities = query_entities | result_entities
        logger.info(f"   🏷️ Entities found: {len(all_entities)}")
        
        # Step 3: Graph traversal
        graph_data = {'nodes': [], 'paths': [], 'standards': [], 'cross_refs': []}
        if self.enabled and all_entities:
            graph_data = self._graph_traverse(all_entities)
            logger.info(f"   🕸️ Graph: {len(graph_data.get('nodes', []))} nodes")
        
        # Step 4: Build combined context
        combined_context = self._build_combined_context_nodes(
            vector_results, graph_data.get('nodes', [])
        )
        
        # Step 5: Generate reasoning chain
        reasoning_chain = self._generate_reasoning_chain(
            query, vector_results, graph_data.get('nodes', []), []
        )
        
        # Step 6: Convert cross-refs to GraphPath
        paths = []
        for ref in graph_data.get('cross_refs', []):
            paths.append(GraphPath(
                source=ref.get('source', ''),
                target=ref.get('target', ''),
                relationship=ref.get('type', 'REFERENCES'),
                strength=0.8
            ))
        
        # Step 7: Convert entities to GraphNode
        entity_nodes = []
        for entity in list(all_entities)[:10]:
            entity_type = 'STANDARD' if not entity.startswith('section_') else 'SECTION'
            entity_nodes.append(GraphNode(
                id=f"entity_{entity}",
                type=entity_type,
                name=entity,
                properties={'extracted_from': 'query_and_results'}
            ))
        
        # Step 8: Build context string for LLM
        context_str = self._build_combined_context(
            vector_results, graph_data.get('nodes', []), []
        )
        
        # Step 9: Generate answer
        answer = ""
        if llm:
            try:
                prompt = f"""Based on the following context, answer the question.

Context:
{context_str[:4000]}

Question: {query}

Provide a detailed, accurate answer based on the context. If the context mentions specific standards or specifications, include them in your answer."""
                
                response = llm.complete(prompt)
                answer = str(response)
            except Exception as e:
                logger.warning(f"LLM generation failed: {e}")
                answer = "Found relevant information but could not generate answer."
        else:
            # Without LLM, return context summary
            answer = f"Found {len(vector_results)} relevant sections and {len(graph_data.get('nodes', []))} related graph nodes.\n\n{context_str[:1500]}"
        
        total_time = time.time() - start_time
        logger.info(f"   ⚡ GraphRAG completed in {total_time:.3f}s")
        
        return GraphRAGResult(
            query=query,
            answer=answer,
            vector_results=vector_results,
            graph_results=graph_data.get('nodes', []),
            entities=entity_nodes,
            paths=paths,
            combined_context=combined_context,
            reasoning_chain=reasoning_chain
        )
    
    def _build_combined_context_nodes(self,
                                       vector_results: List[Dict],
                                       graph_nodes: List[GraphNode]) -> List:
        """Build combined context as list of nodes"""
        from dataclasses import dataclass, field
        
        @dataclass
        class ContextNode:
            text: str
            metadata: Dict = field(default_factory=dict)
        
        combined = []
        
        # Add vector results
        for result in vector_results[:7]:
            combined.append(ContextNode(
                text=result.get('text', ''),
                metadata={
                    **result.get('metadata', {}),
                    'source_type': 'vector',
                    'score': result.get('score', 0)
                }
            ))
        
        # Add graph nodes as context
        for node in graph_nodes[:5]:
            text = f"{node.name}\n"
            if node.properties:
                props = [f"{k}: {v}" for k, v in node.properties.items() if v]
                text += ", ".join(props[:5])
            
            combined.append(ContextNode(
                text=text,
                metadata={
                    'source_type': 'graph',
                    'node_type': node.type,
                    'node_id': node.id
                }
            ))
        
        return combined
    
    def get_entity_context(self,
                           entity_name: str,
                           entity_type: str = "STANDARD",
                           max_hops: int = 2) -> Dict[str, Any]:
        """
        Get all context related to a specific entity
        
        Args:
            entity_name: Name of entity (e.g., "IS10101")
            entity_type: Type (STANDARD, SPECIFICATION, etc.)
            max_hops: Traversal depth
            
        Returns:
            Dict with entity info and related data
        """
        logger.info(f"🔍 Getting entity context: {entity_name}")
        
        result = {
            'entity': entity_name,
            'type': entity_type,
            'related_entities': [],
            'relevant_chunks': [],
            'relationships': []
        }
        
        if not self.graph_manager:
            result['error'] = 'Graph manager not available'
            return result
        
        try:
            # Get related standards
            if entity_type == "STANDARD":
                nodes = self._get_standard_context(entity_name)
                result['related_entities'] = [
                    {'name': n.name, 'type': n.type, 'properties': n.properties}
                    for n in nodes
                ]
                
                # Get cross-references
                refs = self._get_cross_references(entity_name)
                result['relationships'] = refs
            
            # Get vector chunks mentioning this entity
            if self.vector_searcher:
                try:
                    chunks = self._vector_search(entity_name, top_k=5)
                    result['relevant_chunks'] = [
                        {
                            'text': c.get('text', '')[:300],
                            'document': c.get('metadata', {}).get('document_name', 'Unknown'),
                            'score': c.get('score', 0)
                        }
                        for c in chunks
                    ]
                except Exception:
                    pass
            
            logger.info(f"   ✅ Found {len(result['related_entities'])} related entities")
            return result
            
        except Exception as e:
            logger.error(f"❌ Entity context failed: {e}")
            result['error'] = str(e)
            return result
    
    def discover_cross_references(self,
                                   document_name: str,
                                   relationship_types: List[str] = None) -> Dict[str, List]:
        """
        Discover cross-references from/to a document
        
        Args:
            document_name: Document to analyze
            relationship_types: Filter by type (REFERENCES, SUPERSEDES, etc.)
            
        Returns:
            Dict with outgoing and incoming references
        """
        logger.info(f"🔍 Discovering cross-references for: {document_name}")
        
        result = {
            'outgoing': [],
            'incoming': []
        }
        
        if not self.graph_manager:
            return result
        
        try:
            # Outgoing references (this doc references others)
            query_out = """
            MATCH (d:Document {name: $doc_name})-[r:REFERS_TO]->(s:Standard)
            RETURN s.name as target, type(r) as rel_type
            LIMIT 20
            """
            refs_out = self.graph_manager._run_query(
                query_out, {'doc_name': document_name}
            )
            
            for ref in refs_out:
                rel_type = ref.get('rel_type', 'REFERENCES')
                if relationship_types and rel_type not in relationship_types:
                    continue
                result['outgoing'].append({
                    'target': ref.get('target', ''),
                    'relationship': rel_type
                })
            
            # Incoming references (others reference this doc)
            query_in = """
            MATCH (d:Document)-[r:REFERS_TO]->(s:Standard {name: $doc_name})
            RETURN d.name as source, type(r) as rel_type
            LIMIT 20
            """
            refs_in = self.graph_manager._run_query(
                query_in, {'doc_name': document_name}
            )
            
            for ref in refs_in:
                rel_type = ref.get('rel_type', 'REFERENCES')
                if relationship_types and rel_type not in relationship_types:
                    continue
                result['incoming'].append({
                    'source': ref.get('source', ''),
                    'relationship': rel_type
                })
            
            logger.info(f"   ✅ Found {len(result['outgoing'])} outgoing, {len(result['incoming'])} incoming refs")
            return result
            
        except Exception as e:
            logger.error(f"❌ Cross-reference discovery failed: {e}")
            return result


# Singleton instance
_graph_rag: Optional[GraphRAG] = None


def get_graph_rag(
    neo4j_uri: str = None,
    neo4j_user: str = None,
    neo4j_password: str = None,
    qdrant_client=None,
    collection_name: str = None,
    graph_manager=None,
    vector_searcher=None
) -> Optional[GraphRAG]:
    """
    Get or create GraphRAG singleton
    
    Args:
        neo4j_uri: Neo4j connection URI
        neo4j_user: Neo4j username
        neo4j_password: Neo4j password
        qdrant_client: Qdrant client for vector search
        collection_name: Qdrant collection name
        graph_manager: Pre-configured graph manager
        vector_searcher: Pre-configured vector searcher
        
    Returns:
        GraphRAG instance or None if unavailable
    """
    global _graph_rag
    
    # Try to create graph manager from Neo4j credentials
    if graph_manager is None and neo4j_uri and neo4j_user and neo4j_password:
        try:
            from src.graph_manager import get_graph_manager
            graph_manager = get_graph_manager()
            if graph_manager and graph_manager.is_connected():
                logger.info("✅ Connected to Neo4j for GraphRAG")
            else:
                graph_manager = None
                logger.warning("⚠️ Neo4j connection not available")
        except ImportError:
            logger.warning("⚠️ graph_manager module not available")
            graph_manager = None
        except Exception as e:
            logger.warning(f"⚠️ Failed to connect to Neo4j: {e}")
            graph_manager = None
    
    if _graph_rag is None:
        _graph_rag = GraphRAG(
            graph_manager=graph_manager,
            vector_searcher=vector_searcher
        )
    else:
        if graph_manager:
            _graph_rag.graph_manager = graph_manager
        if vector_searcher:
            _graph_rag.vector_searcher = vector_searcher
    
    return _graph_rag


if __name__ == "__main__":
    # Test the module
    logger.info("Testing GraphRAG...")
    
    graph_rag = get_graph_rag()
    
    test_query = "What are the cable requirements according to IEC 60364?"
    
    # Test entity extraction
    entities = graph_rag._extract_entities(test_query)
    print(f"\n📋 Extracted Entities: {entities}")
    
    # Test reasoning chain generation
    chain = graph_rag._generate_reasoning_chain(
        test_query,
        [{'text': 'Cable specifications...', 'metadata': {'document_name': 'IEC 60364-5-52'}}],
        [],
        []
    )
    print(f"\n🔗 Reasoning Chain:")
    for step in chain:
        print(f"   • {step}")
