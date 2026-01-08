"""
Test Response Validator

Tests:
1. Citation validation
2. Confidence threshold
3. Hallucination detection
"""

from src.response_validator import get_response_validator
from loguru import logger


def test_citation_validation():
    """Test citation requirement enforcement"""
    print("\n" + "="*60)
    print("TEST 1: Citation Validation")
    print("="*60)
    
    validator = get_response_validator()
    
    # Good response - all bullets have citations
    good_response = """
## Isı Dedektörü Alan Hesaplaması

Yangın algılama sistemi için dedektör alan kapsama kuralları:

- Isı dedektörleri için: Alan (m²) / 50 (IS 3218, 6.5.1.13)
- Duman dedektörleri için: Alan (m²) / 100 (IS 3218, 6.5.1.14)
- Karbonmonoksit yangın dedektörleri için: Alan (m²) / 100 (IS 3218, 6.5.1.12)

### Önemli Notlar

- Tavan yüksekliği 10.5 m'yi aşarsa daha sık yerleştirme gerekir (IS 3218, 6.5.1)
- Duvara olan mesafe maksimum yarı dedektör aralığı kadar olmalıdır (NEK 606, 5.2.3)
    """
    
    # Bad response - no citations
    bad_response = """
## Isı Dedektörü Alan Hesaplaması

Yangın algılama sistemi için dedektör alan kapsama kuralları:

- Isı dedektörleri için yaklaşık 50 metrekare kullanılır
- Duman dedektörleri için 100 metrekare yeterlidir
- Karbonmonoksit dedektörleri de benzer şekilde yerleştirilir

### Önemli Notlar

- Tavan yüksekliği önemlıdir
- Duvara olan mesafeye dikkat edilmelidir
    """
    
    # Mixed response - some citations missing
    mixed_response = """
## Isı Dedektörü Alan Hesaplaması

- Isı dedektörleri için: Alan (m²) / 50 (IS 3218, 6.5.1.13)
- Duman dedektörleri için yaklaşık 100 m² kullanılır
- Karbonmonoksit yangın dedektörleri için: Alan (m²) / 100 (IS 3218, 6.5.1.12)
    """
    
    print("\n1️⃣ Good Response (all cited):")
    is_valid, coverage, details = validator.validate_citations(good_response)
    print(f"   ✅ Valid: {is_valid}")
    print(f"   📊 Coverage: {coverage:.0%}")
    print(f"   📝 Bullets: {details['cited_bullets']}/{details['total_bullets']}")
    
    print("\n2️⃣ Bad Response (no citations):")
    is_valid, coverage, details = validator.validate_citations(bad_response)
    print(f"   ❌ Valid: {is_valid}")
    print(f"   📊 Coverage: {coverage:.0%}")
    print(f"   📝 Bullets: {details['cited_bullets']}/{details['total_bullets']}")
    if details['uncited_bullets']:
        print(f"   ⚠️ Uncited: {details['uncited_bullets'][0][:60]}...")
    
    print("\n3️⃣ Mixed Response (partial citations):")
    is_valid, coverage, details = validator.validate_citations(mixed_response)
    print(f"   ⚠️ Valid: {is_valid}")
    print(f"   📊 Coverage: {coverage:.0%}")
    print(f"   📝 Bullets: {details['cited_bullets']}/{details['total_bullets']}")


def test_confidence_threshold():
    """Test low confidence detection"""
    print("\n" + "="*60)
    print("TEST 2: Confidence Threshold")
    print("="*60)
    
    validator = get_response_validator(min_confidence=0.5)
    
    # Mock nodes with different scores
    class MockNode:
        def __init__(self, score):
            self.score = score
    
    # High confidence nodes
    high_conf_nodes = [MockNode(0.85), MockNode(0.82), MockNode(0.78), MockNode(0.75)]
    
    # Low confidence nodes
    low_conf_nodes = [MockNode(0.35), MockNode(0.32), MockNode(0.28), MockNode(0.25)]
    
    # Medium confidence nodes (borderline)
    medium_conf_nodes = [MockNode(0.52), MockNode(0.48), MockNode(0.45), MockNode(0.42)]
    
    print("\n1️⃣ High Confidence (avg: 0.80):")
    is_valid, conf, reason = validator.validate_confidence(high_conf_nodes)
    print(f"   ✅ Valid: {is_valid}")
    print(f"   📊 Confidence: {conf:.1%}")
    print(f"   💬 Reason: {reason}")
    
    print("\n2️⃣ Low Confidence (avg: 0.30):")
    is_valid, conf, reason = validator.validate_confidence(low_conf_nodes)
    print(f"   ❌ Valid: {is_valid}")
    print(f"   📊 Confidence: {conf:.1%}")
    print(f"   💬 Reason: {reason}")
    
    print("\n3️⃣ Medium Confidence (avg: 0.47):")
    is_valid, conf, reason = validator.validate_confidence(medium_conf_nodes)
    print(f"   ⚠️ Valid: {is_valid}")
    print(f"   📊 Confidence: {conf:.1%}")
    print(f"   💬 Reason: {reason}")


