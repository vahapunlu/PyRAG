"""
Neo4j Graph Manager

Manages knowledge graph in Neo4j for cross-reference tracking.
Handles document nodes, section nodes, standard nodes, and relationships.
"""

from typing import List, Dict, Optional
from neo4j import GraphDatabase
from loguru import logger
from datetime import datetime
import os


class GraphManager:
    """
    Neo4j graph database manager for PyRAG
    
    Node Types:
    - DOCUMENT: Technical documents (IS3218, etc.)
    - SECTION: Document sections (6.5.1, Annex A, etc.)
    - STANDARD: Referenced standards (EN 54-11, etc.)
    
    Relationship Types:
    - CONTAINS: Document contains Section
    - REFERS_TO: Document/Section refers to Standard
    - CITES: Cross-references between documents
    """
    
    def __init__(self, uri: str, username: str, password: str, database: str = "neo4j"):
        """
        Initialize Neo4j connection
        
        Args:
            uri: Neo4j connection URI
            username: Neo4j username
            password: Neo4j password
            database: Database name (default: neo4j)
        """
        self.uri = uri
        self.username = username
        self.user = username  # Alias for compatibility
        self.password = password
        self.database = database
        
        try:
            self.driver = GraphDatabase.driver(uri, auth=(username, password))
            # Test connection
            with self.driver.session(database=database) as session:
                result = session.run("RETURN 1 AS test")
                result.single()
            logger.success(f"✅ Connected to Neo4j at {uri}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Neo4j: {e}")
            raise
    
    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
            logger.info("🔌 Neo4j connection closed")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
    
    def clear_graph(self):
        """Clear all nodes and relationships (use with caution!)"""
        with self.driver.session(database=self.database) as session:
            session.run("MATCH (n) DETACH DELETE n")
        logger.warning("⚠️ Graph cleared!")
    
    def create_indexes(self):
        """Create indexes for better query performance"""
        with self.driver.session(database=self.database) as session:
            # Document index
            session.run("""
                CREATE INDEX document_name IF NOT EXISTS
                FOR (d:DOCUMENT) ON (d.name)
            """)
            
            # Section index
            session.run("""
                CREATE INDEX section_number IF NOT EXISTS
                FOR (s:SECTION) ON (s.number)
            """)
            
            # Standard index
            session.run("""
                CREATE INDEX standard_name IF NOT EXISTS
                FOR (st:STANDARD) ON (st.name)
            """)
        
        logger.success("✅ Indexes created")
    
    def create_document_node(self, name: str, properties: Dict = None) -> str:
        """
        Create a document node
        
        Args:
            name: Document name (e.g., "IS3218 2024")
            properties: Additional properties (title, year, pages, etc.)
            
        Returns:
            Node ID
        """
        properties = properties or {}
        properties['name'] = name
        
        with self.driver.session(database=self.database) as session:
            result = session.run("""
                MERGE (d:DOCUMENT {name: $name})
                SET d += $properties
                RETURN elementId(d) as id
            """, name=name, properties=properties)
            
            node_id = result.single()['id']
            logger.info(f"📄 Created/Updated DOCUMENT: {name}")
            return node_id
    
    def create_section_node(self, document_name: str, section_number: str, properties: Dict = None) -> str:
        """
        Create a section node and link to document
        
        Args:
            document_name: Parent document name
            section_number: Section number (e.g., "6.5.1")
            properties: Additional properties (title, page, content_summary, etc.)
            
        Returns:
            Node ID
        """
        properties = properties or {}
        properties['number'] = section_number
        properties['document'] = document_name
        
        with self.driver.session(database=self.database) as session:
            result = session.run("""
                MATCH (d:DOCUMENT {name: $doc_name})
                MERGE (s:SECTION {number: $section_number, document: $doc_name})
                SET s += $properties
                MERGE (d)-[:CONTAINS]->(s)
                RETURN elementId(s) as id
            """, doc_name=document_name, section_number=section_number, properties=properties)
            
            node_id = result.single()['id']
            logger.info(f"📑 Created/Updated SECTION: {section_number} in {document_name}")
            return node_id
    
    def create_standard_node(self, name: str, properties: Dict = None) -> str:
        """
        Create a standard node
        
        Args:
            name: Standard name (e.g., "EN 54-11")
            properties: Additional properties (organization, year, etc.)
            
        Returns:
            Node ID
        """
        properties = properties or {}
        properties['name'] = name
        
        with self.driver.session(database=self.database) as session:
            result = session.run("""
                MERGE (st:STANDARD {name: $name})
                SET st += $properties
                RETURN elementId(st) as id
            """, name=name, properties=properties)
            
            node_id = result.single()['id']
            logger.info(f"📘 Created/Updated STANDARD: {name}")
            return node_id
    
    def create_refers_to_relationship(self, source_name: str, target_standard: str, 
                                     source_type: str = "DOCUMENT", properties: Dict = None):
        """
        Create REFERS_TO relationship
        
        Args:
            source_name: Source node name (document or section)
            target_standard: Target standard name
            source_type: Source node type (DOCUMENT or SECTION)
            properties: Additional relationship properties (context, page, etc.)
        """
        properties = properties or {}
        
        with self.driver.session(database=self.database) as session:
            if source_type == "DOCUMENT":
                query = """
                    MATCH (source:DOCUMENT {name: $source_name})
                    MATCH (target:STANDARD {name: $target_standard})
                    MERGE (source)-[r:REFERS_TO]->(target)
                    SET r += $properties
                """
            else:  # SECTION
                query = """
                    MATCH (source:SECTION {number: $source_name})
                    MATCH (target:STANDARD {name: $target_standard})
                    MERGE (source)-[r:REFERS_TO]->(target)
                    SET r += $properties
                """
            
            session.run(query, source_name=source_name, target_standard=target_standard, properties=properties)
            logger.info(f"🔗 Created REFERS_TO: {source_name} → {target_standard}")
    
    def get_cross_references(self, entity_name: str, max_hops: int = 2) -> List[Dict]:
        """
        Get cross-references for an entity (multi-hop traversal)
        
        Args:
            entity_name: Entity to start from (document, section, or standard)
            max_hops: Maximum relationship hops (default: 2)
            
        Returns:
            List of related entities with paths
        """
        with self.driver.session(database=self.database) as session:
            # Build query with literal max_hops (Cypher doesn't allow params in path length)
            query = f"""
                MATCH path = (start)-[*1..{max_hops}]-(related)
                WHERE start.name = $entity_name OR start.number = $entity_name
                RETURN 
                    labels(related) as type,
                    COALESCE(related.name, related.number) as name,
                    related as properties,
                    length(path) as hops,
                    [r in relationships(path) | type(r)] as relationship_types
                ORDER BY hops
                LIMIT 50
            """
            result = session.run(query, entity_name=entity_name)
            
            references = []
            for record in result:
                references.append({
                    'type': record['type'][0],
                    'name': record['name'],
                    'properties': dict(record['properties']),
                    'hops': record['hops'],
                    'relationship_types': record['relationship_types']
                })
            
            return references
    
    def get_document_references(self, document_name: str) -> Dict:
        """
        Get all references from a document
        
        Args:
            document_name: Document name
            
        Returns:
            Dict with standards, sections, and cross-refs
        """
        with self.driver.session(database=self.database) as session:
            # Get referenced standards
            standards_result = session.run("""
                MATCH (d:DOCUMENT {name: $doc_name})-[:REFERS_TO]->(st:STANDARD)
                RETURN st.name as standard
            """, doc_name=document_name)
            
            standards = [record['standard'] for record in standards_result]
            
            # Get sections
            sections_result = session.run("""
                MATCH (d:DOCUMENT {name: $doc_name})-[:CONTAINS]->(s:SECTION)
                RETURN s.number as section, s.title as title
                ORDER BY s.number
            """, doc_name=document_name)
            
            sections = [{'number': r['section'], 'title': r.get('title')} for r in sections_result]
            
            return {
                'document': document_name,
                'standards': standards,
                'sections': sections,
                'total_standards': len(standards),
                'total_sections': len(sections)
            }
    
    def get_graph_statistics(self) -> Dict:
        """Get graph statistics"""
        with self.driver.session(database=self.database) as session:
            result = session.run("""
                MATCH (n)
                RETURN 
                    count(CASE WHEN 'DOCUMENT' IN labels(n) THEN 1 END) as documents,
                    count(CASE WHEN 'SECTION' IN labels(n) THEN 1 END) as sections,
                    count(CASE WHEN 'STANDARD' IN labels(n) THEN 1 END) as standards,
                    count(n) as total_nodes
            """)
            
            stats = dict(result.single())
            
            # Get relationship count
            rel_result = session.run("MATCH ()-[r]->() RETURN count(r) as relationships")
            stats['relationships'] = rel_result.single()['relationships']
            
            return stats
    
    def create_learned_relationship(
        self,
        doc1: str,
        doc2: str,
        rel_type: str,
        weight: float,
        metadata: Dict = None
    ):
        """
        Create a learned relationship between two documents
        
        Args:
            doc1: First document name
            doc2: Second document name
            rel_type: Relationship type (e.g., 'COMPLEMENTS', 'RELATED_TO')
            weight: Relationship weight/confidence (0-1)
            metadata: Additional metadata
        """
        with self.driver.session(database=self.database) as session:
            properties = {
                'weight': weight,
                'learned': True,
                'created_at': datetime.now().isoformat()
            }
            if metadata:
                properties.update(metadata)
            
            query = f"""
                MATCH (d1:DOCUMENT {{name: $doc1}})
                MATCH (d2:DOCUMENT {{name: $doc2}})
                MERGE (d1)-[r:{rel_type}]->(d2)
                SET r += $properties
                RETURN r
            """
            session.run(query, doc1=doc1, doc2=doc2, properties=properties)
            logger.debug(f"🔗 Created learned relationship: {doc1} -[{rel_type}:{weight:.2f}]-> {doc2}")
    
    def get_relationship_weight(self, doc1: str, doc2: str, rel_type: str) -> Optional[float]:
        """
        Get weight of a relationship
        
        Args:
            doc1: First document name
            doc2: Second document name
            rel_type: Relationship type
            
        Returns:
            Weight value or None if relationship doesn't exist
        """
        with self.driver.session(database=self.database) as session:
            query = f"""
                MATCH (d1:DOCUMENT {{name: $doc1}})-[r:{rel_type}]->(d2:DOCUMENT {{name: $doc2}})
                RETURN r.weight as weight
            """
            result = session.run(query, doc1=doc1, doc2=doc2)
            record = result.single()
            return record['weight'] if record else None
    
    def update_relationship_weight(self, doc1: str, doc2: str, rel_type: str, new_weight: float):
        """
        Update weight of an existing relationship
        
        Args:
            doc1: First document name
            doc2: Second document name
            rel_type: Relationship type
            new_weight: New weight value
        """
        with self.driver.session(database=self.database) as session:
            query = f"""
                MATCH (d1:DOCUMENT {{name: $doc1}})-[r:{rel_type}]->(d2:DOCUMENT {{name: $doc2}})
                SET r.weight = $new_weight, r.updated_at = $timestamp
                RETURN r
            """
            session.run(
                query,
                doc1=doc1,
                doc2=doc2,
                new_weight=new_weight,
                timestamp=datetime.now().isoformat()
            )
    
    def get_learned_relationship_stats(self) -> Dict:
        """
        Get statistics about learned relationships
        
        Returns:
            Statistics dictionary
        """
        with self.driver.session(database=self.database) as session:
            result = session.run("""
                MATCH ()-[r]->()
                WHERE r.learned = true
                RETURN 
                    count(r) as total_learned,
                    avg(r.weight) as avg_weight,
                    max(r.weight) as max_weight,
                    min(r.weight) as min_weight,
                    count(DISTINCT type(r)) as relationship_types
            """)
            
            record = result.single()
            if record and record['total_learned'] > 0:
                return dict(record)
            else:
                return {
                    'total_learned': 0,
                    'avg_weight': 0,
                    'max_weight': 0,
                    'min_weight': 0,
                    'relationship_types': 0
                }
    
    def prune_learned_relationships(self, min_weight: float) -> int:
        """
        Remove learned relationships below weight threshold
        
        Args:
            min_weight: Minimum weight to keep
            
        Returns:
            Number of relationships removed
        """
        with self.driver.session(database=self.database) as session:
            result = session.run("""
                MATCH ()-[r]->()
                WHERE r.learned = true AND r.weight < $min_weight
                DELETE r
                RETURN count(r) as deleted
            """, min_weight=min_weight)
            
            record = result.single()
            return record['deleted'] if record else 0
    
    def get_related_documents(
        self,
        doc_name: str,
        rel_types: List[str] = None,
        min_weight: float = 0.0
    ) -> List[Dict]:
        """
        Get related documents based on learned relationships
        
        Args:
            doc_name: Document name
            rel_types: List of relationship types to consider (None = all)
            min_weight: Minimum relationship weight
            
        Returns:
            List of related documents with weights
        """
        with self.driver.session(database=self.database) as session:
            if rel_types:
                rel_filter = " OR ".join([f"type(r) = '{rt}'" for rt in rel_types])
                where_clause = f"WHERE ({rel_filter}) AND r.weight >= $min_weight"
            else:
                where_clause = "WHERE r.weight >= $min_weight"
            
            query = f"""
                MATCH (d1:DOCUMENT {{name: $doc_name}})-[r]-(d2:DOCUMENT)
                {where_clause}
                RETURN 
                    d2.name as document,
                    type(r) as relationship_type,
                    r.weight as weight,
                    r.learned as learned
                ORDER BY r.weight DESC
                LIMIT 10
            """
            
            result = session.run(query, doc_name=doc_name, min_weight=min_weight)
            
            related = []
            for record in result:
                related.append({
                    'document': record['document'],
                    'relationship_type': record['relationship_type'],
                    'weight': record['weight'],
                    'learned': record.get('learned', False)
                })
            
            return related


def get_graph_manager() -> Optional[GraphManager]:
    """
    Get or create graph manager singleton
    
    Reads credentials from .env.neo4j file
    
    Returns:
        GraphManager instance or None if not configured
    """
    env_file = os.path.join(os.path.dirname(__file__), '..', '.env.neo4j')
    
    if not os.path.exists(env_file):
        logger.warning("⚠️ .env.neo4j not found. Graph features disabled.")
        return None
    
    # Read credentials
    credentials = {}
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                credentials[key] = value
    
    if not all(k in credentials for k in ['NEO4J_URI', 'NEO4J_USERNAME', 'NEO4J_PASSWORD']):
        logger.error("❌ Invalid .env.neo4j file. Missing required credentials.")
        return None
    
    try:
        manager = GraphManager(
            uri=credentials['NEO4J_URI'],
            username=credentials['NEO4J_USERNAME'],
            password=credentials['NEO4J_PASSWORD'],
            database=credentials.get('NEO4J_DATABASE', 'neo4j')
        )
        return manager
    except Exception as e:
        logger.error(f"❌ Failed to create GraphManager: {e}")
        return None
