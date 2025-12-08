"""
Auto-Summary Engine for PyRAG

Generates focused summaries from large specification documents.
Particularly useful for MEP (Mechanical, Electrical, Plumbing) projects.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from loguru import logger


class SummaryType(Enum):
    """Types of summaries that can be generated"""
    TOPIC_EXTRACTION = "topic_extraction"  # Extract specific topic (e.g., "electricity")
    REQUIREMENTS_LIST = "requirements_list"  # List requirements for a system (e.g., "UPS")
    CROSS_TRADE_COMPARISON = "cross_trade"  # Compare requirements across trades


@dataclass
class SummaryResult:
    """Result of an auto-summary operation"""
    summary_type: SummaryType
    document_name: str
    focus_topic: str
    summary: str
    extracted_sections: List[Dict[str, str]]  # [{"title": "...", "content": "..."}]
    metadata: Dict[str, any]
    timestamp: str


class AutoSummaryEngine:
    """
    Engine for generating automatic summaries from large documents.
    
    Examples:
    - "Extract only ELECTRICAL items from this 150-page spec"
    - "List all UPS requirements"
    - "Compare firestopping requirements across trades"
    """
    
    def __init__(self, query_engine):
        """
        Initialize the auto-summary engine.
        
        Args:
            query_engine: QueryEngine instance for document access
        """
        self.query_engine = query_engine
        self.logger = logger
    
    def generate_topic_summary(
        self,
        document_name: str,
        topic: str,
        max_sections: int = 50
    ) -> SummaryResult:
        """
        Extract all sections related to a specific topic.
        
        Args:
            document_name: Name of the document to analyze
            topic: Topic to extract (e.g., "electrical", "UPS", "firestopping")
            max_sections: Maximum number of sections to extract
            
        Returns:
            SummaryResult with extracted sections
        """
        self.logger.info(f"🔍 Extracting '{topic}' sections from '{document_name}'")
        
        # Get all chunks from document
        all_chunks = self._get_all_chunks(document_name)
        self.logger.info(f"📦 Found {len(all_chunks)} total chunks")
        
        # Filter chunks by topic
        relevant_chunks = self._filter_chunks_by_topic(all_chunks, topic)
        self.logger.info(f"🎯 Found {len(relevant_chunks)} relevant chunks")
        
        # Limit to max_sections
        if len(relevant_chunks) > max_sections:
            self.logger.warning(f"⚠️ Limiting to {max_sections} sections")
            relevant_chunks = relevant_chunks[:max_sections]
        
        # Extract sections with metadata
        extracted_sections = []
        for chunk in relevant_chunks:
            section = {
                "title": chunk.metadata.get("section_title", "Untitled Section"),
                "section_number": chunk.metadata.get("section_number", "N/A"),
                "page": chunk.metadata.get("page_label", "N/A"),
                "content": chunk.text
            }
            extracted_sections.append(section)
        
        # Generate summary using LLM
        summary = self._generate_llm_summary(extracted_sections, topic, document_name)
        
        return SummaryResult(
            summary_type=SummaryType.TOPIC_EXTRACTION,
            document_name=document_name,
            focus_topic=topic,
            summary=summary,
            extracted_sections=extracted_sections,
            metadata={
                "total_chunks": len(all_chunks),
                "relevant_chunks": len(relevant_chunks),
                "total_pages": self._count_unique_pages(relevant_chunks)
            },
            timestamp=datetime.now().isoformat()
        )
    
    def generate_requirements_list(
        self,
        document_name: str,
        system: str
    ) -> SummaryResult:
        """
        List all requirements for a specific system.
        
        Args:
            document_name: Name of the document to analyze
            system: System name (e.g., "UPS", "Generator", "Fire Alarm")
            
        Returns:
            SummaryResult with requirements list
        """
        self.logger.info(f"📋 Listing requirements for '{system}' from '{document_name}'")
        
        # Get all chunks
        all_chunks = self._get_all_chunks(document_name)
        
        # Filter by system keywords
        system_keywords = self._expand_system_keywords(system)
        relevant_chunks = self._filter_chunks_by_keywords(all_chunks, system_keywords)
        
        self.logger.info(f"🎯 Found {len(relevant_chunks)} relevant chunks for {system}")
        
        # Extract requirements
        extracted_sections = []
        for chunk in relevant_chunks:
            section = {
                "title": chunk.metadata.get("section_title", "Untitled"),
                "section_number": chunk.metadata.get("section_number", "N/A"),
                "page": chunk.metadata.get("page_label", "N/A"),
                "content": chunk.text
            }
            extracted_sections.append(section)
        
        # Generate structured requirements list
        summary = self._generate_requirements_summary(extracted_sections, system, document_name)
        
        return SummaryResult(
            summary_type=SummaryType.REQUIREMENTS_LIST,
            document_name=document_name,
            focus_topic=system,
            summary=summary,
            extracted_sections=extracted_sections,
            metadata={
                "total_chunks": len(all_chunks),
                "system": system,
                "keywords_used": system_keywords
            },
            timestamp=datetime.now().isoformat()
        )
    
    def generate_cross_trade_comparison(
        self,
        document_names: List[str],
        topic: str
    ) -> SummaryResult:
        """
        Compare requirements across multiple documents/trades.
        
        Args:
            document_names: List of documents to compare
            topic: Topic to compare (e.g., "firestopping", "testing", "commissioning")
            
        Returns:
            SummaryResult with cross-trade comparison
        """
        self.logger.info(f"🔄 Comparing '{topic}' across {len(document_names)} documents")
        
        all_sections = {}
        
        for doc_name in document_names:
            chunks = self._get_all_chunks(doc_name)
            relevant = self._filter_chunks_by_topic(chunks, topic)
            
            all_sections[doc_name] = []
            for chunk in relevant:
                all_sections[doc_name].append({
                    "title": chunk.metadata.get("section_title", "Untitled"),
                    "page": chunk.metadata.get("page_label", "N/A"),
                    "content": chunk.text
                })
            
            self.logger.info(f"  📄 {doc_name}: {len(relevant)} relevant sections")
        
        # Generate comparison summary
        summary = self._generate_comparison_summary(all_sections, topic)
        
        # Flatten for extracted_sections
        extracted_sections = []
        for doc_name, sections in all_sections.items():
            for section in sections:
                section["document"] = doc_name
                extracted_sections.append(section)
        
        return SummaryResult(
            summary_type=SummaryType.CROSS_TRADE_COMPARISON,
            document_name=", ".join(document_names),
            focus_topic=topic,
            summary=summary,
            extracted_sections=extracted_sections,
            metadata={
                "documents_compared": len(document_names),
                "total_sections": len(extracted_sections)
            },
            timestamp=datetime.now().isoformat()
        )
    
    def _get_all_chunks(self, document_name: str) -> List:
        """Get all chunks from a document"""
        try:
            collection = self.query_engine.chroma_collection
            result = collection.get(
                where={"file_name": document_name},
                include=['documents', 'metadatas']
            )
            
            chunks = []
            if result and result.get('documents'):
                from llama_index.core.schema import TextNode
                for i, text in enumerate(result['documents']):
                    metadata = result['metadatas'][i] if result.get('metadatas') else {}
                    node = TextNode(text=text, metadata=metadata)
                    chunks.append(node)
            
            return chunks
        except Exception as e:
            self.logger.error(f"Error getting chunks: {e}")
            return []
    
    def _filter_chunks_by_topic(self, chunks: List, topic: str) -> List:
        """Filter chunks by topic keywords"""
        topic_lower = topic.lower()
        
        # Expand topic with synonyms
        keywords = self._expand_topic_keywords(topic_lower)
        
        relevant = []
        for chunk in chunks:
            text_lower = chunk.text.lower()
            title_lower = chunk.metadata.get("section_title", "").lower()
            
            # Check if any keyword appears in text or title
            if any(kw in text_lower or kw in title_lower for kw in keywords):
                relevant.append(chunk)
        
        return relevant
    
    def _filter_chunks_by_keywords(self, chunks: List, keywords: List[str]) -> List:
        """Filter chunks by list of keywords"""
        relevant = []
        for chunk in chunks:
            text_lower = chunk.text.lower()
            if any(kw in text_lower for kw in keywords):
                relevant.append(chunk)
        return relevant
    
    def _expand_topic_keywords(self, topic: str) -> List[str]:
        """Expand topic with common synonyms and related terms"""
        expansions = {
            "electrical": ["electrical", "electric", "power", "voltage", "circuit", "wiring", "cable", "conductor"],
            "electricity": ["electrical", "electric", "power", "voltage", "circuit", "wiring"],
            "ups": ["ups", "uninterruptible power", "emergency power", "backup power"],
            "generator": ["generator", "genset", "standby power", "emergency generator"],
            "fire": ["fire", "flame", "combustion", "fire alarm", "fire detection"],
            "firestopping": ["firestopping", "fire stopping", "fire barrier", "fire seal", "penetration seal"],
            "hvac": ["hvac", "heating", "ventilation", "air conditioning", "mechanical"],
            "plumbing": ["plumbing", "water", "drainage", "sanitary", "waste water"],
            "lighting": ["lighting", "luminaire", "lamp", "illumination", "light"],
            "cable": ["cable", "cabling", "conductor", "wire", "wiring"],
        }
        
        # Return expanded keywords or just the topic
        return expansions.get(topic, [topic])
    
    def _expand_system_keywords(self, system: str) -> List[str]:
        """Expand system name with related terms"""
        return self._expand_topic_keywords(system.lower())
    
    def _count_unique_pages(self, chunks: List) -> int:
        """Count unique pages in chunks"""
        pages = set()
        for chunk in chunks:
            page = chunk.metadata.get("page_label")
            if page:
                pages.add(page)
        return len(pages)
    
    def _generate_llm_summary(self, sections: List[Dict], topic: str, document_name: str) -> str:
        """Generate summary using LLM"""
        if not sections:
            return f"No sections found related to '{topic}' in {document_name}."
        
        # Build prompt for LLM
        sections_text = "\n\n---\n\n".join([
            f"**{s['section_number']} - {s['title']}** (Page {s['page']})\n{s['content'][:500]}..."
            for s in sections[:10]  # Limit to first 10 for prompt
        ])
        
        prompt = f"""You are analyzing a technical specification document.

