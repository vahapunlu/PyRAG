"""
Contextual Chunking Module (Anthropic Approach)

Implements the "Contextual Retrieval" technique that prepends each chunk
with a context summary explaining where it fits in the overall document.

This dramatically improves retrieval accuracy by providing embeddings with
richer contextual information.

Reference: https://www.anthropic.com/news/contextual-retrieval
"""

import re
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache

from llama_index.core import Document
from llama_index.core.schema import TextNode
from loguru import logger

# Import smart table parser (lazy load to avoid circular imports)
_table_chunker = None

def _get_table_chunker():
    """Lazy load table chunker to avoid circular imports"""
    global _table_chunker
    if _table_chunker is None:
        try:
            from src.smart_table_parser import get_table_chunker
            _table_chunker = get_table_chunker()
        except ImportError:
            logger.warning("Smart table parser not available")
            _table_chunker = False  # Mark as unavailable
    return _table_chunker if _table_chunker else None


@dataclass
class ChunkContext:
    """Context information for a chunk"""
    document_title: str
    document_summary: str
    section_path: str  # e.g., "Chapter 6 > 6.5 Cable Requirements > 6.5.1 Types"
    parent_section: str
    section_number: str
    section_title: str
    chunk_position: str  # e.g., "first", "middle", "last"
    preceding_context: str  # Brief summary of what came before
    

