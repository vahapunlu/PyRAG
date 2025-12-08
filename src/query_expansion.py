"""
Query Expansion Module for MEP Engineering Domain

Expands user queries with domain-specific synonyms and related terms
to improve retrieval accuracy and recall.
"""

from typing import List, Dict, Set
from loguru import logger


class QueryExpander:
    """
    Expands queries with MEP-specific synonyms and related terms
    
    Features:
    - Multi-language support (English/Turkish)
    - Domain-specific terminology (electrical, mechanical, plumbing, fire)
    - Related concept mapping
    - Abbreviation expansion
    """
    
    # MEP Domain Synonyms and Related Terms
    MEP_EXPANSIONS = {
        # Electrical terms
        "cable": ["cable", "conductor", "wire", "wiring", "cabling", "kablo", "iletken"],
        "kablo": ["cable", "conductor", "wire", "wiring", "cabling", "kablo", "iletken"],
        "current": ["current", "ampere", "amp", "amperage", "akım"],
        "voltage": ["voltage", "potential", "volt", "gerilim"],
        "power": ["power", "wattage", "watt", "güç", "enerji"],
        "circuit": ["circuit", "loop", "branch", "devre"],
        "breaker": ["breaker", "MCB", "MCCB", "RCD", "RCBO", "circuit breaker", "sigorta"],
        "earthing": ["earthing", "grounding", "earth", "ground", "topraklama"],
        "grounding": ["grounding", "earthing", "earth", "ground", "topraklama"],
        "topraklama": ["earthing", "grounding", "earth", "ground", "topraklama"],
        
        # UPS and Emergency Power
        "ups": ["ups", "UPS", "uninterruptible power supply", "emergency power", "backup power", "kesintisiz güç kaynağı"],
        "generator": ["generator", "standby power", "backup generator", "emergency generator", "jeneratör"],
        "emergency": ["emergency", "backup", "standby", "acil", "yedek"],
        
        # Lighting
        "lighting": ["lighting", "illumination", "luminaire", "lamp", "fixture", "aydınlatma"],
        "luminaire": ["luminaire", "lighting fixture", "light fitting", "armatür"],
        "lux": ["lux", "illuminance", "light level", "aydınlatma seviyesi"],
        
        # Fire Safety
        "fire": ["fire", "fire safety", "fire protection", "yangın"],
        "fire alarm": ["fire alarm", "fire detection", "smoke detector", "heat detector", "yangın algılama"],
        "smoke": ["smoke", "smoke detector", "smoke alarm", "duman", "duman dedektörü"],
        "sprinkler": ["sprinkler", "fire sprinkler", "water spray", "sprinkler sistemi"],
        "firestopping": ["firestopping", "fire stopping", "fire barrier", "fire seal", "penetration seal", "yangın durdurma"],
        
        # HVAC
        "hvac": ["hvac", "HVAC", "heating", "ventilation", "air conditioning", "climate control", "mechanical", "iklimlendirme"],
        "ventilation": ["ventilation", "air movement", "fresh air", "exhaust", "havalandırma"],
        "duct": ["duct", "air duct", "ductwork", "kanal", "hava kanalı"],
        
        # Plumbing
        "plumbing": ["plumbing", "piping", "water supply", "drainage", "sanitary", "tesisat"],
        "pipe": ["pipe", "piping", "pipeline", "tube", "boru"],
        "drainage": ["drainage", "waste", "sanitary", "sewer", "drenaj", "atık su"],
        
        # Installation Methods
        "conduit": ["conduit", "cable tray", "trunking", "raceway", "kanal", "kablo kanalı"],
        "tray": ["tray", "cable tray", "ladder", "trough", "tabla"],
        "installation": ["installation", "mounting", "fixing", "placement", "kurulum", "montaj"],
        
        # Standards and Specifications
        "standard": ["standard", "specification", "requirement", "code", "regulation", "standart", "şartname"],
        "specification": ["specification", "spec", "requirement", "standard", "şartname"],
        "requirement": ["requirement", "specification", "standard", "condition", "şart", "gereksinim"],
        "compliance": ["compliance", "conformity", "accordance", "uygunluk"],
        
        # Sizing and Rating
        "capacity": ["capacity", "rating", "ampacity", "load", "kapasite"],
        "rating": ["rating", "capacity", "nominal", "rated", "değer"],
        "size": ["size", "sizing", "dimension", "cross-section", "boyut", "kesit"],
        "cross-section": ["cross-section", "cross section", "area", "mm²", "kesit alanı"],
        
        # Testing and Commissioning
        "testing": ["testing", "test", "commissioning", "verification", "inspection", "test etme", "deney"],
        "commissioning": ["commissioning", "testing", "verification", "acceptance", "devreye alma"],
        "inspection": ["inspection", "examination", "check", "review", "kontrol", "muayene"],
        
        # Protection and Safety
        "protection": ["protection", "safety", "safeguard", "protective", "koruma"],
        "safety": ["safety", "protection", "safe", "güvenlik", "emniyet"],
        "resistance": ["resistance", "impedance", "ohm", "resistivity", "direnç"],
        
        # Temperature and Environment
        "temperature": ["temperature", "thermal", "heat", "temp", "sıcaklık"],
        "ambient": ["ambient", "surrounding", "environment", "ortam", "çevre"],
        "correction": ["correction", "factor", "adjustment", "correction factor", "düzeltme", "katsayı"],
        
        # Common abbreviations
        "mcb": ["MCB", "miniature circuit breaker", "circuit breaker"],
        "mccb": ["MCCB", "molded case circuit breaker", "circuit breaker"],
        "rcd": ["RCD", "residual current device", "earth leakage"],
        "ip": ["IP", "ingress protection", "protection rating"],
        "iec": ["IEC", "International Electrotechnical Commission"],
        "bs": ["BS", "British Standard"],
        "en": ["EN", "European Norm", "European Standard"],
    }
    
    # Related concepts - these are added for semantic broadening
    RELATED_CONCEPTS = {
        "cable": ["insulation", "sheath", "conductor", "stranded", "solid"],
        "breaker": ["overcurrent", "short circuit", "overload", "tripping"],
        "earthing": ["bonding", "electrode", "resistance", "earth rod"],
        "fire alarm": ["detector", "call point", "panel", "zone", "sounder"],
        "lighting": ["lumen", "lux", "color temperature", "CRI", "efficacy"],
        "hvac": ["airflow", "temperature", "humidity", "pressure"],
    }
    
    def __init__(self, max_expansions: int = 3):
        """
        Initialize query expander
        
        Args:
            max_expansions: Maximum number of expansion terms to add
        """
        self.max_expansions = max_expansions
        logger.info(f"✅ Query Expander initialized (max {max_expansions} expansions)")
    
    def expand(self, query: str, include_related: bool = False) -> str:
        """
        Expand query with synonyms and related terms
        
        Args:
            query: Original user query
            include_related: Include related concepts (more aggressive expansion)
            
        Returns:
            Expanded query string
        """
        query_lower = query.lower()
        expansions_found = []
        
        # Find matching expansions
        for key, synonyms in self.MEP_EXPANSIONS.items():
            if key in query_lower:
                # Add synonyms that are not already in the query
                for synonym in synonyms:
                    if synonym.lower() not in query_lower and synonym not in expansions_found:
                        expansions_found.append(synonym)
                        if len(expansions_found) >= self.max_expansions:
                            break
                break  # Only expand first match to avoid noise
        
        # Add related concepts if requested
        if include_related and not expansions_found:
            for key, concepts in self.RELATED_CONCEPTS.items():
                if key in query_lower:
                    for concept in concepts[:2]:  # Max 2 related concepts
                        if concept.lower() not in query_lower:
                            expansions_found.append(concept)
                    break
        
        # Build expanded query
        if expansions_found:
            expansion_str = " ".join(expansions_found[:self.max_expansions])
            expanded = f"{query} ({expansion_str})"
            logger.debug(f"✨ Query expanded: '{query}' → '{expanded}'")
            return expanded
        
        return query
    
    def get_synonyms(self, term: str) -> List[str]:
        """
        Get all synonyms for a specific term
        
        Args:
            term: Term to look up
            
        Returns:
            List of synonyms
        """
        term_lower = term.lower()
        return self.MEP_EXPANSIONS.get(term_lower, [term])
    
    def add_custom_expansion(self, key: str, synonyms: List[str]):
        """
        Add custom expansion rule
        
        Args:
            key: Key term
            synonyms: List of synonyms
        """
        self.MEP_EXPANSIONS[key.lower()] = synonyms
        logger.info(f"✅ Added custom expansion: {key} → {synonyms}")


# Global expander instance
_expander_instance = None


def get_expander() -> QueryExpander:
    """Get global query expander instance (singleton)"""
    global _expander_instance
    if _expander_instance is None:
        _expander_instance = QueryExpander()
    return _expander_instance
