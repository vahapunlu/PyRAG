"""
Advanced Knowledge Graph Builder

Automatically constructs knowledge graphs from document content with:
- Entity extraction (standards, specifications, requirements)
- Relationship inference (references, dependencies, conflicts)
- Reasoning chain support
- Cross-document linkage

This enables GraphRAG-style retrieval combining vector search with graph traversal.
"""

import re
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from loguru import logger


@dataclass
class Entity:
    """Represents an entity in the knowledge graph"""
    id: str
    type: str  # 'standard', 'specification', 'requirement', 'section', 'term'
    name: str
    properties: Dict[str, Any] = field(default_factory=dict)
    source_doc: str = ""
    source_section: str = ""
    confidence: float = 1.0


@dataclass
class Relationship:
    """Represents a relationship between entities"""
    source_id: str
    target_id: str
    type: str  # 'REFERENCES', 'REQUIRES', 'SUPERSEDES', 'CONFLICTS', 'CONTAINS', 'DEFINES'
    properties: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0


class AdvancedEntityExtractor:
    """
    Extract entities and relationships from technical documents
    
    Entity Types:
    - Standard: IEC 60364, BS 7671, etc.
    - Specification: 2.5mm², 230V, 16A
    - Requirement: "shall", "must not"
    - Section: 6.5.1, Annex A
    - Term: technical definitions
    
    Relationship Types:
    - REFERENCES: Document A references Standard B
    - REQUIRES: Requirement A requires Specification B
    - SUPERSEDES: Standard A supersedes Standard B
    - CONFLICTS: Requirement A conflicts with Requirement B
    - CONTAINS: Document A contains Section B
    - DEFINES: Section A defines Term B
    """
    
    def __init__(self):
        # Standard patterns
        self.standard_patterns = {
            'IS': r'\bIS[\s-]?(\d+)(?:[-:](\d+))?(?:\s*Part\s*(\d+))?',
            'EN': r'\bEN[\s-]?(\d+)(?:[-:](\d+))?',
            'IEC': r'\bIEC[\s-]?(\d+)(?:[-:](\d+))?(?:[-:](\d+))?',
            'BS': r'\bBS[\s-]?(\d+)(?:[-:](\d+))?',
            'NFPA': r'\bNFPA[\s-]?(\d+)',
            'IEEE': r'\bIEEE[\s-]?(\d+)(?:\.(\d+))?',
            'ISO': r'\bISO[\s-]?(\d+)(?:[-:](\d+))?',
            'ASTM': r'\bASTM[\s-]?([A-Z]?\d+)',
        }
        
        # Specification patterns with units
        self.spec_patterns = {
            'current': (r'(\d+(?:\.\d+)?)\s*(A|mA|kA|amp)', 'A'),
            'voltage': (r'(\d+(?:\.\d+)?)\s*(V|mV|kV|volt)', 'V'),
            'power': (r'(\d+(?:\.\d+)?)\s*(W|kW|MW|watt)', 'W'),
            'area': (r'(\d+(?:\.\d+)?)\s*(mm²|mm2|sq\.?\s*mm)', 'mm²'),
            'length': (r'(\d+(?:\.\d+)?)\s*(mm|cm|m|km)', 'm'),
            'resistance': (r'(\d+(?:\.\d+)?)\s*(Ω|ohm)', 'Ω'),
            'temperature': (r'(\d+(?:\.\d+)?)\s*(°C|°F|K)', '°C'),
            'frequency': (r'(\d+(?:\.\d+)?)\s*(Hz|kHz|MHz)', 'Hz'),
        }
        
        # Requirement indicators and their strength
        self.requirement_patterns = {
            'mandatory': [
                (r'\bshall\b(?!\s+not)', 'mandatory'),
                (r'\bmust\b(?!\s+not)', 'mandatory'),
                (r'\brequired\b', 'mandatory'),
                (r'\bmandatory\b', 'mandatory'),
            ],
            'prohibited': [
                (r'\bshall\s+not\b', 'prohibited'),
                (r'\bmust\s+not\b', 'prohibited'),
                (r'\bprohibited\b', 'prohibited'),
                (r'\bforbidden\b', 'prohibited'),
            ],
            'recommended': [
                (r'\bshould\b(?!\s+not)', 'recommended'),
                (r'\brecommended\b', 'recommended'),
            ],
            'optional': [
                (r'\bmay\b', 'optional'),
                (r'\boptional\b', 'optional'),
                (r'\bpermitted\b', 'optional'),
            ],
        }
        
        # Cross-reference patterns for relationship extraction
        self.reference_patterns = [
            (r'as\s+(?:specified|defined|described)\s+in\s+([A-Z]+[\s\-]?\d+[\.\-\d]*)', 'REFERENCES'),
            (r'according\s+to\s+([A-Z]+[\s\-]?\d+[\.\-\d]*)', 'REFERENCES'),
            (r'in\s+accordance\s+with\s+([A-Z]+[\s\-]?\d+[\.\-\d]*)', 'REFERENCES'),
            (r'complying\s+with\s+([A-Z]+[\s\-]?\d+[\.\-\d]*)', 'REQUIRES'),
            (r'supersedes?\s+([A-Z]+[\s\-]?\d+[\.\-\d]*)', 'SUPERSEDES'),
            (r'replaces?\s+([A-Z]+[\s\-]?\d+[\.\-\d]*)', 'SUPERSEDES'),
            (r'see\s+(?:also\s+)?([A-Z]+[\s\-]?\d+[\.\-\d]*)', 'REFERENCES'),
            (r'refer\s+to\s+([A-Z]+[\s\-]?\d+[\.\-\d]*)', 'REFERENCES'),
        ]
        
        logger.info("✅ Advanced Entity Extractor initialized")
    
    def extract_entities(self, text: str, source_doc: str = "", 
                         source_section: str = "") -> List[Entity]:
        """
        Extract all entities from text
        
        Args:
            text: Source text
            source_doc: Source document name
            source_section: Source section number
            
        Returns:
            List of extracted entities
        """
        entities = []
        
        # Extract standards
        entities.extend(self._extract_standards(text, source_doc, source_section))
        
        # Extract specifications
        entities.extend(self._extract_specifications(text, source_doc, source_section))
        
        # Extract requirements
        entities.extend(self._extract_requirements(text, source_doc, source_section))
        
        return entities
    
    def _extract_standards(self, text: str, source_doc: str, 
                           source_section: str) -> List[Entity]:
        """Extract standard references"""
        entities = []
        seen = set()
        
        for std_type, pattern in self.standard_patterns.items():
            for match in re.finditer(pattern, text, re.IGNORECASE):
                full_ref = match.group(0).strip()
                normalized = re.sub(r'\s+', '', full_ref).upper()
                
                if normalized not in seen:
                    seen.add(normalized)
                    
                    entity_id = f"std_{normalized}"
                    entities.append(Entity(
                        id=entity_id,
                        type='standard',
                        name=full_ref,
                        properties={
                            'standard_type': std_type,
                            'normalized': normalized,
                            'position': match.start()
                        },
                        source_doc=source_doc,
                        source_section=source_section
                    ))
        
        return entities
    
    def _extract_specifications(self, text: str, source_doc: str,
                                 source_section: str) -> List[Entity]:
        """Extract technical specifications with units"""
        entities = []
        
        for spec_type, (pattern, base_unit) in self.spec_patterns.items():
            for match in re.finditer(pattern, text, re.IGNORECASE):
                value = match.group(1)
                unit = match.group(2)
                
                # Get context (surrounding text)
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end].replace('\n', ' ').strip()
                
                entity_id = f"spec_{spec_type}_{value}_{unit}"
                entities.append(Entity(
                    id=entity_id,
                    type='specification',
                    name=f"{value} {unit}",
                    properties={
                        'spec_type': spec_type,
                        'value': float(value),
                        'unit': unit,
                        'base_unit': base_unit,
                        'context': context,
                        'position': match.start()
                    },
                    source_doc=source_doc,
                    source_section=source_section
                ))
        
        return entities
    
    def _extract_requirements(self, text: str, source_doc: str,
                               source_section: str) -> List[Entity]:
        """Extract requirement statements"""
        entities = []
        
        for req_category, patterns in self.requirement_patterns.items():
            for pattern, strength in patterns:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    # Extract full sentence containing the requirement
                    sentence = self._extract_sentence(text, match.start())
                    
                    if len(sentence) < 10:
                        continue
                    
                    entity_id = f"req_{source_doc}_{source_section}_{match.start()}"
                    entities.append(Entity(
                        id=entity_id,
                        type='requirement',
                        name=sentence[:100],
                        properties={
                            'category': req_category,
                            'strength': strength,
                            'keyword': match.group(0),
                            'full_text': sentence,
                            'position': match.start()
                        },
                        source_doc=source_doc,
                        source_section=source_section
                    ))
        
        return entities
    
    def _extract_sentence(self, text: str, position: int) -> str:
        """Extract the sentence containing the given position"""
        # Find sentence boundaries
        start = position
        while start > 0 and text[start-1] not in '.!?\n':
            start -= 1
        
        end = position
        while end < len(text) and text[end] not in '.!?\n':
            end += 1
        
        return text[start:end+1].strip()
    
    def extract_relationships(self, text: str, entities: List[Entity],
                               source_doc: str = "") -> List[Relationship]:
        """
        Extract relationships between entities
        
        Args:
            text: Source text
            entities: Extracted entities
            source_doc: Source document name
            
        Returns:
            List of relationships
        """
        relationships = []
        
        # Build entity lookup
        entity_lookup = {e.name.upper().replace(' ', ''): e for e in entities}
        standard_entities = [e for e in entities if e.type == 'standard']
        
        # Extract explicit cross-references
        for pattern, rel_type in self.reference_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                target_ref = match.group(1).strip()
                target_normalized = target_ref.upper().replace(' ', '')
                
                # Find target entity
                target_entity = None
                for std in standard_entities:
                    if std.properties.get('normalized', '') == target_normalized:
                        target_entity = std
                        break
                
                if target_entity:
                    relationships.append(Relationship(
                        source_id=f"doc_{source_doc}",
                        target_id=target_entity.id,
                        type=rel_type,
                        properties={
                            'context': match.group(0),
                            'position': match.start()
                        }
                    ))
        
        # Extract requirement-specification relationships
        req_entities = [e for e in entities if e.type == 'requirement']
        spec_entities = [e for e in entities if e.type == 'specification']
        
        for req in req_entities:
            req_text = req.properties.get('full_text', req.name)
            
            for spec in spec_entities:
                # Check if specification appears in requirement
                spec_value = str(spec.properties.get('value', ''))
                spec_unit = spec.properties.get('unit', '')
                
                if spec_value in req_text or spec.name in req_text:
                    relationships.append(Relationship(
                        source_id=req.id,
                        target_id=spec.id,
                        type='SPECIFIES',
                        properties={
                            'requirement_strength': req.properties.get('strength', ''),
                            'spec_type': spec.properties.get('spec_type', '')
                        }
                    ))
        
        return relationships


