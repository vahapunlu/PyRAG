"""
Error Handler

Centralized error handling and recovery for PyRAG system.
"""

import traceback
import time
from typing import Optional, Dict, Any, Callable
from functools import wraps
from loguru import logger
from enum import Enum


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"           # Non-critical, can continue
    MEDIUM = "medium"     # Important but recoverable
    HIGH = "high"         # Critical, need immediate attention
    CRITICAL = "critical" # System failure


class ErrorCategory(Enum):
    """Error categories"""
    API = "api"                    # API call failures
    DATABASE = "database"          # DB connection/query issues
    NETWORK = "network"            # Network connectivity
    VALIDATION = "validation"      # Input validation
    PROCESSING = "processing"      # Data processing errors
    CONFIGURATION = "configuration" # Config/setup errors
    UNKNOWN = "unknown"            # Unclassified


class ErrorHandler:
    """
    Centralized error handling with logging, recovery, and metrics
    
    Features:
    - Error categorization
    - Automatic retry logic
    - Fallback mechanisms
    - Error metrics tracking
    - Graceful degradation
    """
    
    def __init__(self):
        """Initialize error handler"""
        self.error_counts = {cat: 0 for cat in ErrorCategory}
        self.last_errors = []
        self.max_history = 100
        
        logger.info("✅ Error Handler initialized")
    
    def log_error(self, error: Exception, category: ErrorCategory, 
                  severity: ErrorSeverity, context: Dict = None):
        """
        Log error with context
        
        Args:
            error: Exception object
            category: Error category
            severity: Error severity
            context: Additional context (function, params, etc.)
        """
        error_info = {
            'timestamp': time.time(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'category': category.value,
            'severity': severity.value,
            'context': context or {},
            'traceback': traceback.format_exc()
        }
        
        # Add to history
        self.last_errors.append(error_info)
        if len(self.last_errors) > self.max_history:
            self.last_errors.pop(0)
        
        # Update counter
        self.error_counts[category] += 1
        
        # Log based on severity
        if severity == ErrorSeverity.CRITICAL:
            logger.critical(f"💥 CRITICAL ERROR [{category.value}]: {error}")
        elif severity == ErrorSeverity.HIGH:
            logger.error(f"❌ ERROR [{category.value}]: {error}")
        elif severity == ErrorSeverity.MEDIUM:
            logger.warning(f"⚠️ WARNING [{category.value}]: {error}")
        else:
            logger.info(f"ℹ️ INFO [{category.value}]: {error}")
        
        # Log context if available
        if context:
            logger.debug(f"Context: {context}")
    
    def get_error_stats(self) -> Dict:
        """Get error statistics"""
        return {
            'total_errors': sum(self.error_counts.values()),
            'by_category': {cat.value: count for cat, count in self.error_counts.items()},
            'recent_errors': len(self.last_errors),
            'last_10_errors': self.last_errors[-10:] if self.last_errors else []
        }
    
    def clear_history(self):
        """Clear error history"""
        self.last_errors.clear()
        logger.info("🧹 Error history cleared")


# Singleton instance
_error_handler = None

def get_error_handler() -> ErrorHandler:
    """Get or create error handler singleton"""
    global _error_handler
    
    if _error_handler is None:
        _error_handler = ErrorHandler()
    
    return _error_handler


def with_retry(max_attempts: int = 3, delay: float = 1.0, 
               backoff: float = 2.0, exceptions: tuple = (Exception,)):
    """
    Decorator for automatic retry with exponential backoff
    
    Args:
        max_attempts: Maximum retry attempts
        delay: Initial delay between retries (seconds)
        backoff: Backoff multiplier
        exceptions: Tuple of exceptions to catch
        
    Example:
        @with_retry(max_attempts=3, delay=1.0)
        def api_call():
            return requests.get(url)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 1
            current_delay = delay
            
            while attempt <= max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts:
                        logger.error(f"❌ Failed after {max_attempts} attempts: {func.__name__}")
                        raise
                    
                    logger.warning(f"⚠️ Attempt {attempt}/{max_attempts} failed for {func.__name__}: {e}")
                    logger.info(f"🔄 Retrying in {current_delay:.1f}s...")
                    
                    time.sleep(current_delay)
                    current_delay *= backoff
                    attempt += 1
            
        return wrapper
    return decorator


def with_fallback(fallback_func: Callable = None, fallback_value: Any = None):
    """
    Decorator for fallback mechanism
    
    Args:
        fallback_func: Function to call on error
        fallback_value: Value to return on error
        
    Example:
        @with_fallback(fallback_value="Default response")
        def risky_operation():
            return api_call()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"⚠️ Error in {func.__name__}, using fallback: {e}")
                
                if fallback_func:
                    try:
                        return fallback_func(*args, **kwargs)
                    except Exception as fallback_error:
                        logger.error(f"❌ Fallback also failed: {fallback_error}")
                
                return fallback_value
        
        return wrapper
    return decorator


