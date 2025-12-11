"""
Cross-Reference Engine V2 - Compliance & Gap Analysis

Designed for real-world engineering document comparison:
- Compliance Check: Does your spec meet standards/requirements?
- Gap Analysis: What's missing from your spec?
- Value Comparison: Do numerical values match?

Use Cases:
1. Company Specification vs Standards (BS, EN, IEC, IS)
2. Company Specification vs Government Requirements (LDA)
3. Company Specification vs Employer Requirements
"""

import re
import json
from typing import List, Dict, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from collections import defaultdict

from loguru import logger


class AnalysisMode(Enum):
    """Analysis modes for cross-reference"""
    COMPLIANCE_CHECK = "compliance"      # Check if spec meets requirements
    GAP_ANALYSIS = "gaps"                # Find missing requirements
    VALUE_COMPARISON = "values"          # Compare numerical values
    STANDARD_COVERAGE = "standards"      # Check standard references coverage
    FULL_AUDIT = "full"                  # All of the above


class IssueSeverity(Enum):
    """Severity levels for detected issues"""
    CRITICAL = "critical"    # Must fix - regulatory/safety issue
    HIGH = "high"           # Should fix - major non-compliance
    MEDIUM = "medium"       # Consider - potential issue
    LOW = "low"             # Info - minor difference
    INFO = "info"           # FYI - observation


class IssueCategory(Enum):
    """Categories of issues"""
    VALUE_MISMATCH = "value_mismatch"
    MISSING_REQUIREMENT = "missing_requirement"
    CONFLICTING_SPEC = "conflicting_spec"
    STANDARD_NOT_REFERENCED = "standard_not_referenced"
    INCOMPLETE_COVERAGE = "incomplete_coverage"


@dataclass
class ComplianceIssue:
    """Represents a detected compliance issue"""
    severity: IssueSeverity
    category: IssueCategory
    topic: str
    description: str
    
    # Source document (your spec)
    source_doc: str
    source_section: str
    source_text: str
    source_page: str
    
    # Reference document (standard/requirement)
    reference_doc: str
    reference_section: str
    reference_text: str
    reference_page: str
    
    # Optional fields (must come after required fields)
    source_value: Optional[str] = None
    reference_value: Optional[str] = None
    recommendation: Optional[str] = None
    standard_clause: Optional[str] = None  # e.g., "BS EN 62305-1, Clause 4.2"


@dataclass
class GapItem:
    """Represents a missing requirement"""
    severity: IssueSeverity
    topic: str
    description: str
    
    # What's missing
    missing_requirement: str
    reference_doc: str
    reference_section: str
    reference_text: str
    reference_page: str
    
    # Why it matters
    impact: str
    recommendation: str
    mandatory: bool = False  # "shall", "must" = True


@dataclass
class ValueComparison:
    """Represents a numerical value comparison"""
    parameter: str
    unit: str
    
    source_doc: str
    source_value: float
    source_section: str
    
    reference_doc: str
    reference_value: float
    reference_section: str
    
    difference: float
    percentage_diff: float
    status: str  # "MATCH", "HIGHER", "LOWER", "CONFLICT"
    severity: IssueSeverity
    note: str


@dataclass
class ComplianceReport:
    """Complete compliance analysis report"""
    # Metadata
    analysis_mode: AnalysisMode
    source_document: str  # Your spec
    reference_documents: List[str]  # Standards/requirements
    focus_area: Optional[str]
    timestamp: str
    analysis_duration: float
    
    # Results
    compliance_issues: List[ComplianceIssue] = field(default_factory=list)
    gaps: List[GapItem] = field(default_factory=list)
    value_comparisons: List[ValueComparison] = field(default_factory=list)
    
    # Summary
    compliance_score: float = 0.0  # 0-100%
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    
    # Standards coverage
    standards_referenced: List[str] = field(default_factory=list)
    standards_missing: List[str] = field(default_factory=list)
    
    summary: str = ""


