"""
Query Analyzer

Analyzes user queries to determine optimal retrieval strategy.
Detects numbers, units, tables, definitions, and query intent.
"""

import re
from typing import Dict, List, Optional, Tuple
from enum import Enum
from loguru import logger


class QueryIntent(Enum):
    """Query intent types"""
    TABLE_LOOKUP = "table_lookup"  # Numerical/tabular data
    DEFINITION = "definition"  # "what is", "nedir", definitions
    REFERENCE = "reference"  # Specific standard/code reference
    CALCULATION = "calculation"  # "how to calculate", formulas
    GENERAL = "general"  # General information


class QueryAnalyzer:
    """
    Analyzes queries to determine retrieval strategy
    """
    
    # Number patterns
    NUMBER_PATTERN = r'\d+(?:[.,]\d+)?'
    
    # Engineering units (English and Turkish)
    UNITS = {
        'mm²': 'area',
        'mm2': 'area',
        'mm': 'length',
        'm': 'length',
        'cm': 'length',
        'A': 'current',
        'amp': 'current',
        'amper': 'current',
        'V': 'voltage',
        'volt': 'voltage',
        'W': 'power',
        'watt': 'power',
        'kW': 'power',
        'kVA': 'apparent_power',
        'Ω': 'resistance',
        'ohm': 'resistance',
        '°C': 'temperature',
        'celsius': 'temperature',
        'Hz': 'frequency',
        'hertz': 'frequency',
        '%': 'percentage',
        'yüzde': 'percentage'
    }
    
    # Definition keywords (English and Turkish)
    DEFINITION_KEYWORDS = [
        'what is', 'what are', 'nedir', 'ne demek', 'tanım',
        'define', 'definition', 'meaning', 'anlamı'
    ]
    
    # Table keywords
    TABLE_KEYWORDS = [
        'tablo', 'table', 'değer', 'value', 'kapasite', 'capacity',
        'akım', 'current', 'faktör', 'factor', 'düzeltme', 'correction',
        'seçim', 'selection', 'boyut', 'size', 'kesit', 'cross-section'
    ]
    
    # Calculation keywords
    CALCULATION_KEYWORDS = [
        'calculate', 'hesapla', 'how to', 'nasıl', 'formül', 'formula',
        'compute', 'determine', 'belirle'
    ]
    
    # Reference patterns
    REFERENCE_PATTERN = r'(?:IS|IEC|EN|BS|NFPA|NEC)\s*\d+'
    
    # Turkish character indicators
    TURKISH_CHARS = set('çğıöşüÇĞİÖŞÜ')
    TURKISH_WORDS = ['nedir', 'nasıl', 'için', 'olan', 'gibi', 'hangi', 'kaç', 
                     'değer', 'gerekli', 'gereksinim', 'standart', 'tablo']
    
    def __init__(self):
        """Initialize query analyzer"""
        logger.info("✅ Query Analyzer initialized")
    
    def detect_language(self, query: str) -> str:
        """
        Detect the language of the query
        
        Args:
            query: User query string
            
        Returns:
            Language code: 'tr' for Turkish, 'en' for English
        """
        # Check for Turkish characters
        if any(c in self.TURKISH_CHARS for c in query):
            return 'tr'
        
        # Check for Turkish words
        query_lower = query.lower()
        turkish_word_count = sum(1 for word in self.TURKISH_WORDS if word in query_lower)
        
        if turkish_word_count >= 2:
            return 'tr'
        
        # Default to English
        return 'en'
    
    def analyze(self, query: str) -> Dict:
        """
        Analyze query and return analysis results
        
        Args:
            query: User query string
            
        Returns:
            Dict with analysis results:
            {
                'intent': QueryIntent,
                'has_numbers': bool,
                'numbers': List[float],
                'has_units': bool,
                'units': List[str],
                'has_reference': bool,
                'references': List[str],
                'keywords': List[str],
                'weights': Dict[str, float],  # Retrieval method weights
                'language': str  # Detected language code
            }
        """
        query_lower = query.lower()
        
        # Detect language
        language = self.detect_language(query)
        
        # Detect numbers
        numbers = self._extract_numbers(query)
        has_numbers = len(numbers) > 0
        
        # Detect units
        units = self._extract_units(query)
        has_units = len(units) > 0
        
        # Detect references (IS3218, IEC 60364, etc.)
        references = self._extract_references(query)
        has_reference = len(references) > 0
        
        # Detect intent
        intent = self._determine_intent(query_lower, has_numbers, has_units, has_reference)
        
        # Extract keywords
        keywords = self._extract_keywords(query_lower)
        
        # Determine retrieval weights based on intent
        weights = self._calculate_weights(intent, has_numbers, has_units)
        
        analysis = {
            'intent': intent,
            'has_numbers': has_numbers,
            'numbers': numbers,
            'has_units': has_units,
            'units': units,
            'has_reference': has_reference,
            'references': references,
            'keywords': keywords,
            'weights': weights,
            'language': language
        }
        
        logger.info(
            f"📊 Query Analysis: Intent={intent.value}, Language={language}, "
            f"Numbers={len(numbers)}, Units={len(units)}, "
            f"Weights={weights}"
        )
        
        return analysis
    
    def _extract_numbers(self, query: str) -> List[float]:
        """Extract numbers from query"""
        matches = re.findall(self.NUMBER_PATTERN, query)
        numbers = []
        for match in matches:
            try:
                # Replace comma with dot for Turkish numbers
                num_str = match.replace(',', '.')
                numbers.append(float(num_str))
            except ValueError:
                pass
        return numbers
    
    def _extract_units(self, query: str) -> List[str]:
        """Extract engineering units from query"""
        found_units = []
        query_lower = query.lower()
        
        for unit, unit_type in self.UNITS.items():
            if unit.lower() in query_lower or unit in query:
                found_units.append(unit)
        
        return list(set(found_units))
    
    def _extract_references(self, query: str) -> List[str]:
        """Extract standard references (IS3218, IEC 60364, etc.)"""
        matches = re.findall(self.REFERENCE_PATTERN, query, re.IGNORECASE)
        return matches
    
    def _determine_intent(
        self, 
        query_lower: str, 
        has_numbers: bool, 
        has_units: bool,
        has_reference: bool
    ) -> QueryIntent:
        """Determine primary query intent"""
        
        # Check for definition query
        for keyword in self.DEFINITION_KEYWORDS:
            if keyword in query_lower:
                return QueryIntent.DEFINITION
        
        # Check for calculation query
        for keyword in self.CALCULATION_KEYWORDS:
            if keyword in query_lower:
                return QueryIntent.CALCULATION
        
        # Check for reference query
        if has_reference:
            return QueryIntent.REFERENCE
        
        # Check for table lookup (has numbers + units + table keywords)
        if has_numbers and has_units:
            for keyword in self.TABLE_KEYWORDS:
                if keyword in query_lower:
                    return QueryIntent.TABLE_LOOKUP
        
        # Check for table lookup (table keywords even without numbers)
        table_keyword_count = sum(1 for kw in self.TABLE_KEYWORDS if kw in query_lower)
        if table_keyword_count >= 2:
            return QueryIntent.TABLE_LOOKUP
        
        return QueryIntent.GENERAL
    
    def _extract_keywords(self, query_lower: str) -> List[str]:
        """Extract important keywords from query"""
        # Simple keyword extraction (can be improved with NLP)
        words = query_lower.split()
        
        # Filter out common stop words
        stop_words = {'bir', 'ne', 'mi', 'mu', 'mü', 'the', 'a', 'an', 'is', 'are', 'nedir'}
        keywords = [w for w in words if len(w) > 2 and w not in stop_words]
        
        return keywords
    
    def _calculate_weights(
        self, 
        intent: QueryIntent, 
        has_numbers: bool, 
        has_units: bool
    ) -> Dict[str, float]:
        """
        Calculate retrieval method weights based on query analysis
        
        Returns:
            Dict with weights: {'semantic': float, 'keyword': float, 'table': float}
        """
        
        if intent == QueryIntent.TABLE_LOOKUP:
            # Prioritize table and keyword search for numerical queries
            return {
                'semantic': 0.3,
                'keyword': 0.35,
                'table': 0.35
            }
        
        elif intent == QueryIntent.DEFINITION:
            # Semantic search is best for definitions
            return {
                'semantic': 0.6,
                'keyword': 0.3,
                'table': 0.1
            }
        
        elif intent == QueryIntent.REFERENCE:
            # Keyword exact match is important for references
            return {
                'semantic': 0.3,
                'keyword': 0.6,
                'table': 0.1
            }
        
        elif intent == QueryIntent.CALCULATION:
            # Balance between semantic and keyword
            return {
                'semantic': 0.45,
                'keyword': 0.35,
                'table': 0.2
            }
        
        else:  # GENERAL
            # Default balanced weights
            return {
                'semantic': 0.5,
                'keyword': 0.3,
                'table': 0.2
            }


# Singleton instance
_query_analyzer = None

def get_query_analyzer() -> QueryAnalyzer:
    """Get singleton query analyzer instance"""
    global _query_analyzer
    if _query_analyzer is None:
        _query_analyzer = QueryAnalyzer()
    return _query_analyzer