Document: {document_name}
Topic: {topic}
Found: {len(sections)} relevant sections

Please provide a concise summary of the key requirements and specifications related to '{topic}'. 
Focus on:
1. Main requirements
2. Technical specifications
3. Standards referenced
4. Important notes or warnings

Here are the first sections found:

{sections_text}

Provide a structured summary in 3-5 paragraphs."""
        
        try:
            # Use LlamaIndex Settings.llm
            from llama_index.core import Settings
            response = Settings.llm.complete(prompt)
            return str(response)
        except Exception as e:
            self.logger.error(f"Error generating LLM summary: {e}")
            return f"Found {len(sections)} sections related to '{topic}'. Summary generation failed."
    
    def _generate_requirements_summary(self, sections: List[Dict], system: str, document_name: str) -> str:
        """Generate requirements list summary"""
        if not sections:
            return f"No requirements found for '{system}' in {document_name}."
        
        sections_text = "\n\n---\n\n".join([
            f"**{s['section_number']} - {s['title']}** (Page {s['page']})\n{s['content'][:400]}..."
            for s in sections[:15]
        ])
        
        prompt = f"""You are analyzing requirements for a specific system in a technical specification.

Document: {document_name}
System: {system}
Found: {len(sections)} relevant sections

Please extract and list all requirements for the '{system}' system. Format as a numbered list with:
- Requirement description
- Reference (section number and page)
- Any technical values or standards mentioned