class CrossReferenceEngineV2:
    """
    Advanced Cross-Reference Engine for Engineering Document Compliance
    
    Workflow:
    1. Load source document (your specification)
    2. Load reference documents (standards, requirements)
    3. Extract requirements and specifications from both
    4. Compare and detect:
       - Value mismatches (numbers, specs)
       - Missing mandatory requirements
       - Conflicting specifications
       - Missing standard references
    5. Generate actionable report
    """
    
    def __init__(self, query_engine, graph_manager=None):
        """
        Initialize the engine
        
        Args:
            query_engine: QueryEngine instance for document retrieval
            graph_manager: Optional GraphManager for relationship queries
        """
        self.query_engine = query_engine
        self.graph_manager = graph_manager
        
        # Patterns for extraction
        self.mandatory_patterns = [
            r'\bshall\b', r'\bmust\b', r'\brequired\b', r'\bmandatory\b',
            r'\bcompulsory\b', r'\bessential\b'
        ]
        
        self.value_patterns = {
            # === ELECTRICAL ENGINEERING ===
            'temperature': r'(\d+(?:\.\d+)?)\s*°?C',
            'voltage': r'(\d+(?:\.\d+)?)\s*V(?:olts?)?',
            'current': r'(\d+(?:\.\d+)?)\s*A(?:mps?)?',
            'power': r'(\d+(?:\.\d+)?)\s*(?:kW|MW|W|VA|kVA|MVA)',
            'resistance': r'(\d+(?:\.\d+)?)\s*(?:Ω|ohms?)',
            'impedance': r'(\d+(?:\.\d+)?)\s*(?:Ω|ohms?)(?:/km)?',
            'cable_size': r'(\d+(?:\.\d+)?)\s*mm[²2]',
            'frequency': r'(\d+(?:\.\d+)?)\s*Hz',
            
            # === MECHANICAL ENGINEERING ===
            'pressure': r'(\d+(?:\.\d+)?)\s*(?:bar|psi|kPa|MPa|Pa)',
            'flow_rate': r'(\d+(?:\.\d+)?)\s*(?:l/s|L/s|m³/h|m3/h|l/min|L/min|gpm|cfm)',
            'speed': r'(\d+(?:\.\d+)?)\s*(?:rpm|RPM|rev/min)',
            'torque': r'(\d+(?:\.\d+)?)\s*(?:Nm|N\.m|kNm)',
            'diameter': r'(\d+(?:\.\d+)?)\s*(?:mm|cm|inch|in|")\s*(?:dia|diameter|Ø|ø)?',
            'thickness': r'(\d+(?:\.\d+)?)\s*(?:mm|cm)\s*(?:thick|thickness)?',
            'weight': r'(\d+(?:\.\d+)?)\s*(?:kg|ton|tonne|lb|lbs)',
            'volume': r'(\d+(?:\.\d+)?)\s*(?:m³|m3|litre|liter|L|gallon)',
            'capacity': r'(\d+(?:\.\d+)?)\s*(?:kW|BTU|BTU/h|tons?|TR)',
            
            # === SUSTAINABILITY ENGINEERING ===
            'u_value': r'(\d+(?:\.\d+)?)\s*W/m[²2]K',
            'r_value': r'(\d+(?:\.\d+)?)\s*m[²2]K/W',
            'noise_level': r'(\d+(?:\.\d+)?)\s*(?:dB|dBA)',
            'lux_level': r'(\d+(?:\.\d+)?)\s*(?:lux|lx)',
            'air_quality': r'(\d+(?:\.\d+)?)\s*(?:ppm|μg/m³|mg/m³)',
            'energy_consumption': r'(\d+(?:\.\d+)?)\s*(?:kWh|MWh|GJ)',
            'carbon_emission': r'(\d+(?:\.\d+)?)\s*(?:kgCO2|tCO2|kgCO2e)',
            'water_consumption': r'(\d+(?:\.\d+)?)\s*(?:m³/day|L/day|gallon/day)',
            'cop': r'(\d+(?:\.\d+)?)\s*(?:COP|EER|SEER)',  # Coefficient of Performance
            
            # === COMMON ===
            'percentage': r'(\d+(?:\.\d+)?)\s*%',
            'area': r'(\d+(?:\.\d+)?)\s*(?:m²|m2|sq\.?m|ft²|sq\.?ft)',
            'length': r'(\d+(?:\.\d+)?)\s*(?:m|mm|km)',
            'time': r'(\d+(?:\.\d+)?)\s*(?:ms|s|sec|min|hours?|hrs?)',
        }
        
        # Standard patterns - includes hyphenated numbers like EN 61386-1-21-22-23-24
        self.standard_pattern = r'\b(IS|EN|IEC|BS|NFPA|IEEE|ISO|ASTM|DIN)[\s-]?\d+(?:[-/:]\d+)*(?:\s*[:\(]\d{4}[:\)])?'
        
        # Patterns to identify text that's part of a standard reference
        self.standard_context_pattern = r'\b(?:IS|EN|IEC|BS|NFPA|IEEE|ISO|ASTM|DIN)[\s-]?\d+[-/:0-9]*'
        
        logger.info("✅ CrossReferenceEngine V2 initialized")
    
    def analyze(
        self,
        source_doc: str,
        reference_docs: List[str],
        mode: AnalysisMode = AnalysisMode.FULL_AUDIT,
        focus_area: Optional[str] = None,
        section_filter: Optional[str] = None
    ) -> ComplianceReport:
        """
        Main analysis entry point
        
        Args:
            source_doc: Your specification document name
            reference_docs: List of reference document names (standards, LDA, etc.)
            mode: Analysis mode
            focus_area: Optional focus (e.g., "fire safety", "cable sizing")
            section_filter: Optional section number filter
            
        Returns:
            ComplianceReport with all findings
        """
        start_time = datetime.now()
        logger.info(f"🔍 Starting {mode.value} analysis")
        logger.info(f"   Source: {source_doc}")
        logger.info(f"   References: {reference_docs}")
        logger.info(f"   Focus: {focus_area or 'All areas'}")
        
        # Initialize report
        report = ComplianceReport(
            analysis_mode=mode,
            source_document=source_doc,
            reference_documents=reference_docs,
            focus_area=focus_area,
            timestamp=datetime.now().isoformat(),
            analysis_duration=0.0
        )
        
        try:
            # Step 1: Get chunks from source document
            source_chunks = self._get_document_chunks(
                source_doc, focus_area, section_filter
            )
            logger.info(f"📄 Source document: {len(source_chunks)} chunks")
            
            # Step 2: Get chunks from reference documents
            reference_chunks = {}
            for ref_doc in reference_docs:
                chunks = self._get_document_chunks(
                    ref_doc, focus_area, section_filter
                )
                reference_chunks[ref_doc] = chunks
                logger.info(f"📚 Reference '{ref_doc}': {len(chunks)} chunks")
            
            # Step 3: Run analyses based on mode
            if mode in [AnalysisMode.COMPLIANCE_CHECK, AnalysisMode.FULL_AUDIT]:
                issues = self._check_compliance(source_chunks, reference_chunks, focus_area)
                report.compliance_issues.extend(issues)
            
            if mode in [AnalysisMode.GAP_ANALYSIS, AnalysisMode.FULL_AUDIT]:
                gaps = self._analyze_gaps(source_chunks, reference_chunks, focus_area)
                report.gaps.extend(gaps)
            
            if mode in [AnalysisMode.VALUE_COMPARISON, AnalysisMode.FULL_AUDIT]:
                comparisons = self._compare_values(source_chunks, reference_chunks, focus_area)
                report.value_comparisons.extend(comparisons)
            
            if mode in [AnalysisMode.STANDARD_COVERAGE, AnalysisMode.FULL_AUDIT]:
                self._check_standard_coverage(source_chunks, reference_chunks, report)
            
            # Step 4: Calculate summary
            self._calculate_summary(report)
            
        except Exception as e:
            logger.error(f"❌ Analysis failed: {e}", exc_info=True)
            report.summary = f"Analysis failed: {str(e)}"
        
        # Calculate duration
        report.analysis_duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ Analysis complete in {report.analysis_duration:.1f}s")
        
        return report
    
    def _get_document_chunks(
        self,
        doc_name: str,
        focus_area: Optional[str],
        section_filter: Optional[str]
    ) -> List[Dict]:
        """Get all chunks from a document with optional filtering"""
        chunks = []
        
        try:
            if not hasattr(self.query_engine, 'client'):
                return chunks
            
            client = self.query_engine.client
            collection_name = self.query_engine.settings.get_collection_name()
            
            # Build filter using Qdrant models
            from qdrant_client.http import models
            
            scroll_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="file_name",
                        match=models.MatchValue(value=doc_name)
                    )
                ]
            )
            
            offset = None
            while True:
                points, next_offset = client.scroll(
                    collection_name=collection_name,
                    limit=100,
                    offset=offset,
                    with_payload=True,
                    with_vectors=False,
                    scroll_filter=scroll_filter
                )
                
                for point in points:
                    payload = point.payload or {}
                    
                    # Get text content
                    text = self._extract_text(payload)
                    if not text:
                        continue
                    
                    # Apply section filter
                    if section_filter:
                        section_num = payload.get('section_number', '')
                        if not section_num.startswith(section_filter):
                            continue
                    
                    # Apply focus area filter
                    if focus_area and not self._matches_focus(text, focus_area):
                        continue
                    
                    chunk = {
                        'text': text,
                        'page': payload.get('page_label', 'N/A'),
                        'section_number': payload.get('section_number', ''),
                        'section_title': payload.get('section_title', ''),
                        'has_mandatory': payload.get('has_mandatory_requirements', False),
                        'spec_values': payload.get('spec_values', []),
                        'referenced_standards': payload.get('referenced_standards', []),
                        'requirement_types': payload.get('requirement_types', []),
                        'metadata': payload
                    }
                    chunks.append(chunk)
                
                offset = next_offset
                if offset is None:
                    break
            
        except Exception as e:
            logger.error(f"Error getting chunks from {doc_name}: {e}")
        
        return chunks
    
    def _extract_text(self, payload: Dict) -> str:
        """Extract text from payload"""
        text = payload.get('original_text') or payload.get('text', '')
        
        if not text:
            node_content = payload.get('_node_content', '')
            if isinstance(node_content, str) and node_content.startswith('{'):
                try:
                    content = json.loads(node_content)
                    text = content.get('text', '')
                except:
                    pass
        
        return text
    
    def _matches_focus(self, text: str, focus_area: str) -> bool:
        """Check if text matches focus area"""
        focus_lower = focus_area.lower()
        text_lower = text.lower()
        
        # Expand keywords
        keyword_expansions = {
            'cable': ['cable', 'kablo', 'wire', 'conductor', 'wiring', 'core'],
            'sizing': ['sizing', 'size', 'cross-section', 'cross section', 'csa', 'mm²', 'mm2', 'area', 'section'],
            'cross': ['cross-section', 'cross section', 'csa', 'area'],
            'fire': ['fire', 'yangın', 'smoke', 'alarm', 'detection'],
            'earthing': ['earthing', 'grounding', 'topraklama', 'earth', 'ground'],
            'lighting': ['lighting', 'aydınlatma', 'lux', 'luminaire', 'lamp'],
            'ups': ['ups', 'uninterruptible', 'battery', 'backup'],
            'generator': ['generator', 'genset', 'diesel', 'standby'],
            'hvac': ['hvac', 'ventilation', 'cooling', 'heating', 'air'],
            'security': ['security', 'güvenlik', 'access', 'cctv', 'camera'],
            'conduit': ['conduit', 'duct', 'ducting', 'trunking', 'containment'],
            'distribution': ['distribution', 'panel', 'board', 'switchgear', 'mcc'],
            'socket': ['socket', 'outlet', 'receptacle'],
            'motor': ['motor', 'drive', 'vfd', 'inverter'],
            'transformer': ['transformer', 'trafo', 'tx'],
        }
        
        keywords = [focus_lower]
        
        # Split focus area into words and expand each
        focus_words = focus_lower.split()
        for word in focus_words:
            keywords.append(word)
            for key, expansions in keyword_expansions.items():
                if key in word or word in expansions:
                    keywords.extend(expansions)
        
        # Also add direct expansions
        for key, expansions in keyword_expansions.items():
            if key in focus_lower:
                keywords.extend(expansions)
        
        return any(kw in text_lower for kw in keywords)
    
    def _get_priority_types(self, focus_area: Optional[str]) -> set:
        """Get priority parameter types based on focus area"""
        if not focus_area:
            return set()  # Empty = no filtering
        
        focus_lower = focus_area.lower()
        
        # =====================================================
        # ELECTRICAL ENGINEERING
        # =====================================================
        
        # Cable sizing related
        if 'sizing' in focus_lower or 'cross' in focus_lower or 'section' in focus_lower or 'mm' in focus_lower:
            return {'cable_size', 'current', 'voltage'}
        elif 'cable' in focus_lower and ('size' in focus_lower or 'area' in focus_lower):
            return {'cable_size', 'current', 'voltage'}
        
        # Wiring / Installation - focus on cable, current, voltage (not random lengths)
        elif 'wiring' in focus_lower or 'installation' in focus_lower:
            return {'cable_size', 'current', 'voltage', 'power'}
        
        # Electrical general - similar to wiring
        elif 'electrical' in focus_lower and not any(x in focus_lower for x in ['fire', 'earth', 'light']):
            return {'cable_size', 'current', 'voltage', 'power'}
        
        # Current/Amperage
        elif 'current' in focus_lower or 'amp' in focus_lower:
            return {'current', 'cable_size'}
        
        # Voltage
        elif 'voltage' in focus_lower or 'volt' in focus_lower:
            return {'voltage'}
        
        # Fire safety
        elif 'fire' in focus_lower or 'smoke' in focus_lower:
            return {'temperature', 'time'}
        
        # Earthing/Grounding
        elif 'earthing' in focus_lower or 'ground' in focus_lower or 'earth' in focus_lower:
            return {'resistance', 'impedance', 'current'}
        
        # Lighting
        elif 'lighting' in focus_lower or 'lux' in focus_lower or 'luminaire' in focus_lower:
            return {'power', 'percentage', 'lux_level'}
        
        # Conduit/Containment - lengths are relevant here
        elif 'conduit' in focus_lower or 'duct' in focus_lower or 'trunking' in focus_lower:
            return {'length', 'cable_size', 'diameter'}
        
        # Distribution/Panels - current ratings
        elif 'distribution' in focus_lower or 'panel' in focus_lower or 'board' in focus_lower:
            return {'current', 'voltage', 'power'}
        
        # Motor/Drive
        elif 'motor' in focus_lower or 'drive' in focus_lower:
            return {'current', 'voltage', 'power', 'speed', 'torque'}
        
        # UPS/Battery
        elif 'ups' in focus_lower or 'battery' in focus_lower:
            return {'current', 'voltage', 'power', 'time'}
        
        # Generator
        elif 'generator' in focus_lower or 'genset' in focus_lower:
            return {'current', 'voltage', 'power', 'frequency'}
        
        # Protection devices
        elif 'protection' in focus_lower or 'breaker' in focus_lower or 'fuse' in focus_lower:
            return {'current', 'time'}
        
        # =====================================================
        # MECHANICAL ENGINEERING
        # =====================================================
        
        # HVAC
        elif 'hvac' in focus_lower or 'air condition' in focus_lower or 'cooling' in focus_lower or 'heating' in focus_lower:
            return {'temperature', 'power', 'capacity', 'flow_rate', 'pressure', 'cop'}
        
        # Ventilation
        elif 'ventilation' in focus_lower or 'fan' in focus_lower or 'ahu' in focus_lower:
            return {'flow_rate', 'pressure', 'power', 'noise_level'}
        
        # Plumbing
        elif 'plumbing' in focus_lower or 'water' in focus_lower or 'pipe' in focus_lower:
            return {'flow_rate', 'pressure', 'diameter', 'volume'}
        
        # Pump
        elif 'pump' in focus_lower:
            return {'flow_rate', 'pressure', 'power', 'speed'}
        
        # Boiler
        elif 'boiler' in focus_lower:
            return {'temperature', 'pressure', 'power', 'capacity'}
        
        # Mechanical general
        elif 'mechanical' in focus_lower:
            return {'pressure', 'flow_rate', 'temperature', 'power', 'capacity'}
        
        # =====================================================
        # SUSTAINABILITY ENGINEERING
        # =====================================================
        
        # Energy efficiency
        elif 'energy' in focus_lower or 'efficiency' in focus_lower:
            return {'power', 'energy_consumption', 'cop', 'percentage', 'u_value', 'r_value'}
        
        # Thermal / Insulation
        elif 'thermal' in focus_lower or 'insulation' in focus_lower or 'envelope' in focus_lower:
            return {'u_value', 'r_value', 'temperature', 'thickness'}
        
        # Carbon / Emissions
        elif 'carbon' in focus_lower or 'emission' in focus_lower or 'co2' in focus_lower:
            return {'carbon_emission', 'energy_consumption', 'percentage'}
        
        # LEED / BREEAM / Green building
        elif 'leed' in focus_lower or 'breeam' in focus_lower or 'green' in focus_lower or 'sustainable' in focus_lower:
            return {'u_value', 'r_value', 'lux_level', 'energy_consumption', 'water_consumption', 'percentage'}
        
        # Acoustics / Noise
        elif 'acoustic' in focus_lower or 'noise' in focus_lower or 'sound' in focus_lower:
            return {'noise_level'}
        
        # Indoor air quality
        elif 'air quality' in focus_lower or 'iaq' in focus_lower:
            return {'air_quality', 'flow_rate', 'percentage'}
        
        # =====================================================
        # DEFAULT - "All areas" or unrecognized focus
        # =====================================================
        
        # Default filter: Include meaningful technical parameters, exclude noise (random lengths, times)
        return {
            # Electrical
            'cable_size', 'current', 'voltage', 'power', 'resistance', 'impedance', 'frequency',
            # Mechanical
            'pressure', 'flow_rate', 'capacity', 'speed', 'torque',
            # Sustainability
            'u_value', 'r_value', 'noise_level', 'lux_level', 'cop', 'energy_consumption',
            # Common
            'temperature', 'percentage', 'diameter', 'thickness', 'weight', 'volume', 'area'
        }
        # Note: 'length' and 'time' excluded from default to reduce false positives
    
    def _check_compliance(
        self,
        source_chunks: List[Dict],
        reference_chunks: Dict[str, List[Dict]],
        focus_area: Optional[str]
    ) -> List[ComplianceIssue]:
        """
        Check if source document complies with reference documents
        
        Strategy:
        1. Find mandatory requirements in reference docs ("shall", "must")
        2. Search for corresponding content in source doc
        3. Compare values and requirements
        """
        issues = []
        
        # Get priority types for focus area
        priority_types = self._get_priority_types(focus_area)
        
        for ref_doc, ref_chunks in reference_chunks.items():
            logger.info(f"🔍 Checking compliance against: {ref_doc}")
            
            # Find mandatory requirements in reference
            mandatory_chunks = [c for c in ref_chunks if c.get('has_mandatory')]
            logger.info(f"   Found {len(mandatory_chunks)} mandatory requirement chunks")
            
            for ref_chunk in mandatory_chunks:
                ref_text = ref_chunk['text']
                
                # Extract the specific requirement
                requirements = self._extract_requirements(ref_text, priority_types)
                
                for req in requirements:
                    # Skip if no relevant values for the focus area
                    if priority_types and not req.get('values'):
                        continue
                    
                    # Search for matching content in source
                    matching_source = self._find_matching_content(
                        req['topic'], source_chunks
                    )
                    
                    if matching_source:
                        # Compare values
                        conflict = self._detect_value_conflict(
                            source_chunk=matching_source,
                            ref_chunk=ref_chunk,
                            requirement=req,
                            ref_doc=ref_doc,
                            priority_types=priority_types
                        )
                        if conflict:
                            issues.append(conflict)
        
        return issues
    
    def _extract_requirements(self, text: str, priority_types: set = None) -> List[Dict]:
        """Extract specific requirements from text"""
        requirements = []
        
        # Split into sentences
        sentences = re.split(r'[.;]\s+', text)
        
        for sentence in sentences:
            # Check if mandatory
            is_mandatory = any(
                re.search(pattern, sentence, re.IGNORECASE)
                for pattern in self.mandatory_patterns
            )
            
            if is_mandatory:
                # Extract topic keywords
                topic_words = []
                important_words = re.findall(r'\b[A-Z][a-z]+(?:\s+[a-z]+)*\b', sentence)
                topic_words.extend(important_words[:3])
                
                # Extract any values
                values = self._extract_all_values(sentence)
                
                # Filter values by priority types if specified
                if priority_types and values:
                    values = [v for v in values if v['type'] in priority_types]
                
                requirements.append({
                    'text': sentence.strip(),
                    'mandatory': True,
                    'topic': ' '.join(topic_words) if topic_words else sentence[:50],
                    'values': values
                })
        
        return requirements
    
    def _extract_all_values(self, text: str) -> List[Dict]:
        """Extract all numerical values with units from text"""
        values = []
        
        # Skip if text contains standard numbers that might be confused with values
        # Check for patterns like "EN 62305" before extracting
        standard_matches = re.findall(self.standard_pattern, text)
        standard_numbers = set()
        for std in standard_matches:
            # Extract numbers from standard names
            nums = re.findall(r'\d+', std)
            standard_numbers.update(float(n) for n in nums)
        
        # Also skip year-like numbers (1990-2030)
        year_pattern = r'\b(19[89]\d|20[0-3]\d)\b'
        years = set(float(y) for y in re.findall(year_pattern, text))
        
        # Find ALL numbers that appear in standard references (including hyphenated parts)
        # This catches EN 61386-1-21-22-23-24 -> filters out 61386, 1, 21, 22, 23, 24
        std_context_matches = re.findall(self.standard_context_pattern, text)
        for std_ref in std_context_matches:
            nums = re.findall(r'\d+', std_ref)
            standard_numbers.update(float(n) for n in nums)
        
        for param_type, pattern in self.value_patterns.items():
            # Use finditer to get match objects with position
            for match in re.finditer(pattern, text, re.IGNORECASE):
                try:
                    value = float(match.group(1))
                    
                    # Filter out unlikely values
                    # Skip if this number appears in a standard reference
                    if value in standard_numbers:
                        continue
                    
                    # Skip year-like numbers
                    if value in years:
                        continue
                    
                    # Skip values that look like standard numbers (4-5 digit round numbers)
                    if value >= 1000 and value == int(value):
                        # Check if it could be a standard number
                        if 1000 <= value <= 99999:
                            # Additional check: is it surrounded by standard context?
                            match_pos = match.start()
                            context_start = max(0, match_pos - 25)
                            context_end = min(len(text), match.end() + 10)
                            context = text[context_start:context_end].lower()
                            if any(prefix in context for prefix in ['en ', 'en-', 'bs ', 'bs-', 'is ', 'is-', 'iec ', 'iec-', 'iso ']):
                                continue
                    
                    # Apply reasonable ranges for each type
                    valid = True
                    if param_type == 'temperature':
                        if value > 500 or value < -50:  # Reasonable temp range
                            valid = False
                    elif param_type == 'voltage':
                        if value > 50000:  # Skip unreasonable voltages
                            valid = False
                    elif param_type == 'current':
                        if value > 1000:  # Skip unreasonable currents
                            valid = False
                    elif param_type == 'cable_size':
                        if value > 1000:  # Cable sizes usually < 1000mm²
                            valid = False
                    elif param_type == 'percentage':
                        if value > 100:  # Percentages max 100
                            valid = False
                    elif param_type == 'time':
                        if value > 1000:  # Time values usually < 1000s
                            valid = False
                    elif param_type == 'length':
                        if value > 5000:  # Skip unreasonably large lengths
                            valid = False
                    
                    if valid:
                        # Extract context - what is this value describing?
                        match_pos = match.start()
                        context_start = max(0, match_pos - 60)
                        context_end = min(len(text), match.end() + 20)
                        surrounding = text[context_start:context_end].lower()
                        
                        # Extract subject keywords from context
                        subject = self._extract_value_subject(surrounding, param_type)
                        
                        values.append({
                            'type': param_type,
                            'value': value,
                            'original': match.group(0),
                            'subject': subject,
                            'context': surrounding.strip()
                        })
                except ValueError:
                    pass
        
        return values
    
    def _extract_value_subject(self, context: str, param_type: str) -> str:
        """Extract what the value is describing (e.g., 'cable length', 'conductor size')"""
        
        # Subject keywords that describe what's being measured
        subject_patterns = {
            'length': [
                r'(cable|conductor|wire|core|run|route|trench|duct|conduit|pipe|branch|main)\s+(?:length|run|distance)',
                r'(maximum|minimum|min|max)\s+(?:length|distance|run)',
                r'(depth|height|width|spacing|clearance|distance)',
                r'(?:length|distance|run)\s+of\s+(\w+)',
            ],
            'cable_size': [
                r'(cable|conductor|wire|core)\s+(?:size|cross.?section|area|csa)',
                r'(minimum|maximum|min|max)\s+(?:size|cross.?section|csa)',
                r'(\d+)\s*mm[²2]?\s*(cable|conductor|wire)?',
            ],
            'current': [
                r'(rated|nominal|maximum|minimum|full.?load|fault)\s+current',
                r'(breaker|fuse|mcb|rcbo|rcd)\s+(?:rating|current)',
                r'current\s+(?:rating|capacity)',
            ],
            'voltage': [
                r'(rated|nominal|supply|operating|system)\s+voltage',
                r'(low|medium|high)\s+voltage',
                r'voltage\s+(?:rating|drop|level)',
            ],
            'temperature': [
                r'(ambient|operating|maximum|minimum)\s+temperature',
                r'temperature\s+(?:rating|range|limit)',
            ],
            'percentage': [
                r'(voltage|power|load)\s+(?:drop|factor|efficiency)',
                r'(minimum|maximum)\s+(?:fill|capacity|efficiency)',
            ],
            'time': [
                r'(response|reaction|clearing|operating)\s+time',
                r'(delay|duration|period)',
            ]
        }
        
        patterns = subject_patterns.get(param_type, [])
        
        for pattern in patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                # Return the matched subject
                return match.group(0).strip().lower()
        
        # Fallback: look for technical keywords in context
        tech_words = [
            'cable', 'conductor', 'wire', 'core', 'duct', 'conduit', 'trunking',
            'breaker', 'fuse', 'mcb', 'rcd', 'rcbo', 'panel', 'board',
            'socket', 'outlet', 'lighting', 'motor', 'transformer',
            'trench', 'depth', 'height', 'spacing', 'clearance',
            'maximum', 'minimum', 'rated', 'nominal', 'operating'
        ]
        
        context_words = re.findall(r'\b([a-z]{4,})\b', context.lower())
        for word in context_words:
            if word in tech_words:
                return f"{word} {param_type.replace('_', ' ')}"
        
        return param_type  # Default to just the type
    
    def _find_matching_content(
        self,
        topic: str,
        source_chunks: List[Dict]
    ) -> Optional[Dict]:
        """Find content in source that matches the topic"""
        topic_lower = topic.lower()
        topic_words = set(topic_lower.split())
        
        best_match = None
        best_score = 0
        
        for chunk in source_chunks:
            text_lower = chunk['text'].lower()
            
            # Calculate word overlap
            text_words = set(text_lower.split())
            overlap = len(topic_words & text_words)
            
            if overlap > best_score:
                best_score = overlap
                best_match = chunk
        
        # Require at least 2 word overlap
        return best_match if best_score >= 2 else None
    
    def _detect_value_conflict(
        self,
        source_chunk: Dict,
        ref_chunk: Dict,
        requirement: Dict,
        ref_doc: str,
        priority_types: set = None
    ) -> Optional[ComplianceIssue]:
        """Detect if there's a value conflict between source and reference"""
        
        source_values = self._extract_all_values(source_chunk['text'])
        ref_values = requirement.get('values', [])
        
        if not ref_values:
            return None
        
        # Filter by priority types if specified
        if priority_types:
            source_values = [v for v in source_values if v['type'] in priority_types]
            ref_values = [v for v in ref_values if v['type'] in priority_types]
        
        if not ref_values:
            return None
        
        for ref_val in ref_values:
            # Find matching type in source
            source_match = None
            for src_val in source_values:
                if src_val['type'] == ref_val['type']:
                    source_match = src_val
                    break
            
            if source_match and source_match['value'] != ref_val['value']:
                # Determine severity based on difference
                diff_pct = abs(source_match['value'] - ref_val['value']) / ref_val['value'] * 100
                
                if diff_pct > 50:
                    severity = IssueSeverity.CRITICAL
                elif diff_pct > 20:
                    severity = IssueSeverity.HIGH
                elif diff_pct > 10:
                    severity = IssueSeverity.MEDIUM
                else:
                    severity = IssueSeverity.LOW
                
                # Get meaningful subject description
                src_subject = source_match.get('subject', ref_val['type'])
                ref_subject = ref_val.get('subject', ref_val['type'])
                subject_desc = src_subject if src_subject != ref_val['type'] else ref_subject
                param_name = ref_val['type'].replace('_', ' ').title()
                
                return ComplianceIssue(
                    severity=severity,
                    category=IssueCategory.VALUE_MISMATCH,
                    topic=f"{param_name} - {subject_desc}",
                    description=f"{param_name} ({subject_desc}): "
                               f"Your spec has {source_match['value']}, "
                               f"but {ref_doc} requires {ref_val['value']}",
                    source_doc=source_chunk['metadata'].get('file_name', ''),
                    source_section=source_chunk.get('section_number', ''),
                    source_text=source_chunk['text'][:300],
                    source_page=source_chunk.get('page', 'N/A'),
                    source_value=str(source_match['value']),
                    reference_doc=ref_doc,
                    reference_section=ref_chunk.get('section_number', ''),
                    reference_text=ref_chunk['text'][:300],
                    reference_page=ref_chunk.get('page', 'N/A'),
                    reference_value=str(ref_val['value']),
                    recommendation=f"Review and align {subject_desc} value with {ref_doc} requirements"
                )
        
        return None
    
    def _analyze_gaps(
        self,
        source_chunks: List[Dict],
        reference_chunks: Dict[str, List[Dict]],
        focus_area: Optional[str]
    ) -> List[GapItem]:
        """
        Find requirements in reference docs that are missing from source
        
        Strategy:
        1. Extract all mandatory requirements from references
        2. Check if each requirement topic exists in source
        3. Report missing ones
        """
        gaps = []
        
        # Build source topic index
        source_topics = set()
        source_standards = set()
        
        for chunk in source_chunks:
            # Extract key topics
            text_lower = chunk['text'].lower()
            
            # Add section titles as topics
            if chunk.get('section_title'):
                source_topics.add(chunk['section_title'].lower())
            
            # Add referenced standards
            standards = chunk.get('referenced_standards', [])
            source_standards.update(s.upper() for s in standards)
            
            # Extract key terms
            key_terms = re.findall(r'\b[A-Za-z]{4,}\b', text_lower)
            source_topics.update(key_terms)
        
        logger.info(f"📋 Source has {len(source_topics)} topics, {len(source_standards)} standards")
        
        for ref_doc, ref_chunks in reference_chunks.items():
            mandatory_chunks = [c for c in ref_chunks if c.get('has_mandatory')]
            
            for ref_chunk in mandatory_chunks:
                ref_text = ref_chunk['text']
                
                # Check if this topic exists in source
                topic_found = self._topic_exists_in_source(ref_text, source_topics)
                
                if not topic_found:
                    # Extract what the requirement is about
                    topic = self._extract_topic(ref_chunk)
                    
                    gap = GapItem(
                        severity=IssueSeverity.HIGH if 'shall' in ref_text.lower() else IssueSeverity.MEDIUM,
                        topic=topic,
                        description=f"Requirement from {ref_doc} may not be addressed in your spec",
                        missing_requirement=ref_text[:400],
                        reference_doc=ref_doc,
                        reference_section=ref_chunk.get('section_number', ''),
                        reference_text=ref_text[:300],
                        reference_page=ref_chunk.get('page', 'N/A'),
                        impact="Potential non-compliance with requirements",
                        recommendation=f"Review {ref_doc} Section {ref_chunk.get('section_number', 'N/A')} "
                                      f"and ensure your spec addresses this requirement",
                        mandatory='shall' in ref_text.lower() or 'must' in ref_text.lower()
                    )
                    gaps.append(gap)
        
        # Deduplicate gaps by topic
        unique_gaps = {}
        for gap in gaps:
            key = gap.topic.lower()[:50]
            if key not in unique_gaps:
                unique_gaps[key] = gap
        
        return list(unique_gaps.values())
    
    def _topic_exists_in_source(self, ref_text: str, source_topics: Set[str]) -> bool:
        """Check if the reference topic exists in source"""
        ref_lower = ref_text.lower()
        
        # Extract key terms from reference
        ref_terms = set(re.findall(r'\b[a-z]{4,}\b', ref_lower))
        
        # Check overlap
        overlap = ref_terms & source_topics
        
        # Require at least 3 matching terms
        return len(overlap) >= 3
    
    def _extract_topic(self, chunk: Dict) -> str:
        """Extract topic name from chunk"""
        if chunk.get('section_title'):
            return chunk['section_title']
        
        text = chunk['text'][:100]
        # Find first capitalized phrase
        match = re.search(r'[A-Z][a-z]+(?:\s+[A-Za-z]+){0,3}', text)
        return match.group(0) if match else text[:50]
    
    def _compare_values(
        self,
        source_chunks: List[Dict],
        reference_chunks: Dict[str, List[Dict]],
        focus_area: Optional[str]
    ) -> List[ValueComparison]:
        """
        Compare numerical values between source and references
        Only compare values that appear in semantically similar contexts
        """
        comparisons = []
        seen_comparisons = set()  # Avoid duplicates
        
        # Technical keywords that indicate specific contexts - must match for comparison
        context_keywords = {
            'cable', 'conductor', 'wire', 'core', 'armour', 'sheath', 'insulation',
            'duct', 'conduit', 'trunking', 'tray', 'ladder', 'basket',
            'socket', 'outlet', 'switch', 'breaker', 'fuse', 'mcb', 'rcbo', 'rcd',
            'panel', 'board', 'switchgear', 'distribution', 'mcc',
            'transformer', 'motor', 'generator', 'ups', 'inverter',
            'lighting', 'luminaire', 'lamp', 'lux', 'emergency',
            'earthing', 'grounding', 'bonding', 'lightning', 'protection',
            'trench', 'excavation', 'backfill', 'sand', 'bedding',
            'voltage', 'current', 'power', 'factor', 'frequency',
            'temperature', 'ambient', 'rating', 'derating',
            'size', 'cross-section', 'diameter', 'thickness', 'depth', 'width'
        }
        
        # Get priority parameter types based on focus area
        priority_types = self._get_priority_types(focus_area)
        
        # For each reference chunk with values, find similar source chunk
        for ref_doc, ref_chunks in reference_chunks.items():
            for ref_chunk in ref_chunks:
                ref_values = self._extract_all_values(ref_chunk['text'])
                
                if not ref_values:
                    continue
                
                # If we have priority types, filter to only those
                if priority_types:
                    ref_values = [v for v in ref_values if v['type'] in priority_types]
                    if not ref_values:
                        continue
                
                # Find best matching source chunk based on content similarity
                ref_section = ref_chunk.get('section_title', '') or ref_chunk.get('section_number', '')
                ref_text = ref_chunk['text'].lower()
                
                # Extract technical context keywords from reference
                ref_context = set()
                ref_words = set(ref_text.split())
                for word in ref_words:
                    # Clean word of punctuation
                    clean_word = re.sub(r'[^a-z]', '', word)
                    if clean_word in context_keywords:
                        ref_context.add(clean_word)
                
                # Skip if no technical context found
                if not ref_context:
                    continue
                
                # Find matching source chunks with SAME technical context
                matching_sources = []
                for src_chunk in source_chunks:
                    src_text = src_chunk['text'].lower()
                    src_words = set(src_text.split())
                    
                    # Extract source technical context
                    src_context = set()
                    for word in src_words:
                        clean_word = re.sub(r'[^a-z]', '', word)
                        if clean_word in context_keywords:
                            src_context.add(clean_word)
                    
                    # Must have at least 2 matching technical keywords
                    context_overlap = len(ref_context & src_context)
                    if context_overlap >= 2:
                        # Also check general word overlap
                        word_overlap = len(ref_words & src_words)
                        if word_overlap >= 5:  # At least 5 common words
                            matching_sources.append({
                                'chunk': src_chunk,
                                'context_overlap': context_overlap,
                                'word_overlap': word_overlap,
                                'common_context': ref_context & src_context
                            })
                
                # Sort by context overlap first, then word overlap
                matching_sources.sort(key=lambda x: (x['context_overlap'], x['word_overlap']), reverse=True)
                
                # Compare values only with matching chunks (top 2 only)
                for match in matching_sources[:2]:
                    src_chunk = match['chunk']
                    src_values = self._extract_all_values(src_chunk['text'])
                    
                    # If we have priority types, filter source values too
                    if priority_types:
                        src_values = [v for v in src_values if v['type'] in priority_types]
                    
                    for ref_val in ref_values:
                        param_type = ref_val['type']
                        ref_subject = ref_val.get('subject', param_type)
                    if context_overlap >= 2:
                        # Also check general word overlap
                        word_overlap = len(ref_words & src_words)
                        if word_overlap >= 5:  # At least 5 common words
                            matching_sources.append({
                                'chunk': src_chunk,
                                'context_overlap': context_overlap,
                                'word_overlap': word_overlap,
                                'common_context': ref_context & src_context
                            })
                
                # Sort by context overlap first, then word overlap
                matching_sources.sort(key=lambda x: (x['context_overlap'], x['word_overlap']), reverse=True)
                
                # Compare values only with matching chunks (top 2 only)
                for match in matching_sources[:2]:
                    src_chunk = match['chunk']
                    src_values = self._extract_all_values(src_chunk['text'])
                    
                    for ref_val in ref_values:
                        param_type = ref_val['type']
                        ref_subject = ref_val.get('subject', param_type)
                        
                        # Find same parameter type in source WITH similar subject
                        for src_val_entry in src_values:
                            if src_val_entry['type'] != param_type:
                                continue
                            
                            src_subject = src_val_entry.get('subject', param_type)
                            
                            # Check if subjects are related
                            if not self._subjects_match(src_subject, ref_subject):
                                continue
                            
                            src_val = src_val_entry['value']
                            ref_v = ref_val['value']
                            
                            # Create unique key to avoid duplicates
                            comp_key = (param_type, src_val, ref_v, src_subject)
                            if comp_key in seen_comparisons:
                                continue
                            seen_comparisons.add(comp_key)
                            
                            if src_val != ref_v:
                                diff = src_val - ref_v
                                pct_diff = (diff / ref_v * 100) if ref_v != 0 else 0
                                
                                if src_val > ref_v:
                                    status = "HIGHER"
                                else:
                                    status = "LOWER"
                                
                                # Determine severity
                                if abs(pct_diff) > 50:
                                    severity = IssueSeverity.CRITICAL
                                elif abs(pct_diff) > 20:
                                    severity = IssueSeverity.HIGH
                                elif abs(pct_diff) > 10:
                                    severity = IssueSeverity.MEDIUM
                                else:
                                    severity = IssueSeverity.LOW
                                
                                # Create meaningful description
                                subject_desc = src_subject if src_subject != param_type else ref_subject
                                
                                comparison = ValueComparison(
                                    parameter=f"{param_type.replace('_', ' ').title()} ({subject_desc})",
                                    unit=self._get_unit(param_type),
                                    source_doc=src_chunk['metadata'].get('file_name', ''),
                                    source_value=src_val,
                                    source_section=src_chunk.get('section_number', '') or src_chunk.get('section_title', ''),
                                    reference_doc=ref_doc,
                                    reference_value=ref_v,
                                    reference_section=ref_chunk.get('section_number', '') or ref_chunk.get('section_title', ''),
                                    difference=diff,
                                    percentage_diff=pct_diff,
                                    status=status,
                                    severity=severity,
                                    note=f"{subject_desc}: Your spec {src_val}{self._get_unit(param_type)}, {ref_doc} requires {ref_v}{self._get_unit(param_type)}"
                                )
                                comparisons.append(comparison)
        
        return comparisons
    
    def _subjects_match(self, subject1: str, subject2: str) -> bool:
        """Check if two value subjects are related (describing the same thing)"""
        s1 = subject1.lower()
        s2 = subject2.lower()
        
        # Direct match
        if s1 == s2:
            return True
        
        # One contains the other
        if s1 in s2 or s2 in s1:
            return True
        
        # Related terms groups
        related_groups = [
            {'cable', 'conductor', 'wire', 'core'},
            {'duct', 'conduit', 'pipe', 'trunking'},
            {'trench', 'excavation', 'depth', 'backfill'},
            {'breaker', 'mcb', 'fuse', 'rcbo', 'rcd', 'protection'},
            {'socket', 'outlet', 'receptacle'},
            {'panel', 'board', 'switchgear', 'distribution'},
            {'maximum', 'max', 'minimum', 'min'},
            {'length', 'distance', 'run'},
            {'size', 'cross-section', 'area', 'csa'},
        ]
        
        # Extract key words
        words1 = set(re.findall(r'\b\w{3,}\b', s1))
        words2 = set(re.findall(r'\b\w{3,}\b', s2))
        
        # Check if they share a key concept word
        common = words1 & words2
        if common:
            return True
        
        # Check related groups
        for group in related_groups:
            if (words1 & group) and (words2 & group):
                return True
        
        return False
        
        return comparisons
    
    def _get_unit(self, param_type: str) -> str:
        """Get unit for parameter type"""
        units = {
            'temperature': '°C',
            'voltage': 'V',
            'current': 'A',
            'power': 'W',
            'resistance': 'Ω',
            'impedance': 'Ω',
            'cable_size': 'mm²',
            'length': 'm',
            'percentage': '%',
            'time': 's',
            'frequency': 'Hz'
        }
        return units.get(param_type, '')
    
    def _check_standard_coverage(
        self,
        source_chunks: List[Dict],
        reference_chunks: Dict[str, List[Dict]],
        report: ComplianceReport
    ):
        """Check which standards are referenced and which are missing"""
        
        # Standards in source
        source_standards = set()
        for chunk in source_chunks:
            standards = chunk.get('referenced_standards', [])
            source_standards.update(s.upper() for s in standards)
            
            # Also extract from text
            text_standards = re.findall(self.standard_pattern, chunk['text'])
            source_standards.update(s.upper() for s in text_standards)
        
        # Standards in references
        ref_standards = set()
        for ref_doc, chunks in reference_chunks.items():
            for chunk in chunks:
                standards = chunk.get('referenced_standards', [])
                ref_standards.update(s.upper() for s in standards)
        
        report.standards_referenced = list(source_standards)
        report.standards_missing = list(ref_standards - source_standards)
        
        # Add gaps for missing critical standards
        for std in report.standards_missing:
            if any(prefix in std for prefix in ['BS', 'EN', 'IEC', 'IS']):
                gap = GapItem(
                    severity=IssueSeverity.MEDIUM,
                    topic=f"Standard Reference: {std}",
                    description=f"Standard {std} is referenced in requirements but not in your spec",
                    missing_requirement=f"Reference to {std}",
                    reference_doc="Multiple",
                    reference_section="Various",
                    reference_text=f"Standard {std} appears in reference documents",
                    reference_page="N/A",
                    impact="May indicate incomplete coverage of requirements",
                    recommendation=f"Review if {std} is applicable to your specification",
                    mandatory=False
                )
                report.gaps.append(gap)
    
    def _calculate_summary(self, report: ComplianceReport):
        """Calculate summary statistics and remove duplicates"""
        
        # Remove duplicate compliance issues (same description)
        seen_descriptions = set()
        unique_issues = []
        for issue in report.compliance_issues:
            # Create a key from the core description (first 100 chars)
            key = issue.description[:100].lower().strip()
            if key not in seen_descriptions:
                seen_descriptions.add(key)
                unique_issues.append(issue)
        report.compliance_issues = unique_issues
        
        # Remove duplicate gaps (same topic)
        seen_gaps = set()
        unique_gaps = []
        for gap in report.gaps:
            key = gap.topic.lower().strip()
            if key not in seen_gaps:
                seen_gaps.add(key)
                unique_gaps.append(gap)
        report.gaps = unique_gaps
        
        # Remove duplicate value comparisons
        seen_values = set()
        unique_values = []
        for vc in report.value_comparisons:
            key = (vc.parameter, vc.source_value, vc.reference_value)
            if key not in seen_values:
                seen_values.add(key)
                unique_values.append(vc)
        report.value_comparisons = unique_values
        
        # Count by severity
        all_issues = report.compliance_issues + report.gaps
        
        report.critical_count = sum(1 for i in all_issues if i.severity == IssueSeverity.CRITICAL)
        report.high_count = sum(1 for i in all_issues if i.severity == IssueSeverity.HIGH)
        report.medium_count = sum(1 for i in all_issues if i.severity == IssueSeverity.MEDIUM)
        report.low_count = sum(1 for i in all_issues if i.severity == IssueSeverity.LOW)
        
        # Calculate compliance score (simple heuristic)
        total_checks = len(all_issues) + 10  # Base checks
        penalty = (report.critical_count * 20 + 
                   report.high_count * 10 + 
                   report.medium_count * 5 + 
                   report.low_count * 1)
        
        report.compliance_score = max(0, min(100, 100 - penalty))
        
        # Generate summary text
        summary_parts = [
            f"📊 Compliance Analysis Complete",
            f"",
            f"📄 Source: {report.source_document}",
            f"📚 References: {', '.join(report.reference_documents)}",
            f"🎯 Focus: {report.focus_area or 'All areas'}",
            f"",
            f"📈 Compliance Score: {report.compliance_score:.0f}%",
            f"",
            f"🔴 Critical Issues: {report.critical_count}",
            f"🟠 High Priority: {report.high_count}",
            f"🟡 Medium Priority: {report.medium_count}",
            f"🟢 Low Priority: {report.low_count}",
            f"",
            f"📋 Total Issues: {len(report.compliance_issues)}",
            f"❓ Gaps Found: {len(report.gaps)}",
            f"📐 Value Comparisons: {len(report.value_comparisons)}",
        ]
        
        if report.standards_missing:
            summary_parts.append(f"")
            summary_parts.append(f"⚠️ Standards not referenced: {len(report.standards_missing)}")
        
        report.summary = "\n".join(summary_parts)


# Export for use
__all__ = [
    'CrossReferenceEngineV2',
    'AnalysisMode',
    'IssueSeverity',
    'IssueCategory',
    'ComplianceReport',
    'ComplianceIssue',
    'GapItem',
    'ValueComparison'
]