def test_hallucination_detection():
    """Test hallucination detection"""
    print("\n" + "="*60)
    print("TEST 3: Hallucination Detection")
    print("="*60)
    
    validator = get_response_validator(max_hallucination_score=0.3)
    
    # Mock source nodes
    class MockNode:
        def __init__(self, text):
            self.text = text
            self.score = 0.8
    
    source_nodes = [
        MockNode("""
        Isı dedektörleri için maksimum alan kapsama 50 m² olarak belirtilmiştir.
        Tablo 6.1'de kablo akım kapasiteleri verilmiştir: 2.5mm² için 20A.
        Duman dedektörleri 100 m² alanı kapsayabilir.
        """),
        MockNode("""
        IS 3218 standardına göre dedektör yerleştirme kuralları:
        - Tavan yüksekliği 10.5m altında normal yerleştirme
        - Duvara olan mesafe maksimum yarı dedektör aralığı
        """)
    ]
    
    # Good response - matches source content
    good_response = """
    - Isı dedektörleri için maksimum alan: 50 m² (IS 3218, 6.5.1.13)
    - Kablo akım kapasitesi 2.5mm² için: 20A (IS 3218, Tablo 6.1)
    - Duman dedektörleri alan kapsama: 100 m² (IS 3218, 6.5.1.14)
    """
    
    # Bad response - contains information not in sources
    bad_response = """
    - Isı dedektörleri için yaklaşık 75 m² alan yeterlidir
    - Genelde 3 katlı binalarda 5 dedektör kullanılır
    - Asansör sayısı kat sayısına bölü 4'tür
    - Yangın söndürme tüpü her 20 metrede bir bulunmalıdır
    """
    
    print("\n1️⃣ Good Response (matches sources):")
    halluc_score, details = validator.detect_hallucination(good_response, source_nodes)
    print(f"   ✅ Hallucination Score: {halluc_score:.1%}")
    print(f"   📊 Verified Claims: {details['verified_claims']}/{details['total_claims']}")
    
    print("\n2️⃣ Bad Response (contains unsupported claims):")
    halluc_score, details = validator.detect_hallucination(bad_response, source_nodes)
    print(f"   ❌ Hallucination Score: {halluc_score:.1%}")
    print(f"   📊 Verified Claims: {details['verified_claims']}/{details['total_claims']}")
    if details['unverified_claims']:
        print(f"   ⚠️ Unverified: {details['unverified_claims'][0]['claim'][:60]}...")


def test_comprehensive_validation():
    """Test complete validation pipeline"""
    print("\n" + "="*60)
    print("TEST 4: Comprehensive Validation")
    print("="*60)
    
    validator = get_response_validator()
    
    # Mock nodes
    class MockNode:
        def __init__(self, text, score):
            self.text = text
            self.score = score
    
    nodes = [
        MockNode("Isı dedektörleri için alan kapsama 50 m²", 0.85),
        MockNode("Duman dedektörleri 100 m² alan kapsar", 0.78)
    ]
    
    # Perfect response
    perfect_response = """
    - Isı dedektörleri için: 50 m² (IS 3218, 6.5.1.13)
    - Duman dedektörleri için: 100 m² (IS 3218, 6.5.1.14)
    """
    
    # Problematic response
    problem_response = """
    - Isı dedektörleri için yaklaşık 50 metrekare
    - Genelde bu değerler kullanılır
    - Tavsiye edilen yöntem budur
    """
    
    print("\n1️⃣ Perfect Response:")
    result = validator.validate_response(perfect_response, nodes)
    print(f"   ✅ Valid: {result['is_valid']}")
    print(f"   📊 Confidence: {result['confidence']:.1%}")
    print(f"   📊 Citation Coverage: {result['citation_coverage']:.1%}")
    print(f"   📊 Hallucination Score: {result['hallucination_score']:.1%}")
    print(f"   ⭐ Quality Score: {result['details']['confidence_check']}")
    
    print("\n2️⃣ Problematic Response:")
    result = validator.validate_response(problem_response, nodes)
    print(f"   ❌ Valid: {result['is_valid']}")
    print(f"   📊 Confidence: {result['confidence']:.1%}")
    print(f"   📊 Citation Coverage: {result['citation_coverage']:.1%}")
    print(f"   📊 Hallucination Score: {result['hallucination_score']:.1%}")
    if result['warnings']:
        print(f"   ⚠️ Warnings:")
        for warning in result['warnings']:
            print(f"      - {warning}")


if __name__ == "__main__":
    logger.info("🧪 Testing Response Validator...")
    
    test_citation_validation()
    test_confidence_threshold()
    test_hallucination_detection()
    test_comprehensive_validation()
    
    print("\n" + "="*60)
    print("✅ All tests completed!")
    print("="*60)
