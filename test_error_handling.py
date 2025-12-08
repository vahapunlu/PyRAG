"""
Test Error Handling & Resilience
"""

import sys
import time
from pathlib import Path
from loguru import logger

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.error_handler import (
    ErrorHandler,
    ErrorCategory,
    ErrorSeverity,
    with_retry,
    with_fallback,
    safe_execute,
    CircuitBreaker,
    validate_input
)


def test_error_handler():
    """Test error handler"""
    logger.info("=" * 60)
    logger.info("Testing Error Handler")
    logger.info("=" * 60)
    
    handler = ErrorHandler()
    
    # Test 1: Log errors
    logger.info("\n📝 Test 1: Logging errors...")
    
    try:
        raise ValueError("Test validation error")
    except Exception as e:
        handler.log_error(e, ErrorCategory.VALIDATION, ErrorSeverity.LOW, 
                         {'test': 'validation'})
    
    try:
        raise ConnectionError("Test network error")
    except Exception as e:
        handler.log_error(e, ErrorCategory.NETWORK, ErrorSeverity.HIGH,
                         {'test': 'network'})
    
    logger.success("✅ Errors logged")
    
    # Test 2: Get statistics
    logger.info("\n📊 Test 2: Error statistics...")
    stats = handler.get_error_stats()
    logger.info(f"Total errors: {stats['total_errors']}")
    logger.info(f"By category: {stats['by_category']}")
    logger.info(f"Recent errors: {stats['recent_errors']}")
    
    # Test 3: Retry decorator
    logger.info("\n🔄 Test 3: Retry mechanism...")
    
    attempt_count = {'value': 0}
    
    @with_retry(max_attempts=3, delay=0.5, backoff=1.5)
    def unstable_function():
        attempt_count['value'] += 1
        logger.info(f"  Attempt {attempt_count['value']}")
        if attempt_count['value'] < 3:
            raise ConnectionError("Connection failed")
        return "Success!"
    
    try:
        result = unstable_function()
        logger.success(f"✅ Function succeeded: {result}")
    except Exception as e:
        logger.error(f"❌ Function failed: {e}")
    
    # Test 4: Fallback decorator
    logger.info("\n🛟 Test 4: Fallback mechanism...")
    
    @with_fallback(fallback_value="Fallback response")
    def risky_function():
        raise ValueError("Something went wrong")
    
    result = risky_function()
    logger.success(f"✅ Got fallback: {result}")
    
    # Test 5: Safe execute
    logger.info("\n🔒 Test 5: Safe execution...")
    
    def failing_function():
        raise RuntimeError("Expected failure")
    
    result = safe_execute(
        failing_function,
        default_value="Default value",
        error_handler=handler,
        category=ErrorCategory.PROCESSING
    )
    logger.success(f"✅ Safe execute returned: {result}")
    
    # Test 6: Input validation
    logger.info("\n✔️ Test 6: Input validation...")
    
    # Valid input
    try:
        validate_input("test query", str, min_length=1, max_length=100)
        logger.success("✅ Valid input passed")
    except ValueError as e:
        logger.error(f"❌ Validation failed: {e}")
    
    # Invalid input - empty
    try:
        validate_input("", str, min_length=1)
        logger.error("❌ Should have failed for empty string")
    except ValueError as e:
        logger.success(f"✅ Correctly rejected: {e}")
    
    # Invalid input - wrong type
    try:
        validate_input(123, str)
        logger.error("❌ Should have failed for wrong type")
    except ValueError as e:
        logger.success(f"✅ Correctly rejected: {e}")
    
    # Test 7: Circuit breaker
    logger.info("\n🔌 Test 7: Circuit breaker...")
    
    circuit = CircuitBreaker(failure_threshold=3, timeout=5.0)
    
    def unreliable_api():
        raise ConnectionError("API unavailable")
    
    # Trigger failures
    for i in range(5):
        try:
            circuit.call(unreliable_api)
        except Exception as e:
            logger.info(f"  Call {i+1}: {type(e).__name__}")
    
    logger.info(f"Circuit state: {circuit.state}")
    logger.info(f"Failure count: {circuit.failure_count}")
    
    if circuit.state == "OPEN":
        logger.success("✅ Circuit breaker opened after threshold")
    
    logger.info("\n" + "=" * 60)
    logger.success("✅ All error handling tests completed!")
    
    # Final stats
    logger.info("\n📊 Final Statistics:")
    final_stats = handler.get_error_stats()
    logger.info(f"Total errors logged: {final_stats['total_errors']}")
    for category, count in final_stats['by_category'].items():
        if count > 0:
            logger.info(f"  - {category}: {count}")


def test_retry_with_success():
    """Test retry that eventually succeeds"""
    logger.info("\n" + "=" * 60)
    logger.info("Test Retry Success Scenario")
    logger.info("=" * 60)
    
    counter = {'attempts': 0, 'max_attempts': 2}
    
    @with_retry(max_attempts=5, delay=0.3)
    def eventually_succeeds():
        counter['attempts'] += 1
        logger.info(f"Attempt {counter['attempts']}/{counter['max_attempts']}")
        
        if counter['attempts'] < counter['max_attempts']:
            raise RuntimeError("Not yet...")
        
        return f"Success after {counter['attempts']} attempts!"
    
    result = eventually_succeeds()
    logger.success(f"✅ {result}")


def test_nested_error_handling():
    """Test nested error handling"""
    logger.info("\n" + "=" * 60)
    logger.info("Test Nested Error Handling")
    logger.info("=" * 60)
    
    handler = ErrorHandler()
    
    @with_fallback(fallback_value="Layer 2 fallback")
    def layer2_function():
        raise ValueError("Layer 2 error")
    
    @with_fallback(fallback_value="Layer 1 fallback")
    def layer1_function():
        result = layer2_function()
        return f"Layer 1: {result}"
    
    result = layer1_function()
    logger.success(f"✅ Nested fallback result: {result}")


if __name__ == "__main__":
    test_error_handler()
    test_retry_with_success()
    test_nested_error_handling()