def safe_execute(func: Callable, *args, default_value: Any = None, 
                error_handler: ErrorHandler = None, 
                category: ErrorCategory = ErrorCategory.UNKNOWN, **kwargs) -> Any:
    """
    Safely execute function with error handling
    
    Args:
        func: Function to execute
        *args: Function arguments
        default_value: Value to return on error
        error_handler: ErrorHandler instance
        category: Error category
        **kwargs: Function keyword arguments
        
    Returns:
        Function result or default_value on error
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if error_handler:
            error_handler.log_error(
                error=e,
                category=category,
                severity=ErrorSeverity.MEDIUM,
                context={'function': func.__name__, 'args': args, 'kwargs': kwargs}
            )
        else:
            logger.error(f"❌ Error in {func.__name__}: {e}")
        
        return default_value


class CircuitBreaker:
    """
    Circuit breaker pattern for preventing cascading failures
    
    States:
    - CLOSED: Normal operation
    - OPEN: Too many failures, reject requests
    - HALF_OPEN: Testing if service recovered
    """
    
    def __init__(self, failure_threshold: int = 5, timeout: float = 60.0):
        """
        Initialize circuit breaker
        
        Args:
            failure_threshold: Number of failures before opening circuit
            timeout: Time to wait before trying again (seconds)
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"
    
    def call(self, func: Callable, *args, **kwargs):
        """
        Call function through circuit breaker
        
        Args:
            func: Function to call
            *args, **kwargs: Function arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If circuit is open or function fails
        """
        # Check circuit state
        if self.state == "OPEN":
            if time.time() - self.last_failure_time < self.timeout:
                raise Exception(f"Circuit breaker OPEN for {func.__name__}")
            else:
                self.state = "HALF_OPEN"
                logger.info(f"🔄 Circuit breaker HALF_OPEN for {func.__name__}")
        
        try:
            result = func(*args, **kwargs)
            
            # Success - reset on HALF_OPEN
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
                logger.success(f"✅ Circuit breaker CLOSED for {func.__name__}")
            
            return result
            
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
                logger.error(f"🚫 Circuit breaker OPEN for {func.__name__} (failures: {self.failure_count})")
            
            raise


def validate_input(value: Any, value_type: type, allow_none: bool = False, 
                  min_length: int = None, max_length: int = None) -> bool:
    """
    Validate input value
    
    Args:
        value: Value to validate
        value_type: Expected type
        allow_none: Allow None values
        min_length: Minimum length (for strings/lists)
        max_length: Maximum length (for strings/lists)
        
    Returns:
        True if valid
        
    Raises:
        ValueError: If validation fails
    """
    # None check
    if value is None:
        if allow_none:
            return True
        raise ValueError("Value cannot be None")
    
    # Type check
    if not isinstance(value, value_type):
        raise ValueError(f"Expected {value_type.__name__}, got {type(value).__name__}")
    
    # Length checks for strings/lists
    if hasattr(value, '__len__'):
        length = len(value)
        
        if min_length is not None and length < min_length:
            raise ValueError(f"Length {length} is less than minimum {min_length}")
        
        if max_length is not None and length > max_length:
            raise ValueError(f"Length {length} exceeds maximum {max_length}")
    
    return True
