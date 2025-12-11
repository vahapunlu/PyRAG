"""
Graph Builder

Automatically builds knowledge graph from Qdrant documents.
Extracts references and creates nodes/relationships in Neo4j.
"""

from typing import List, Dict, Optional
from loguru import logger
from src.reference_extractor import get_reference_extractor
from src.graph_manager import get_graph_manager
from src.utils import get_settings
import qdrant_client


class GraphBuilder:
    """
    Build knowledge graph from document collection
    
    Process:
    1. Get all documents from Qdrant
    2. Extract references using ReferenceExtractor
    3. Create nodes in Neo4j (documents, sections, standards)
    4. Create relationships (CONTAINS, REFERS_TO)
    """
    
    def __init__(self, collection_name: str = "default"):
        """
        Initialize graph builder
        
        Args:
            collection_name: Collection name
        """
        self.settings = get_settings()
        self.collection_name = collection_name
        self.reference_extractor = get_reference_extractor()
        self.graph_manager = get_graph_manager()
        
        if not self.graph_manager:
            raise ValueError("Graph manager not configured. Check .env.neo4j file.")
        
        logger.info(f"✅ Graph Builder initialized for collection: {collection_name}")
    
    def build_graph(self, clear_existing: bool = False):
        """
        Build complete knowledge graph from Qdrant
        
        Args:
            clear_existing: Clear existing graph before building (default: False)
        """
        if clear_existing:
            logger.warning("⚠️ Clearing existing graph...")
            self.graph_manager.clear_graph()
        
        logger.info("🏗️ Building knowledge graph...")
        
        # Step 1: Create indexes
        self.graph_manager.create_indexes()
        
        # Step 2: Get all documents from Qdrant
        documents = self._get_documents_from_qdrant()
            
        logger.info(f"   Found {len(documents)} unique documents")
        
        # Step 3: Process each document
        stats = {
            'documents': 0,
            'sections': 0,
            'standards': 0,
            'relationships': 0
        }
        
        for doc_name, doc_data in documents.items():
            self._process_document(doc_name, doc_data, stats)
        
        # Step 4: Summary
        graph_stats = self.graph_manager.get_graph_statistics()
        logger.success(f"✅ Graph built successfully!")
        logger.info(f"   Nodes: {graph_stats['total_nodes']} (Docs: {graph_stats['documents']}, "
                   f"Sections: {graph_stats['sections']}, Standards: {graph_stats['standards']})")
        logger.info(f"   Relationships: {graph_stats['relationships']}")
        
        return graph_stats
    
    def _get_documents_from_qdrant(self) -> Dict[str, Dict]:
        """
        Get all documents from Qdrant collection
        
        Returns:
            Dict of {doc_name: {metadata, chunks}}
        """
        try:
            client = qdrant_client.QdrantClient(path=self.settings.qdrant_path)
            
            # Scroll through all points
            offset = None
            documents = {}
            
            while True:
                points, next_offset = client.scroll(
                    collection_name=self.collection_name,
                    limit=100,
                    offset=offset,
                    with_payload=True,
                    with_vectors=False
                )
                
                for point in points:
                    metadata = point.payload or {}
                    # LlamaIndex stores text in 'text' or '_node_content'
                    text = metadata.get('text')
                    if not text:
                        node_content = metadata.get('_node_content')
                        if isinstance(node_content, str):
                            import json
                            try:
                                node_content = json.loads(node_content)
                                text = node_content.get('text', '')
                            except:
                                pass
                    
                    if not text:
                        continue
                        
                    doc_name = metadata.get('document_name', metadata.get('file_name', 'Unknown'))
                    
                    if doc_name not in documents:
                        documents[doc_name] = {
                            'name': doc_name,
                            'metadata': {
                                'file_name': metadata.get('file_name', ''),
                                'standard_no': metadata.get('standard_no', ''),
                                'date': metadata.get('date', ''),
                                'description': metadata.get('description', ''),
                            },
                            'chunks': [],
                            'sections': set()
                        }
                    
                    # Add chunk
                    documents[doc_name]['chunks'].append({
                        'text': text,
                        'metadata': metadata
                    })
                    
                    # Track sections
                    section = metadata.get('section_number', '')
                    if section:
                        documents[doc_name]['sections'].add(section)
                
                offset = next_offset
                if offset is None:
                    break
            
            return documents
            
        except Exception as e:
            logger.error(f"Error fetching documents from Qdrant: {e}")
            return {}
    
    def _process_document(self, doc_name: str, doc_data: Dict, stats: Dict):
        """
        Process a single document: create nodes and relationships
        
        Args:
            doc_name: Document name
            doc_data: Document data (metadata, chunks, sections)
            stats: Statistics dict to update
        """
        logger.info(f"📄 Processing: {doc_name}")
        
        # Step 1: Create document node
        doc_properties = {
            'file_name': doc_data['metadata']['file_name'],
            'standard_no': doc_data['metadata']['standard_no'],
            'date': doc_data['metadata']['date'],
            'description': doc_data['metadata']['description'],
            'total_chunks': len(doc_data['chunks']),
            'total_sections': len(doc_data['sections'])
        }
        self.graph_manager.create_document_node(doc_name, doc_properties)
        stats['documents'] += 1
        
        # Step 2: Extract references from all chunks
        all_text = ' '.join([chunk['text'] for chunk in doc_data['chunks']])
        references = self.reference_extractor.extract_all(all_text)
        
        logger.info(f"   Found {references['summary']['total_standards']} standard references")
        logger.info(f"   Found {references['summary']['total_sections']} section references")
        
        # Step 3: Create standard nodes and relationships
        seen_standards = set()
        for std_ref in references['standards']:
            std_name = std_ref['full']
            
            if std_name not in seen_standards:
                seen_standards.add(std_name)
                
                # Create standard node
                std_properties = {
                    'type': std_ref['type'],
                    'number': std_ref['number']
                }
                self.graph_manager.create_standard_node(std_name, std_properties)
                stats['standards'] += 1
                
                # Create REFERS_TO relationship
                self.graph_manager.create_refers_to_relationship(
                    doc_name,
                    std_name,
                    source_type="DOCUMENT"
                )
                stats['relationships'] += 1
        
        # Step 4: Create section nodes
        for section_number in sorted(doc_data['sections']):
            # Find section metadata from chunks
            section_meta = self._find_section_metadata(section_number, doc_data['chunks'])
            
            section_properties = {
                'title': section_meta.get('section_title', ''),
                'page': section_meta.get('page_number', ''),
            }
            
            self.graph_manager.create_section_node(
                doc_name,
                section_number,
                section_properties
            )
            stats['sections'] += 1
            
            # Check if this section refers to any standards
            section_chunks = [c for c in doc_data['chunks'] 
                            if c['metadata'].get('section_number') == section_number]
            section_text = ' '.join([c['text'] for c in section_chunks])
            section_refs = self.reference_extractor.extract_standards(section_text)
            
            for std_ref in section_refs[:3]:  # Limit to top 3 per section
                std_name = std_ref['full']
                if std_name in seen_standards:
                    self.graph_manager.create_refers_to_relationship(
                        section_number,
                        std_name,
                        source_type="SECTION",
                        properties={'page': section_meta.get('page_number', '')}
                    )
                    stats['relationships'] += 1
    
    def _find_section_metadata(self, section_number: str, chunks: List[Dict]) -> Dict:
        """Find metadata for a specific section"""
        for chunk in chunks:
            if chunk['metadata'].get('section_number') == section_number:
                return {
                    'section_title': chunk['metadata'].get('section_title', ''),
                    'page_number': chunk['metadata'].get('page_number', ''),
                }
        return {}
    
    def get_build_statistics(self) -> Dict:
        """Get current graph statistics"""
        if not self.graph_manager:
            return {}
        return self.graph_manager.get_graph_statistics()
    
    def add_document(self, doc_id: str, text: str, metadata: Dict):
        """
        Add a single document to the graph
        
        Args:
            doc_id: Document ID
            text: Document text content
            metadata: Document metadata (file_name, section_number, etc.)
        """
        if not self.graph_manager:
            logger.warning("⚠️ Graph manager not available")
            return
        
        try:
            file_name = metadata.get('file_name', 'Unknown')
            section_number = metadata.get('section_number', '')
            section_title = metadata.get('section_title', '')
            
            # Create document node if not exists
            self.graph_manager.create_document_node(
                name=file_name,
                properties=metadata
            )
            
            # If has section info, create section node
            if section_number:
                section_props = {
                    'title': section_title,
                    'page': metadata.get('page_number', '')
                }
                
                self.graph_manager.create_section_node(
                    document_name=file_name,
                    section_number=section_number,
                    properties=section_props
                )
            
            # Extract and add references
            extracted_refs = self.reference_extractor.extract_all(text)
            
            # Process standard references
            for ref in extracted_refs['standards']:
                # Create standard node
                self.graph_manager.create_standard_node(
                    name=ref['full'],
                    properties={
                        'type': ref['type'],
                        'number': ref['number']
                    }
                )
                
                # Create REFERS_TO relationship
                source_name = section_number if section_number else file_name
                source_type = "SECTION" if section_number else "DOCUMENT"
                
                self.graph_manager.create_refers_to_relationship(
                    source_name=source_name,
                    target_standard=ref['full'],
                    source_type=source_type,
                    properties={'context': text[:200]}
                )
            
        except Exception as e:
            logger.warning(f"Failed to add document to graph: {e}")


def build_graph_from_qdrant(collection_name: str = "default", 
                          clear_existing: bool = False) -> Dict:
    """
    Convenience function to build graph from Qdrant
    
    Args:
        collection_name: Collection name
        clear_existing: Clear existing graph
        
    Returns:
        Graph statistics
    """
    builder = GraphBuilder(collection_name=collection_name)
    stats = builder.build_graph(clear_existing=clear_existing)
    builder.graph_manager.close()
    return stats