Relevant sections:

{sections_text}

Provide a clear, numbered list of requirements."""
        
        try:
            from llama_index.core import Settings
            response = Settings.llm.complete(prompt)
            return str(response)
        except Exception as e:
            self.logger.error(f"Error generating requirements summary: {e}")
            return f"Found {len(sections)} sections related to '{system}'. Summary generation failed."
    
    def _generate_comparison_summary(self, all_sections: Dict[str, List], topic: str) -> str:
        """Generate cross-trade comparison summary"""
        if not all_sections:
            return f"No sections found for comparison on topic '{topic}'."
        
        # Build comparison text
        comparison_text = ""
        for doc_name, sections in all_sections.items():
            if sections:
                comparison_text += f"\n\n### {doc_name}\n"
                for s in sections[:5]:  # First 5 per document
                    comparison_text += f"- **{s['title']}** (Page {s['page']}): {s['content'][:300]}...\n"
        
        prompt = f"""You are comparing requirements across multiple specification documents.

Topic: {topic}
Documents: {', '.join(all_sections.keys())}

Please analyze and compare how '{topic}' is addressed in each document. Focus on:
1. Common requirements across all documents
2. Unique requirements in each document
3. Differences in approach or specifications
4. Potential conflicts or inconsistencies

Documents and their sections:

{comparison_text}

Provide a structured comparison analysis."""
        
        try:
            from llama_index.core import Settings
            response = Settings.llm.complete(prompt)
            return str(response)
        except Exception as e:
            self.logger.error(f"Error generating comparison summary: {e}")
            return f"Comparison data collected for {len(all_sections)} documents. Summary generation failed."