class KnowledgeGraphConstructor:
    """
    High-level interface for building knowledge graphs
    
    Orchestrates:
    - Entity extraction
    - Relationship inference
    - Graph construction in Neo4j
    - Conflict detection
    """
    
    def __init__(self, graph_manager=None):
        """
        Initialize constructor
        
        Args:
            graph_manager: Neo4j graph manager instance
        """
        self.extractor = AdvancedEntityExtractor()
        self.graph_manager = graph_manager
        
        # Statistics
        self.stats = {
            'entities': 0,
            'relationships': 0,
            'conflicts': 0
        }
        
        logger.info("✅ Knowledge Graph Constructor initialized")
    
    def process_document(self, doc_id: str, text: str, 
                          metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a document and extract knowledge graph elements
        
        Args:
            doc_id: Document identifier
            text: Document text
            metadata: Document metadata
            
        Returns:
            Extraction results with entities and relationships
        """
        source_doc = metadata.get('document_name', metadata.get('file_name', doc_id))
        source_section = metadata.get('section_number', '')
        
        # Extract entities
        entities = self.extractor.extract_entities(text, source_doc, source_section)
        
        # Extract relationships
        relationships = self.extractor.extract_relationships(text, entities, source_doc)
        
        # Persist to graph if manager available
        if self.graph_manager:
            self._persist_to_graph(entities, relationships, source_doc, metadata)
        
        # Update stats
        self.stats['entities'] += len(entities)
        self.stats['relationships'] += len(relationships)
        
        return {
            'entities': [self._entity_to_dict(e) for e in entities],
            'relationships': [self._relationship_to_dict(r) for r in relationships],
            'summary': {
                'standards': len([e for e in entities if e.type == 'standard']),
                'specifications': len([e for e in entities if e.type == 'specification']),
                'requirements': len([e for e in entities if e.type == 'requirement']),
                'relationships': len(relationships)
            }
        }
    
    def _entity_to_dict(self, entity: Entity) -> Dict[str, Any]:
        """Convert entity to dictionary"""
        return {
            'id': entity.id,
            'type': entity.type,
            'name': entity.name,
            'properties': entity.properties,
            'source_doc': entity.source_doc,
            'source_section': entity.source_section,
            'confidence': entity.confidence
        }
    
    def _relationship_to_dict(self, rel: Relationship) -> Dict[str, Any]:
        """Convert relationship to dictionary"""
        return {
            'source_id': rel.source_id,
            'target_id': rel.target_id,
            'type': rel.type,
            'properties': rel.properties,
            'confidence': rel.confidence
        }
    
    def _persist_to_graph(self, entities: List[Entity], 
                          relationships: List[Relationship],
                          source_doc: str, metadata: Dict):
        """Persist extracted elements to Neo4j"""
        try:
            # Create document node
            self.graph_manager.create_document_node(source_doc, metadata)
            
            # Create entity nodes
            for entity in entities:
                if entity.type == 'standard':
                    self.graph_manager.create_standard_node(
                        entity.name, entity.properties
                    )
                elif entity.type == 'specification':
                    self._create_spec_node(entity)
                elif entity.type == 'requirement':
                    self._create_requirement_node(entity)
            
            # Create relationships
            for rel in relationships:
                self.graph_manager.create_refers_to_relationship(
                    source_name=rel.source_id.replace('doc_', ''),
                    target_name=rel.target_id.replace('std_', ''),
                    source_type="DOCUMENT",
                    properties=rel.properties
                )
                
        except Exception as e:
            logger.warning(f"Failed to persist to graph: {e}")
    
    def _create_spec_node(self, entity: Entity):
        """Create specification node in graph"""
        if not self.graph_manager:
            return
        
        # Use raw Cypher for custom node types
        try:
            query = """
            MERGE (s:Specification {id: $id})
            SET s.name = $name,
                s.type = $spec_type,
                s.value = $value,
                s.unit = $unit,
                s.source_doc = $source_doc,
                s.source_section = $source_section
            """
            self.graph_manager._run_query(query, {
                'id': entity.id,
                'name': entity.name,
                'spec_type': entity.properties.get('spec_type', ''),
                'value': entity.properties.get('value', 0),
                'unit': entity.properties.get('unit', ''),
                'source_doc': entity.source_doc,
                'source_section': entity.source_section
            })
        except Exception as e:
            logger.debug(f"Spec node creation skipped: {e}")
    
    def _create_requirement_node(self, entity: Entity):
        """Create requirement node in graph"""
        if not self.graph_manager:
            return
        
        try:
            query = """
            MERGE (r:Requirement {id: $id})
            SET r.text = $text,
                r.category = $category,
                r.strength = $strength,
                r.source_doc = $source_doc,
                r.source_section = $source_section
            """
            self.graph_manager._run_query(query, {
                'id': entity.id,
                'text': entity.name,
                'category': entity.properties.get('category', ''),
                'strength': entity.properties.get('strength', ''),
                'source_doc': entity.source_doc,
                'source_section': entity.source_section
            })
        except Exception as e:
            logger.debug(f"Requirement node creation skipped: {e}")
    
    def detect_conflicts(self, doc1_requirements: List[Entity],
                          doc2_requirements: List[Entity]) -> List[Dict]:
        """
        Detect potential conflicts between requirements
        
        Args:
            doc1_requirements: Requirements from document 1
            doc2_requirements: Requirements from document 2
            
        Returns:
            List of potential conflicts
        """
        conflicts = []
        
        for req1 in doc1_requirements:
            for req2 in doc2_requirements:
                conflict = self._check_conflict(req1, req2)
                if conflict:
                    conflicts.append(conflict)
                    self.stats['conflicts'] += 1
        
        return conflicts
    
    def _check_conflict(self, req1: Entity, req2: Entity) -> Optional[Dict]:
        """Check if two requirements potentially conflict"""
        # Get requirement strengths
        strength1 = req1.properties.get('strength', '')
        strength2 = req2.properties.get('strength', '')
        
        # Check for mandatory/prohibited conflicts
        if (strength1 == 'mandatory' and strength2 == 'prohibited') or \
           (strength1 == 'prohibited' and strength2 == 'mandatory'):
            
            # Check if they reference similar specifications
            text1 = req1.properties.get('full_text', req1.name).lower()
            text2 = req2.properties.get('full_text', req2.name).lower()
            
            # Simple overlap check (can be enhanced with NLP)
            words1 = set(text1.split())
            words2 = set(text2.split())
            
            overlap = len(words1 & words2) / max(len(words1), len(words2))
            
            if overlap > 0.3:  # 30% word overlap threshold
                return {
                    'type': 'strength_conflict',
                    'requirement1': {
                        'doc': req1.source_doc,
                        'section': req1.source_section,
                        'text': req1.name,
                        'strength': strength1
                    },
                    'requirement2': {
                        'doc': req2.source_doc,
                        'section': req2.source_section,
                        'text': req2.name,
                        'strength': strength2
                    },
                    'overlap_score': overlap,
                    'severity': 'high'
                }
        
        return None
    
    def get_statistics(self) -> Dict[str, int]:
        """Get extraction statistics"""
        return dict(self.stats)


# Singleton instance
_kg_constructor: Optional[KnowledgeGraphConstructor] = None


def get_kg_constructor(graph_manager=None) -> KnowledgeGraphConstructor:
    """Get or create knowledge graph constructor singleton"""
    global _kg_constructor
    if _kg_constructor is None:
        _kg_constructor = KnowledgeGraphConstructor(graph_manager)
    elif graph_manager:
        _kg_constructor.graph_manager = graph_manager
    return _kg_constructor


if __name__ == "__main__":
    # Test the module
    logger.info("Testing Knowledge Graph Constructor...")
    
    test_text = """
    ## 6.5.1 Cable Requirements
    
    Cables shall comply with IEC 60364-5-52 and BS 7671 requirements.
    
    The minimum conductor size for power circuits shall be 2.5 mm².
    Current ratings must not exceed values specified in Table 4D1A.
    
    According to EN 50575, cables in escape routes shall have fire resistance.
    
    For voltages up to 1000V, the maximum voltage drop shall not exceed 4%.
    The installation temperature range is -5°C to 70°C.
    
    This standard supersedes IS 3218-1982.
    """
    
    constructor = get_kg_constructor()
    result = constructor.process_document(
        doc_id="test_doc",
        text=test_text,
        metadata={'document_name': 'Test Standard', 'section_number': '6.5.1'}
    )
    
    print("\n📋 Extraction Results:")
    print(f"   Standards: {result['summary']['standards']}")
    print(f"   Specifications: {result['summary']['specifications']}")
    print(f"   Requirements: {result['summary']['requirements']}")
    print(f"   Relationships: {result['summary']['relationships']}")
    
    print("\n🔗 Extracted Entities:")
    for entity in result['entities'][:5]:
        print(f"   [{entity['type']}] {entity['name']}")
    
    print("\n🔀 Extracted Relationships:")
    for rel in result['relationships'][:5]:
        print(f"   {rel['source_id']} --{rel['type']}--> {rel['target_id']}")
