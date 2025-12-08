"""
Cross-Reference Engine for Multi-Document Analysis

This module provides functionality to compare multiple documents,
detect conflicts, analyze gaps, and generate comprehensive reports.
"""

import logging
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class AnalysisType(Enum):
    """Types of cross-reference analysis"""
    CONFLICTS = "conflicts"
    GAPS = "gaps"
    ALIGNMENT = "alignment"
    REQUIREMENTS = "requirements"


class SeverityLevel(Enum):
    """Severity levels for detected issues"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class DocumentChunk:
    """Represents a chunk of text from a document"""
    document_name: str
    page: str
    text: str
    metadata: Dict[str, Any]
    section: Optional[str] = None
    

@dataclass
class ConflictItem:
    """Represents a detected conflict between documents"""
    severity: SeverityLevel
    topic: str
    doc1_name: str
    doc1_section: str
    doc1_text: str
    doc1_page: str
    doc2_name: str
    doc2_section: str
    doc2_text: str
    doc2_page: str
    description: str
    resolution: Optional[str] = None


@dataclass
class GapItem:
    """Represents a detected gap or missing requirement"""
    severity: SeverityLevel
    topic: str
    source_doc: str
    source_section: str
    source_text: str
    missing_in: List[str]
    description: str


@dataclass
class AnalysisReport:
    """Complete analysis report"""
    analysis_type: AnalysisType
    documents: List[str]
    focus_area: Optional[str]
    conflicts: List[ConflictItem]
    gaps: List[GapItem]
    summary: str
    timestamp: str


class CrossReferenceEngine:
    """
    Engine for cross-referencing multiple documents and detecting inconsistencies.
    """
    
    def __init__(self, query_engine):
        """
        Initialize the Cross-Reference Engine
        
        Args:
            query_engine: Instance of QueryEngine for document retrieval
        """
        self.query_engine = query_engine
        self.logger = logging.getLogger(__name__)
        
    def analyze(
        self,
        doc_names: List[str],
        analysis_type: AnalysisType,
        focus_area: Optional[str] = None,
        top_k: int = 10
    ) -> AnalysisReport:
        """
        Perform cross-reference analysis on multiple documents
        
        Args:
            doc_names: List of document names to analyze
            analysis_type: Type of analysis to perform
            focus_area: Optional focus area (e.g., "fire safety", "cable sizing")
            top_k: Number of chunks to retrieve per document
            
        Returns:
            AnalysisReport with detected conflicts, gaps, and recommendations
        """
        if len(doc_names) < 2:
            raise ValueError("At least 2 documents required for cross-reference analysis")
            
        self.logger.info(f"Starting {analysis_type.value} analysis on {len(doc_names)} documents")
        
        if analysis_type == AnalysisType.CONFLICTS:
            return self._detect_conflicts(doc_names, focus_area, top_k)
        elif analysis_type == AnalysisType.GAPS:
            return self._analyze_gaps(doc_names, focus_area, top_k)
        elif analysis_type == AnalysisType.ALIGNMENT:
            return self._check_alignment(doc_names, focus_area, top_k)
        elif analysis_type == AnalysisType.REQUIREMENTS:
            return self._map_requirements(doc_names, focus_area, top_k)
        else:
            raise ValueError(f"Unknown analysis type: {analysis_type}")
    
    def _detect_conflicts(
        self,
        doc_names: List[str],
        focus_area: Optional[str],
        top_k: int
    ) -> AnalysisReport:
        """
        Detect conflicts between documents using semantic pre-filtering
        
        Args:
            doc_names: List of document names (first is base)
            focus_area: Optional focus area
            top_k: Number of chunks per document
            
        Returns:
            AnalysisReport with detected conflicts
        """
        from datetime import datetime
        
        conflicts = []
        
        if len(doc_names) < 2:
            summary = "Need at least 2 documents for comparison"
            return AnalysisReport(
                analysis_type=AnalysisType.CONFLICTS,
                documents=doc_names,
                focus_area=focus_area,
                conflicts=[],
                gaps=[],
                summary=summary,
                timestamp=datetime.now().isoformat()
            )
        
        base_doc = doc_names[0]
        compare_docs = doc_names[1:]
        
        self.logger.info(f"🎯 Smart comparison: {base_doc} vs {len(compare_docs)} documents")
        
        # Get ALL chunks from base document
        all_base_chunks = self._get_all_chunks_from_document(base_doc)
        self.logger.info(f"📄 Base document '{base_doc}': {len(all_base_chunks)} total chunks")
        
        if not all_base_chunks:
            summary = f"No content found in base document: {base_doc}"
            return AnalysisReport(
                analysis_type=AnalysisType.CONFLICTS,
                documents=doc_names,
                focus_area=focus_area,
                conflicts=[],
                gaps=[],
                summary=summary,
                timestamp=datetime.now().isoformat()
            )
        
        # Filter chunks by focus area if provided
        if focus_area:
            # Expand keywords with synonyms and translations
            focus_lower = focus_area.lower()
            keywords = focus_lower.split()
            
            # Add common synonyms for electrical terms
            expanded_keywords = set(keywords)
            keyword_map = {
                'kablo': ['cable', 'wire', 'conductor', 'wiring'],
                'kesiti': ['section', 'cross-section', 'cross section', 'size', 'sizing', 'csa'],
                'cable': ['kablo', 'wire', 'conductor'],
                'section': ['kesit', 'cross-section', 'size'],
                'earthing': ['topraklama', 'grounding', 'earth', 'ground'],
                'topraklama': ['earthing', 'grounding', 'earth'],
            }
            
            for keyword in keywords:
                if keyword in keyword_map:
                    expanded_keywords.update(keyword_map[keyword])
            
            self.logger.info(f"🔍 Search keywords: {expanded_keywords}")
            
            base_chunks = [
                chunk for chunk in all_base_chunks
                if any(kw in chunk.text.lower() for kw in expanded_keywords)
            ]
            self.logger.info(f"🎯 Filtered to {len(base_chunks)} chunks matching focus area '{focus_area}'")
        else:
            base_chunks = all_base_chunks
        
        if not base_chunks:
            summary = f"No chunks found matching focus area: {focus_area}"
            return AnalysisReport(
                analysis_type=AnalysisType.CONFLICTS,
                documents=doc_names,
                focus_area=focus_area,
                conflicts=[],
                gaps=[],
                summary=summary,
                timestamp=datetime.now().isoformat()
            )
        
        # For each base chunk, find semantically similar chunks in compare docs
        total_comparisons = len(base_chunks) * len(compare_docs)
        self.logger.info(f"🚀 Starting {total_comparisons} semantic searches...")
        
        for idx, base_chunk in enumerate(base_chunks):
            progress_pct = int((idx + 1) / len(base_chunks) * 100)
            if (idx + 1) % 5 == 0 or idx == 0:
                self.logger.info(f"⏳ Progress: {idx + 1}/{len(base_chunks)} chunks ({progress_pct}%)")
            
            # Search in each compare document
            for compare_doc in compare_docs:
                # Semantic search: find top-5 most relevant chunks (reduced from 10 for speed)
                relevant_chunks = self._semantic_search_in_document(
                    query_text=base_chunk.text,
                    document_name=compare_doc,
                    focus_area=focus_area,
                    top_k=5  # Reduced to 5 for faster analysis
                )
                
                if relevant_chunks:
                    # Compare base chunk against these relevant chunks only
                    chunk_conflicts = self._compare_single_chunk_against_many(
                        base_chunk,
                        relevant_chunks,
                        base_doc,
                        compare_doc
                    )
                    conflicts.extend(chunk_conflicts)
        
        self.logger.info(f"✅ Analysis complete! Found {len(conflicts)} potential conflicts")
        
        # Generate summary
        summary = self._generate_conflict_summary(conflicts, doc_names)
        
        return AnalysisReport(
            analysis_type=AnalysisType.CONFLICTS,
            documents=doc_names,
            focus_area=focus_area,
            conflicts=conflicts,
            gaps=[],
            summary=summary,
            timestamp=datetime.now().isoformat()
        )
    
    def _get_all_chunks_from_document(self, document_name: str, limit: int = None) -> List[DocumentChunk]:
        """
        Get chunks from a document via ChromaDB.
        
        Args:
            document_name: File name (e.g., "LDA.pdf")
            limit: Maximum number of chunks to retrieve (None = all available)
        """
        try:
            self.logger.info(f"🔍 Getting chunks from document: {document_name}")
            collection = self.query_engine.chroma_collection
            if not collection:
                self.logger.error("❌ Collection not available")
                return []
            
            # Get chunks for this document using file_name
            result = collection.get(
                where={"file_name": document_name},
                include=['documents', 'metadatas'],
                limit=limit  # None means get all
            )
            
            chunk_count = len(result.get('documents', []))
            self.logger.info(f"📦 Retrieved {chunk_count} chunks from ChromaDB")
            
            chunks = []
            if result and result.get('documents'):
                for i, text in enumerate(result['documents']):
                    metadata = result['metadatas'][i] if result.get('metadatas') else {}
                    chunk = DocumentChunk(
                        document_name=document_name,
                        page=metadata.get('page_label', 'N/A'),
                        text=text,
                        metadata=metadata,
                        section=metadata.get('section')
                    )
                    chunks.append(chunk)
            
            return chunks
            
        except Exception as e:
            self.logger.error(f"Error getting chunks from {document_name}: {e}")
            return []
    
    def _semantic_search_in_document(
        self,
        query_text: str,
        document_name: str,
        focus_area: Optional[str],
        top_k: int = 10
    ) -> List[DocumentChunk]:
        """
        Semantic search: find most relevant chunks in a document
        This dramatically reduces comparison time
        """
        try:
            # Build search query
            search_text = query_text
            if focus_area:
                search_text = f"{focus_area}: {query_text}"
            
            # Query only this specific document
            result = self.query_engine.query(
                question=search_text,
                document_filter=document_name,
                category_filter=None,
                filters=None
            )
            
            chunks = []
            if result.get("sources"):
                for source in result["sources"]:
                    chunk = DocumentChunk(
                        document_name=source.get("document", document_name),
                        page=source.get("page", "N/A"),
                        text=source.get("text", ""),
                        metadata=source.get("metadata", {}),
                        section=source.get("metadata", {}).get("section")
                    )
                    chunks.append(chunk)
            
            return chunks
            
        except Exception as e:
            self.logger.error(f"Semantic search error in {document_name}: {e}")
            return []
    
    def _compare_single_chunk_against_many(
        self,
        base_chunk: DocumentChunk,
        compare_chunks: List[DocumentChunk],
        base_doc: str,
        compare_doc: str
    ) -> List[ConflictItem]:
        """Compare one base chunk against multiple candidate chunks"""
        conflicts = []
        
        conflict_keywords = [
            ("maximum", "max"), ("minimum", "min"),
            ("shall", "must"), ("impedance", "resistance"),
            ("voltage", "current"), ("temperature", "°C"),
            ("mm²", "mm2", "cross-sectional area"),
            ("rating", "capacity"), ("complies", "compliance")
        ]
        
        for compare_chunk in compare_chunks:
            conflict = self._detect_conflict_in_pair(
                base_chunk,
                compare_chunk,
                base_doc,
                compare_doc,
                conflict_keywords
            )
            if conflict:
                conflicts.append(conflict)
        
        return conflicts
    
    def _compare_document_chunks(
        self,
        chunks1: List[DocumentChunk],
        chunks2: List[DocumentChunk],
        doc1_name: str,
        doc2_name: str
    ) -> List[ConflictItem]:
        """
        Compare chunks from two documents to detect conflicts
        
        Args:
            chunks1: Chunks from first document
            chunks2: Chunks from second document
            doc1_name: Name of first document
            doc2_name: Name of second document
            
        Returns:
            List of detected conflicts
        """
        conflicts = []
        
        # Keywords that indicate potential conflicts
        conflict_keywords = [
            ("maximum", "max"), ("minimum", "min"),
            ("shall", "must"), ("impedance", "resistance"),
            ("voltage", "current"), ("temperature", "°C"),
            ("mm²", "mm2", "cross-sectional area"),
            ("rating", "capacity"), ("complies", "compliance")
        ]
        
        for c1 in chunks1:
            for c2 in chunks2:
                # Check for semantic similarity and value differences
                conflict = self._detect_conflict_in_pair(
                    c1, c2, doc1_name, doc2_name, conflict_keywords
                )
                if conflict:
                    conflicts.append(conflict)
        
        return conflicts
    
    def _detect_conflict_in_pair(
        self,
        chunk1: DocumentChunk,
        chunk2: DocumentChunk,
        doc1_name: str,
        doc2_name: str,
        conflict_keywords: List[Tuple[str, ...]]
    ) -> Optional[ConflictItem]:
        """
        Detect if two chunks contain conflicting information
        
        Args:
            chunk1: First chunk
            chunk2: Second chunk
            doc1_name: First document name
            doc2_name: Second document name
            conflict_keywords: Keywords indicating potential conflicts
            
        Returns:
            ConflictItem if conflict detected, None otherwise
        """
        import re
        
        text1_lower = chunk1.text.lower()
        text2_lower = chunk2.text.lower()
        
        # Check for shared keywords
        shared_topics = []
        for keyword_group in conflict_keywords:
            if any(kw in text1_lower for kw in keyword_group) and \
               any(kw in text2_lower for kw in keyword_group):
                shared_topics.append(keyword_group[0])
        
        if not shared_topics:
            return None
        
        # Extract numerical values
        numbers1 = re.findall(r'\d+\.?\d*', chunk1.text)
        numbers2 = re.findall(r'\d+\.?\d*', chunk2.text)
        
        # If both contain numbers and shared keywords, likely a conflict
        if numbers1 and numbers2 and shared_topics:
            # Simple heuristic: different numbers = potential conflict
            if set(numbers1) != set(numbers2):
                severity = SeverityLevel.MEDIUM
                
                # Check for "shall" or "must" (mandatory requirements)
                if any(word in text1_lower or word in text2_lower 
                       for word in ["shall", "must", "required", "mandatory"]):
                    severity = SeverityLevel.HIGH
                
                topic = ", ".join(shared_topics)
                
                return ConflictItem(
                    severity=severity,
                    topic=topic.title(),
                    doc1_name=doc1_name,
                    doc1_section=chunk1.section or f"Page {chunk1.page}",
                    doc1_text=chunk1.text[:200] + "..." if len(chunk1.text) > 200 else chunk1.text,
                    doc1_page=chunk1.page,
                    doc2_name=doc2_name,
                    doc2_section=chunk2.section or f"Page {chunk2.page}",
                    doc2_text=chunk2.text[:200] + "..." if len(chunk2.text) > 200 else chunk2.text,
                    doc2_page=chunk2.page,
                    description=f"Different values found for {topic} between documents",
                    resolution=None
                )
        
        return None
    
    def _analyze_gaps(
        self,
        doc_names: List[str],
        focus_area: Optional[str],
        top_k: int
    ) -> AnalysisReport:
        """
        Analyze gaps and missing requirements across documents
        
        Args:
            doc_names: List of document names
            focus_area: Optional focus area
            top_k: Number of chunks per document
            
        Returns:
            AnalysisReport with detected gaps
        """
        from datetime import datetime
        
        # Placeholder implementation
        gaps = []
        summary = f"Gap analysis across {len(doc_names)} documents (implementation in progress)"
        
        return AnalysisReport(
            analysis_type=AnalysisType.GAPS,
            documents=doc_names,
            focus_area=focus_area,
            conflicts=[],
            gaps=gaps,
            summary=summary,
            timestamp=datetime.now().isoformat()
        )
    
    def _check_alignment(
        self,
        doc_names: List[str],
        focus_area: Optional[str],
        top_k: int
    ) -> AnalysisReport:
        """Check alignment between documents"""
        from datetime import datetime
        
        summary = f"Alignment check across {len(doc_names)} documents (implementation in progress)"
        
        return AnalysisReport(
            analysis_type=AnalysisType.ALIGNMENT,
            documents=doc_names,
            focus_area=focus_area,
            conflicts=[],
            gaps=[],
            summary=summary,
            timestamp=datetime.now().isoformat()
        )
    
    def _map_requirements(
        self,
        doc_names: List[str],
        focus_area: Optional[str],
        top_k: int
    ) -> AnalysisReport:
        """Map requirements across documents"""
        from datetime import datetime
        
        summary = f"Requirements mapping across {len(doc_names)} documents (implementation in progress)"
        
        return AnalysisReport(
            analysis_type=AnalysisType.REQUIREMENTS,
            documents=doc_names,
            focus_area=focus_area,
            conflicts=[],
            gaps=[],
            summary=summary,
            timestamp=datetime.now().isoformat()
        )
    
    def _generate_conflict_summary(
        self,
        conflicts: List[ConflictItem],
        doc_names: List[str]
    ) -> str:
        """Generate summary text for conflict analysis"""
        
        if len(doc_names) < 2:
            return "Insufficient documents for comparison"
        
        base_doc = doc_names[0]
        compare_docs = doc_names[1:]
        
        if not conflicts:
            return f"No conflicts detected.\n\nBase: {base_doc}\nCompared against: {', '.join(compare_docs)}"
        
        high = sum(1 for c in conflicts if c.severity == SeverityLevel.HIGH)
        medium = sum(1 for c in conflicts if c.severity == SeverityLevel.MEDIUM)
        low = sum(1 for c in conflicts if c.severity == SeverityLevel.LOW)
        
        summary = f"Detected {len(conflicts)} potential conflict(s):\n"
        summary += f"  🔴 High Severity: {high}\n"
        summary += f"  🟡 Medium Severity: {medium}\n"
        summary += f"  🟢 Low Severity: {low}\n\n"
        summary += f"Base Document: {base_doc}\n"
        summary += f"Compared Against: {', '.join(compare_docs)}"
        
        return summary
