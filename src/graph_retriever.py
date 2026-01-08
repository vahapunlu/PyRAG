"""
Graph Retriever

Enhance RAG with knowledge graph cross-references.
"""

from typing import List, Dict, Optional
from loguru import logger
from src.graph_manager import get_graph_manager
from src.reference_extractor import get_reference_extractor


class GraphRetriever:
    """
    Retrieve related information using knowledge graph
    
    Features:
    - Extract standards/sections from queries
    - Find cross-references using graph
    - Enhance vector search results with graph context
    """
    
    def __init__(self):
        """Initialize graph retriever"""
        self.graph_manager = get_graph_manager()
        self.reference_extractor = get_reference_extractor()
        
        if not self.graph_manager:
            logger.warning("⚠️ Graph manager not available - graph features disabled")
            self.enabled = False
        else:
            self.enabled = True
            logger.info("✅ Graph Retriever initialized")
    
    def get_cross_references(self, query: str, max_hops: int = 2) -> Dict:
        """
        Get cross-references for entities mentioned in query
        
        Args:
            query: User query
            max_hops: Maximum traversal depth (1-3)
            
        Returns:
            {
                'enabled': bool,
                'entities_found': List[str],
                'references': List[Dict],
                'summary': str
            }
        """
        if not self.enabled:
            return {
                'enabled': False,
                'entities_found': [],
                'references': [],
                'summary': ''
            }
        
        # Extract entities from query
        extracted = self.reference_extractor.extract_all(query)
        entities = []
        
        # Add standards
        for std in extracted['standards']:
            entities.append(std['full'])
        
        # Add section numbers
        for sec in extracted['sections']:
            entities.append(sec['number'])
        
        if not entities:
            return {
                'enabled': True,
                'entities_found': [],
                'references': [],
                'summary': ''
            }
        
        logger.info(f"🔍 Found entities in query: {entities}")
        
        # Get cross-references for each entity
        all_references = []
        seen = set()
        
        for entity in entities:
            refs = self.graph_manager.get_cross_references(entity, max_hops)
            
            for ref in refs:
                ref_id = f"{ref['type']}:{ref['name']}"
                if ref_id not in seen:
                    seen.add(ref_id)
                    all_references.append(ref)
        
        # Generate summary
        summary = self._generate_summary(entities, all_references)
        
        return {
            'enabled': True,
            'entities_found': entities,
            'references': all_references,
            'summary': summary
        }
    
    def enhance_results(self, 
                       query: str,
                       vector_results: List[Dict],
                       max_hops: int = 2) -> Dict:
        """
        Enhance vector search results with graph context
        
        Args:
            query: User query
            vector_results: Results from vector search
            max_hops: Graph traversal depth
            
        Returns:
            {
                'enhanced_results': List[Dict],  # Original + graph context
                'graph_info': Dict,              # Cross-reference info
                'enhancement_applied': bool
            }
        """
        if not self.enabled:
            return {
                'enhanced_results': vector_results,
                'graph_info': {},
                'enhancement_applied': False
            }
        
        # Get cross-references
        graph_info = self.get_cross_references(query, max_hops)
        
        if not graph_info['references']:
            return {
                'enhanced_results': vector_results,
                'graph_info': graph_info,
                'enhancement_applied': False
            }
        
        # Add graph context to results
        enhanced = []
        for result in vector_results:
            enhanced_result = result.copy()
            enhanced_result['graph_context'] = {
                'cross_references': graph_info['references'][:5],  # Top 5
                'summary': graph_info['summary']
            }
            enhanced.append(enhanced_result)
        
        logger.info(f"✅ Enhanced {len(vector_results)} results with graph context")
        
        return {
            'enhanced_results': enhanced,
            'graph_info': graph_info,
            'enhancement_applied': True
        }
    
    def get_document_context(self, document_name: str) -> Dict:
        """
        Get full graph context for a document
        
        Args:
            document_name: Document name
            
        Returns:
            Document references and statistics
        """
        if not self.enabled:
            return {}
        
        return self.graph_manager.get_document_references(document_name)
    
    def _generate_summary(self, entities: List[str], references: List[Dict]) -> str:
        """Generate human-readable summary of cross-references"""
        if not references:
            return ""
        
        # Count by type
        by_type = {}
        learned_count = 0
        
        for ref in references:
            ref_type = ref['type'][0] if ref['type'] else 'Unknown'
            by_type[ref_type] = by_type.get(ref_type, 0) + 1
            
            # Check for learned relationships
            if 'COMPLEMENTS' in ref.get('relationship_types', []):
                learned_count += 1
        
        # Build summary
        parts = []
        if 'STANDARD' in by_type:
            parts.append(f"{by_type['STANDARD']} ilgili standart")
        if 'SECTION' in by_type:
            parts.append(f"{by_type['SECTION']} bölüm")
        if 'DOCUMENT' in by_type:
            parts.append(f"{by_type['DOCUMENT']} döküman")
        
        if learned_count > 0:
            parts.append(f"**{learned_count} adet öğrenilmiş ilişki**")
        
        if not parts:
            return ""
        
        return f"Graph analizinde {', '.join(parts)} tespit edilmiştir."
    
    def get_statistics(self) -> Dict:
        """Get graph statistics"""
        if not self.enabled:
            return {
                'enabled': False,
                'message': 'Graph features not available'
            }
        
        stats = self.graph_manager.get_graph_statistics()
        stats['enabled'] = True
        return stats


# Singleton instance
_graph_retriever = None

def get_graph_retriever() -> Optional[GraphRetriever]:
    """Get or create graph retriever singleton"""
    global _graph_retriever
    
    if _graph_retriever is None:
        try:
            _graph_retriever = GraphRetriever()
        except Exception as e:
            logger.warning(f"⚠️ Could not initialize graph retriever: {e}")
            return None
    
    return _graph_retriever