class HierarchicalSectionParser:
    """
    Parse document structure into hierarchical sections
    
    Extracts:
    - Main headings (H1-H6 in markdown)
    - Section numbers (1.2.3)
    - Table of contents structure
    """
    
    def __init__(self):
        # Markdown heading patterns
        self.heading_patterns = [
            (1, r'^#\s+(.+)$'),                    # # Heading 1
            (2, r'^##\s+(.+)$'),                   # ## Heading 2
            (3, r'^###\s+(.+)$'),                  # ### Heading 3
            (4, r'^####\s+(.+)$'),                 # #### Heading 4
            (5, r'^#####\s+(.+)$'),                # ##### Heading 5
            (6, r'^######\s+(.+)$'),               # ###### Heading 6
        ]
        
        # Section number pattern (e.g., "6.5.1 Cable Requirements")
        self.section_number_pattern = r'^(\d+(?:\.\d+)*)\s+(.+)$'
        
        # Table markers
        self.table_start_pattern = r'^\|.*\|$'
        self.table_header_sep = r'^\|[-:\s|]+\|$'
        
    def parse_sections(self, text: str) -> List[Dict[str, Any]]:
        """
        Parse text into hierarchical sections
        
        Returns list of sections with:
        - level: hierarchy level (1-6)
        - number: section number if present
        - title: section title
        - start_pos: character position
        - content: section content
        """
        sections = []
        lines = text.split('\n')
        current_section = None
        content_lines = []
        
        for i, line in enumerate(lines):
            heading = self._parse_heading(line)
            
            if heading:
                # Save previous section
                if current_section:
                    current_section['content'] = '\n'.join(content_lines).strip()
                    sections.append(current_section)
                    content_lines = []
                
                current_section = heading
            elif current_section:
                content_lines.append(line)
        
        # Save last section
        if current_section:
            current_section['content'] = '\n'.join(content_lines).strip()
            sections.append(current_section)
        
        return sections
    
    def _parse_heading(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse a line as a heading"""
        line = line.strip()
        if not line:
            return None
        
        # Try markdown headings
        for level, pattern in self.heading_patterns:
            match = re.match(pattern, line)
            if match:
                title = match.group(1).strip()
                # Check for section number in title
                sec_match = re.match(self.section_number_pattern, title)
                if sec_match:
                    return {
                        'level': level,
                        'number': sec_match.group(1),
                        'title': sec_match.group(2).strip(),
                        'full_title': title
                    }
                return {
                    'level': level,
                    'number': '',
                    'title': title,
                    'full_title': title
                }
        
        # Try plain section number at start of line
        if re.match(r'^\d+(\.\d+)+\s+', line):
            sec_match = re.match(self.section_number_pattern, line)
            if sec_match:
                level = len(sec_match.group(1).split('.'))  # Infer level from depth
                return {
                    'level': min(level, 6),
                    'number': sec_match.group(1),
                    'title': sec_match.group(2).strip(),
                    'full_title': line
                }
        
        return None
    
    def build_section_path(self, sections: List[Dict], current_index: int) -> str:
        """
        Build hierarchical path to current section
        
        Example: "6. Electrical Installation > 6.5 Cabling > 6.5.1 Types"
        """
        if current_index < 0 or current_index >= len(sections):
            return ""
        
        current = sections[current_index]
        current_level = current.get('level', 1)
        
        path_parts = []
        
        # Look backwards for parent sections
        for i in range(current_index, -1, -1):
            section = sections[i]
            level = section.get('level', 1)
            
            if level < current_level or i == current_index:
                title = section.get('full_title', section.get('title', ''))
                if title:
                    path_parts.insert(0, title)
                    current_level = level
                    
                    if level == 1:
                        break
        
        return ' > '.join(path_parts)


class ContextualChunker:
    """
    Creates contextually-enriched chunks for better retrieval
    
    Each chunk is prefixed with:
    1. Document title and brief summary
    2. Section hierarchy path
    3. Preceding context summary
    
    This provides embeddings with much richer semantic information.
    """
    
    def __init__(self, 
                 llm=None,
                 use_llm_summarization: bool = False,
                 max_context_length: int = 200):
        """
        Initialize contextual chunker
        
        Args:
            llm: LlamaIndex LLM for generating summaries (optional)
            use_llm_summarization: Use LLM for context generation (expensive but better)
            max_context_length: Maximum characters for context prefix
        """
        self.llm = llm
        self.use_llm_summarization = use_llm_summarization and llm is not None
        self.max_context_length = max_context_length
        self.section_parser = HierarchicalSectionParser()
        
        # Cache for document summaries
        self._doc_summary_cache = {}
        
        logger.info(f"✅ Contextual Chunker initialized (LLM: {use_llm_summarization})")
    
    def _get_document_summary(self, doc: Document) -> str:
        """
        Get or generate document summary
        
        Uses metadata if available, otherwise generates from content
        """
        doc_name = doc.metadata.get('document_name', 'Unknown')
        
        # Check cache
        if doc_name in self._doc_summary_cache:
            return self._doc_summary_cache[doc_name]
        
        # Use description from metadata if available
        description = doc.metadata.get('description', '')
        if description:
            summary = f"Document '{doc_name}': {description}"
            self._doc_summary_cache[doc_name] = summary
            return summary
        
        # Generate summary from standard number and category
        standard_no = doc.metadata.get('standard_no', '')
        categories = doc.metadata.get('categories', '')
        
        if standard_no:
            summary = f"Technical standard {standard_no} ({doc_name})"
            if categories:
                summary += f" covering {categories}"
        else:
            summary = f"Document '{doc_name}'"
            if categories:
                summary += f" categorized as {categories}"
        
        self._doc_summary_cache[doc_name] = summary
        return summary
    
    def _extract_table_context(self, text: str) -> Optional[str]:
        """
        Extract context about tables in the chunk
        
        If chunk contains a table, identify what the table shows.
        """
        # Check for markdown table
        if '|' in text and re.search(r'\|[-:\s]+\|', text):
            lines = text.split('\n')
            
            # Find table and preceding line (usually caption)
            for i, line in enumerate(lines):
                if line.strip().startswith('|') and '|' in line[1:]:
                    # Check for caption before table
                    if i > 0:
                        prev_line = lines[i-1].strip()
                        if prev_line and not prev_line.startswith('|'):
                            # Check if it looks like a table caption
                            if re.match(r'^(Table|Tablo)\s+\d+', prev_line, re.IGNORECASE):
                                return f"Contains {prev_line}"
                    
                    # Try to identify table from headers
                    headers = [h.strip() for h in line.split('|') if h.strip()]
                    if headers:
                        return f"Contains table with columns: {', '.join(headers[:5])}"
            
            return "Contains tabular data"
        
        return None
    
    def _generate_context_prefix(self, 
                                  chunk_text: str,
                                  doc: Document,
                                  section_path: str,
                                  section_title: str,
                                  chunk_position: int,
                                  total_chunks: int) -> str:
        """
        Generate context prefix for a chunk
        
        Format:
        [Document: {name} - {summary}]
        [Section: {path}]
        [Context: {what this chunk contains}]
        
        {original chunk text}
        """
        parts = []
        
        # 1. Document context
        doc_summary = self._get_document_summary(doc)
        parts.append(f"[Document: {doc_summary}]")
        
        # 2. Section path (hierarchical context)
        if section_path:
            parts.append(f"[Section: {section_path}]")
        elif section_title:
            parts.append(f"[Section: {section_title}]")
        
        # 3. Page info
        page_num = doc.metadata.get('page_number', doc.metadata.get('page_label', ''))
        if page_num:
            parts.append(f"[Page: {page_num}]")
        
        # 4. Table context (if applicable)
        table_context = self._extract_table_context(chunk_text)
        if table_context:
            parts.append(f"[{table_context}]")
        
        # 5. Position context
        if total_chunks > 1:
            if chunk_position == 0:
                pos_text = "beginning"
            elif chunk_position == total_chunks - 1:
                pos_text = "end"
            else:
                pos_text = f"part {chunk_position + 1} of {total_chunks}"
            parts.append(f"[Position: {pos_text}]")
        
        # Combine and truncate if needed
        context = '\n'.join(parts)
        if len(context) > self.max_context_length:
            # Keep most important parts
            context = '\n'.join(parts[:3])
        
        return context
    
    def _generate_llm_context(self, chunk_text: str, doc: Document, section_path: str) -> str:
        """
        Use LLM to generate a rich contextual summary (expensive but accurate)
        
        Only used when use_llm_summarization=True
        """
        if not self.llm:
            return ""
        
        prompt = f"""Please provide a brief, one-sentence context for this document chunk.
The context should explain what this chunk is about and how it fits in the document.

Document: {doc.metadata.get('document_name', 'Unknown')}
Section Path: {section_path or 'N/A'}

Chunk:
{chunk_text[:500]}...

Context (one sentence):"""
        
        try:
            response = self.llm.complete(prompt)
            return f"[Context: {str(response).strip()}]"
        except Exception as e:
            logger.warning(f"LLM context generation failed: {e}")
            return ""
    
    def enrich_chunks(self, 
                      nodes: List[TextNode], 
                      documents: List[Document]) -> List[TextNode]:
        """
        Add contextual prefixes to all chunks
        
        Args:
            nodes: List of text nodes (chunks)
            documents: Original documents for context
            
        Returns:
            Enriched nodes with contextual prefixes
        """
        logger.info(f"🔄 Enriching {len(nodes)} chunks with contextual information...")
        
        # Build document lookup
        doc_lookup = {}
        for doc in documents:
            doc_id = doc.metadata.get('file_name', doc.doc_id)
            if doc_id not in doc_lookup:
                doc_lookup[doc_id] = []
            doc_lookup[doc_id].append(doc)
        
        # Parse sections from all documents
        doc_sections = {}
        for doc_name, docs in doc_lookup.items():
            full_text = '\n\n'.join([d.text for d in docs])
            sections = self.section_parser.parse_sections(full_text)
            doc_sections[doc_name] = sections
        
        enriched_nodes = []
        
        for node in nodes:
            try:
                # Get document info
                file_name = node.metadata.get('file_name', '')
                section_number = node.metadata.get('section_number', '')
                section_title = node.metadata.get('section_title', '')
                
                # Find parent document
                parent_doc = None
                if file_name in doc_lookup:
                    parent_doc = doc_lookup[file_name][0]
                else:
                    parent_doc = documents[0] if documents else None
                
                # Build section path
                section_path = ""
                if file_name in doc_sections and section_number:
                    sections = doc_sections[file_name]
                    # Find matching section
                    for i, sec in enumerate(sections):
                        if sec.get('number', '') == section_number:
                            section_path = self.section_parser.build_section_path(sections, i)
                            break
                
                # Generate context prefix
                if parent_doc:
                    context_prefix = self._generate_context_prefix(
                        chunk_text=node.text,
                        doc=parent_doc,
                        section_path=section_path,
                        section_title=section_title,
                        chunk_position=0,  # Would need tracking for multi-chunk docs
                        total_chunks=1
                    )
                else:
                    context_prefix = f"[Document: {file_name}]"
                
                # Smart Table Processing - enhance table content
                table_metadata = {}
                table_enrichment = ""
                table_chunker = _get_table_chunker()
                
                if table_chunker and table_chunker.has_table(node.text):
                    try:
                        table_result = table_chunker.process_chunk(node.text)
                        if table_result['has_table']:
                            # Add table summary to context
                            if table_result['tables']:
                                table_summaries = [t.summary for t in table_result['tables']]
                                table_enrichment = "\n[Table Data: " + "; ".join(table_summaries) + "]"
                            
                            # Store table metadata
                            table_metadata = table_result['table_metadata']
                            table_metadata['table_json'] = table_result['table_json']
                    except Exception as e:
                        logger.debug(f"Table processing skipped: {e}")
                
                # Create enriched node
                enriched_text = f"{context_prefix}{table_enrichment}\n\n{node.text}"
                
                # Update node
                enriched_node = TextNode(
                    text=enriched_text,
                    metadata={
                        **node.metadata,
                        'original_text': node.text,  # Keep original for display
                        'context_prefix': context_prefix,
                        'section_path': section_path,
                        'has_contextual_enrichment': True,
                        'has_table': bool(table_metadata),
                        **table_metadata
                    },
                    id_=node.id_
                )
                
                enriched_nodes.append(enriched_node)
                
            except Exception as e:
                logger.warning(f"Failed to enrich chunk: {e}")
                enriched_nodes.append(node)  # Keep original
        
        logger.success(f"✅ Enriched {len(enriched_nodes)} chunks with contextual prefixes")
        return enriched_nodes
    
    def process_documents(self, documents: List[Document]) -> List[Document]:
        """
        Process documents to add hierarchical metadata
        
        Extracts section structure and adds:
        - section_path: Full hierarchical path
        - parent_section: Immediate parent section
        - section_level: Depth in hierarchy
        """
        logger.info(f"📊 Processing {len(documents)} documents for hierarchical structure...")
        
        processed = []
        
        for doc in documents:
            try:
                # Parse document structure
                sections = self.section_parser.parse_sections(doc.text)
                
                if sections:
                    # Find the most specific section for this document
                    best_section = None
                    best_level = 0
                    
                    for i, section in enumerate(sections):
                        if section.get('level', 0) > best_level:
                            best_level = section['level']
                            best_section = section
                            best_section['index'] = i
                    
                    if best_section:
                        section_path = self.section_parser.build_section_path(
                            sections, best_section.get('index', 0)
                        )
                        
                        # Update metadata
                        doc.metadata['section_path'] = section_path
                        doc.metadata['section_level'] = best_level
                        doc.metadata['section_count'] = len(sections)
                
                processed.append(doc)
                
            except Exception as e:
                logger.warning(f"Error processing document: {e}")
                processed.append(doc)
        
        logger.success(f"✅ Processed {len(processed)} documents")
        return processed


class EntityExtractor:
    """
    Extract named entities from technical documents
    
    Extracts:
    - Standards (IS, EN, IEC, BS, etc.)
    - Specifications (values with units)
    - Requirements (must, shall, required)
    - Technical terms
    """
    
    def __init__(self):
        # Standard reference patterns
        self.standard_patterns = {
            'IS': r'\bIS[\s-]?\d+(?:[-:]\d+)*(?:\s*Part\s*\d+)?',
            'EN': r'\bEN[\s-]?\d+(?:[-:]\d+)*',
            'IEC': r'\bIEC[\s-]?\d+(?:[-:]\d+)*',
            'BS': r'\bBS[\s-]?\d+(?:[-:]\d+)*',
            'NFPA': r'\bNFPA[\s-]?\d+',
            'IEEE': r'\bIEEE[\s-]?\d+(?:\.\d+)?',
            'ISO': r'\bISO[\s-]?\d+(?:[-:]\d+)*',
            'ASTM': r'\bASTM[\s-]?[A-Z]?\d+',
            'NEC': r'\bNEC\s*(?:Article\s*)?\d+(?:\.\d+)?',
        }
        
        # Specification patterns (value + unit)
        self.spec_patterns = [
            r'(\d+(?:\.\d+)?)\s*(mm²|mm2|sq\.?\s*mm)',  # Area
            r'(\d+(?:\.\d+)?)\s*(kV|V|mV)',             # Voltage
            r'(\d+(?:\.\d+)?)\s*(kA|A|mA)',             # Current
            r'(\d+(?:\.\d+)?)\s*(kW|W|MW)',             # Power
            r'(\d+(?:\.\d+)?)\s*(Ω|ohm|ohms)',          # Resistance
            r'(\d+(?:\.\d+)?)\s*(°C|°F|K)',             # Temperature
            r'(\d+(?:\.\d+)?)\s*(m|mm|cm|km)',          # Length
            r'(\d+(?:\.\d+)?)\s*(Hz|kHz|MHz)',          # Frequency
            r'(\d+(?:\.\d+)?)\s*(%)',                   # Percentage
        ]
        
        # Requirement indicators
        self.requirement_patterns = [
            r'\b(shall|must|required|mandatory|obligatory)\b',
            r'\b(should|recommended|preferred)\b',
            r'\b(may|optional|permitted)\b',
            r'\b(shall not|must not|prohibited|forbidden)\b',
        ]
        
        logger.info("✅ Entity Extractor initialized")
    
    def extract_all(self, text: str) -> Dict[str, Any]:
        """
        Extract all entities from text
        
        Returns:
            {
                'standards': [{'type': 'IEC', 'reference': 'IEC 60364-5-52'}],
                'specifications': [{'value': '2.5', 'unit': 'mm²', 'context': '...'}],
                'requirements': [{'type': 'mandatory', 'text': '...'}],
                'entities_count': int
            }
        """
        results = {
            'standards': [],
            'specifications': [],
            'requirements': [],
            'entities_count': 0
        }
        
        # Extract standards
        for std_type, pattern in self.standard_patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                ref = match.group(0).strip()
                results['standards'].append({
                    'type': std_type,
                    'reference': ref,
                    'position': match.start()
                })
        
        # Deduplicate standards
        seen_standards = set()
        unique_standards = []
        for std in results['standards']:
            key = std['reference'].upper()
            if key not in seen_standards:
                seen_standards.add(key)
                unique_standards.append(std)
        results['standards'] = unique_standards
        
        # Extract specifications
        for pattern in self.spec_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                value = match.group(1)
                unit = match.group(2)
                # Get surrounding context
                start = max(0, match.start() - 30)
                end = min(len(text), match.end() + 30)
                context = text[start:end].replace('\n', ' ').strip()
                
                results['specifications'].append({
                    'value': value,
                    'unit': unit,
                    'full': f"{value} {unit}",
                    'context': context,
                    'position': match.start()
                })
        
        # Extract requirements
        for pattern in self.requirement_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                keyword = match.group(0).lower()
                
                # Determine requirement type
                if keyword in ['shall', 'must', 'required', 'mandatory', 'obligatory']:
                    req_type = 'mandatory'
                elif keyword in ['should', 'recommended', 'preferred']:
                    req_type = 'recommended'
                elif keyword in ['may', 'optional', 'permitted']:
                    req_type = 'optional'
                else:
                    req_type = 'prohibited'
                
                # Get sentence context
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 100)
                context = text[start:end].replace('\n', ' ').strip()
                
                results['requirements'].append({
                    'type': req_type,
                    'keyword': keyword,
                    'context': context,
                    'position': match.start()
                })
        
        results['entities_count'] = (
            len(results['standards']) + 
            len(results['specifications']) + 
            len(results['requirements'])
        )
        
        return results
    
    def extract_for_metadata(self, text: str) -> Dict[str, Any]:
        """
        Extract entities suitable for metadata storage
        
        Returns flattened dict for Qdrant payload
        """
        entities = self.extract_all(text)
        
        return {
            'referenced_standards': [s['reference'] for s in entities['standards']],
            'standard_types': list(set(s['type'] for s in entities['standards'])),
            'has_specifications': len(entities['specifications']) > 0,
            'spec_values': [s['full'] for s in entities['specifications'][:10]],  # Limit
            'requirement_types': list(set(r['type'] for r in entities['requirements'])),
            'has_mandatory_requirements': any(r['type'] == 'mandatory' for r in entities['requirements']),
            'entities_count': entities['entities_count']
        }


# Singleton pattern for global access
_contextual_chunker: Optional[ContextualChunker] = None
_entity_extractor: Optional[EntityExtractor] = None


def get_contextual_chunker(llm=None, use_llm: bool = False) -> ContextualChunker:
    """Get or create contextual chunker singleton"""
    global _contextual_chunker
    if _contextual_chunker is None:
        _contextual_chunker = ContextualChunker(llm=llm, use_llm_summarization=use_llm)
    return _contextual_chunker


def get_entity_extractor() -> EntityExtractor:
    """Get or create entity extractor singleton"""
    global _entity_extractor
    if _entity_extractor is None:
        _entity_extractor = EntityExtractor()
    return _entity_extractor


if __name__ == "__main__":
    # Test the module
    from loguru import logger
    logger.info("Testing Contextual Chunker...")
    
    # Test entity extraction
    test_text = """
    ## 6.5.1 Cable Requirements
    
    According to IEC 60364-5-52, cables shall be rated for the installation environment.
    The minimum conductor size is 2.5 mm² for power circuits and 1.5 mm² for lighting.
    
    | Conductor Size | Current Rating | Application |
    |----------------|----------------|-------------|
    | 1.5 mm²        | 15 A           | Lighting    |
    | 2.5 mm²        | 20 A           | Sockets     |
    | 4 mm²          | 27 A           | Appliances  |
    
    As specified in BS 7671, the voltage drop shall not exceed 4% of nominal voltage.
    Reference: EN 50575 for fire performance requirements.
    """
    
    extractor = get_entity_extractor()
    entities = extractor.extract_all(test_text)
    
    print("\n📋 Extracted Entities:")
    print(f"   Standards: {[s['reference'] for s in entities['standards']]}")
    print(f"   Specs: {[s['full'] for s in entities['specifications']]}")
    print(f"   Requirements: {len(entities['requirements'])} found")
    print(f"   Total: {entities['entities_count']} entities")
    
    # Test section parsing
    parser = HierarchicalSectionParser()
    sections = parser.parse_sections(test_text)
    print(f"\n📊 Sections: {len(sections)} found")
    for sec in sections:
        print(f"   L{sec['level']}: {sec.get('number', '')} {sec['title']}")
