"""
Response Validator - Ensures response quality and prevents hallucination

Features:
1. Source citation validation - Every bullet must have source
2. Confidence threshold - Low confidence = "Not found"
3. Hallucination detection - Compare response with source content
"""

import re
from typing import List, Dict, Tuple, Optional
from loguru import logger
from difflib import SequenceMatcher


class ResponseValidator:
    """Validates LLM responses for quality and hallucination prevention"""
    
    def __init__(self, 
                 min_confidence: float = 0.35,
                 min_citation_coverage: float = 0.6,
                 max_hallucination_score: float = 0.4):
        """
        Args:
            min_confidence: Minimum retrieval confidence to generate response
            min_citation_coverage: Minimum % of bullets that must have citations
            max_hallucination_score: Maximum allowed hallucination score (0-1)
        """
        self.min_confidence = min_confidence
        self.min_citation_coverage = min_citation_coverage
        self.max_hallucination_score = max_hallucination_score
        
        # Citation patterns - matches (Source, 1.2.3) or [Source] or (Source)
        self.citation_patterns = [
            r'\([A-Z][A-Za-z0-9\s]+,\s*[\d.]+\)',  # (IS 3218, 6.5.1.13)
            r'\([A-Z][A-Za-z0-9\s]+\)',             # (IS 3218)
            r'\[[A-Z][A-Za-z0-9\s]+\]',             # [IS 3218]
        ]
    
    def validate_confidence(self, nodes: List, min_score: float = None) -> Tuple[bool, float, str]:
        """
        Check if retrieval confidence is sufficient
        
        Args:
            nodes: Retrieved nodes with scores
            min_score: Override minimum score threshold
            
        Returns:
            (is_valid, avg_confidence, reason)
        """
        if min_score is None:
            min_score = self.min_confidence
        
        if not nodes:
            return False, 0.0, "No relevant documents found"
        
        # Calculate average confidence from top nodes
        scores = [getattr(node, 'score', 0.5) for node in nodes[:5]]  # Top 5 nodes
        avg_score = sum(scores) / len(scores) if scores else 0.0
        
        if avg_score < min_score:
            logger.warning(f"⚠️ Low confidence: {avg_score:.3f} < {min_score:.3f}")
            return False, avg_score, f"Low confidence ({avg_score:.2%}). Information may be unreliable."
        
        logger.info(f"✅ Confidence OK: {avg_score:.3f}")
        return True, avg_score, "OK"
    
    def validate_citations(self, response: str) -> Tuple[bool, float, Dict]:
        """
        Check if response has proper source citations
        
        Args:
            response: LLM generated response
            
        Returns:
            (is_valid, coverage_ratio, details)
        """
        # Extract all bullet points
        bullets = self._extract_bullets(response)
        
        if not bullets:
            # No bullets = likely paragraph response, less strict
            has_any_citation = any(
                re.search(pattern, response) 
                for pattern in self.citation_patterns
            )
            return has_any_citation, 1.0 if has_any_citation else 0.0, {
                'total_bullets': 0,
                'cited_bullets': 0,
                'paragraph_mode': True,
                'has_citation': has_any_citation
            }
        
        # Check each bullet for citations
        cited_count = 0
        uncited_bullets = []
        
        for bullet in bullets:
            has_citation = any(
                re.search(pattern, bullet) 
                for pattern in self.citation_patterns
            )
            if has_citation:
                cited_count += 1
            else:
                uncited_bullets.append(bullet[:80] + "..." if len(bullet) > 80 else bullet)
        
        coverage = cited_count / len(bullets) if bullets else 0.0
        is_valid = coverage >= self.min_citation_coverage
        
        details = {
            'total_bullets': len(bullets),
            'cited_bullets': cited_count,
            'coverage': coverage,
            'uncited_bullets': uncited_bullets[:3]  # Show first 3
        }
        
        if not is_valid:
            logger.warning(f"⚠️ Low citation coverage: {coverage:.1%} < {self.min_citation_coverage:.1%}")
            logger.warning(f"   Uncited bullets: {len(uncited_bullets)}")
        else:
            logger.info(f"✅ Citation coverage OK: {coverage:.1%}")
        
        return is_valid, coverage, details
    
    def detect_hallucination(self, response: str, source_nodes: List) -> Tuple[float, Dict]:
        """
        Detect potential hallucination by comparing response with source content
        
        Args:
            response: LLM generated response
            source_nodes: Retrieved source documents
            
        Returns:
            (hallucination_score, details)
            hallucination_score: 0.0 = no hallucination, 1.0 = complete hallucination
        """
        if not source_nodes:
            return 1.0, {'reason': 'No source nodes to verify against'}
        
        # Extract all text from sources
        source_text = " ".join([
            node.text for node in source_nodes 
            if hasattr(node, 'text')
        ]).lower()
        
        # Extract key claims from response (sentences with technical info)
        claims = self._extract_claims(response)
        
        if not claims:
            return 0.0, {'reason': 'No technical claims to verify'}
        
        # Check each claim against source text
        verified_claims = 0
        unverified_claims = []
        
        for claim in claims:
            # Calculate similarity with source text
            similarity = self._calculate_similarity(claim.lower(), source_text)
            
            if similarity > 0.3:  # Threshold for "found in source"
                verified_claims += 1
            else:
                unverified_claims.append({
                    'claim': claim[:100] + "..." if len(claim) > 100 else claim,
                    'similarity': similarity
                })
        
        hallucination_score = 1.0 - (verified_claims / len(claims)) if claims else 0.0
        
        details = {
            'total_claims': len(claims),
            'verified_claims': verified_claims,
            'hallucination_score': hallucination_score,
            'unverified_claims': unverified_claims[:3]  # Show first 3
        }
        
        if hallucination_score > self.max_hallucination_score:
            logger.warning(f"⚠️ High hallucination risk: {hallucination_score:.1%}")
            logger.warning(f"   Unverified claims: {len(unverified_claims)}/{len(claims)}")
        else:
            logger.info(f"✅ Hallucination check OK: {hallucination_score:.1%}")
        
        return hallucination_score, details
    
    def validate_response(self, response: str, source_nodes: List) -> Dict:
        """
        Comprehensive response validation
        
        Returns:
            {
                'is_valid': bool,
                'confidence': float,
                'citation_coverage': float,
                'hallucination_score': float,
                'warnings': List[str],
                'details': Dict
            }
        """
        warnings = []
        
        # 1. Check retrieval confidence
        conf_valid, confidence, conf_reason = self.validate_confidence(source_nodes)
        if not conf_valid:
            warnings.append(f"Low confidence: {conf_reason}")
        
        # 2. Check citations
        cite_valid, citation_coverage, cite_details = self.validate_citations(response)
        if not cite_valid:
            warnings.append(f"Missing citations: {citation_coverage:.0%} coverage")
        
        # 3. Check hallucination
        halluc_score, halluc_details = self.detect_hallucination(response, source_nodes)
        if halluc_score > self.max_hallucination_score:
            warnings.append(f"High hallucination risk: {halluc_score:.0%}")
        
        # Overall validity
        is_valid = conf_valid and cite_valid and (halluc_score <= self.max_hallucination_score)
        
        return {
            'is_valid': is_valid,
            'confidence': confidence,
            'citation_coverage': citation_coverage,
            'hallucination_score': halluc_score,
            'warnings': warnings,
            'details': {
                'confidence_check': {'valid': conf_valid, 'reason': conf_reason},
                'citation_check': cite_details,
                'hallucination_check': halluc_details
            }
        }
    
    def _extract_bullets(self, text: str) -> List[str]:
        """Extract bullet points from text"""
        bullets = []
        lines = text.split('\n')
        
        for line in lines:
            stripped = line.strip()
            # Match bullets: -, *, •, or numbered (1., 2., etc)
            if re.match(r'^[-*•]\s+', stripped) or re.match(r'^\d+\.\s+', stripped):
                bullets.append(stripped)
        
        return bullets
    
    def _extract_claims(self, text: str) -> List[str]:
        """Extract technical claims from response"""
        # Split by sentences
        sentences = re.split(r'[.!?]\s+', text)
        
        claims = []
        for sentence in sentences:
            # Skip very short sentences
            if len(sentence) < 20:
                continue
            
            # Keep sentences with technical indicators
            # Numbers, units, technical terms, specifications
            has_technical = any([
                re.search(r'\d+', sentence),  # Contains numbers
                re.search(r'(mm|cm|m²|°C|A|V|kW|Hz|IP\d+)', sentence),  # Units
                re.search(r'(maximum|minimum|required|shall|must|standard)', sentence, re.IGNORECASE)
            ])
            
            if has_technical:
                claims.append(sentence.strip())
        
        return claims
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity using SequenceMatcher"""
        # For long texts, sample to avoid performance issues
        max_len = 1000
        text1_sample = text1[:max_len]
        
        # Find best matching substring in text2
        matcher = SequenceMatcher(None, text1_sample, text2)
        return matcher.ratio()


# Singleton instance
_validator: Optional[ResponseValidator] = None


def get_response_validator(
    min_confidence: float = 0.5,
    min_citation_coverage: float = 0.7,
    max_hallucination_score: float = 0.3
) -> ResponseValidator:
    """Get or create ResponseValidator singleton"""
    global _validator
    if _validator is None:
        _validator = ResponseValidator(
            min_confidence=min_confidence,
            min_citation_coverage=min_citation_coverage,
            max_hallucination_score=max_hallucination_score
        )
        logger.info(f"✅ ResponseValidator initialized (conf≥{min_confidence}, cite≥{min_citation_coverage}, halluc≤{max_hallucination_score})")
    return _validator


if __name__ == "__main__":
    # Test the validator
    validator = get_response_validator()
    
    # Test case 1: Good response with citations
    good_response = """
    Isı dedektörü alan hesaplaması:
    
    - Isı dedektörleri için: Alan (m²) / 50 (IS 3218, 6.5.1.13)
    - Duman dedektörleri için: Alan (m²) / 100 (IS 3218, 6.5.1.14)
    - Karbonmonoksit dedektörleri için: Alan (m²) / 100 (NEK 606, 5.2.1)
    """
    
    # Test case 2: Bad response without citations
    bad_response = """
    Isı dedektörü alan hesaplaması:
    
    - Isı dedektörleri için yaklaşık 50 metrekare
    - Duman dedektörleri için 100 metrekare olmalı
    - Tavanda montaj yapılır
    """
    
    print("\n=== Test 1: Good Response ===")
    cite_valid, coverage, details = validator.validate_citations(good_response)
    print(f"Valid: {cite_valid}, Coverage: {coverage:.1%}")
    print(f"Details: {details}")
    
    print("\n=== Test 2: Bad Response ===")
    cite_valid, coverage, details = validator.validate_citations(bad_response)
    print(f"Valid: {cite_valid}, Coverage: {coverage:.1%}")
    print(f"Details: {details}")
