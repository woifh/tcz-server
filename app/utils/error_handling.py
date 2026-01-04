"""Error handling utilities for active booking session logic."""
import logging
from datetime import datetime, date as date_class
from typing import Optional, Tuple, List, Any
from functools import wraps

# Configure logging
logger = logging.getLogger(__name__)


def with_fallback_to_date_logic(fallback_message: str = None):
    """
    Decorator to provide fallback to date-based logic when time-based logic fails.
    
    Args:
        fallback_message: Custom message to log when fallback is used
        
    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Try the enhanced time-based logic first
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Time-based logic failed in {func.__name__}: {e}")
                
                # Log fallback usage
                message = fallback_message or f"Falling back to date-based logic in {func.__name__}"
                logger.warning(message)
                
                # Try to call the fallback version if it exists
                fallback_func_name = f"{func.__name__}_fallback"
                if hasattr(func, '__self__'):
                    # Method case
                    if hasattr(func.__self__, fallback_func_name):
                        fallback_func = getattr(func.__self__, fallback_func_name)
                        return fallback_func(*args, **kwargs)
                else:
                    # Function case - look in the same module
                    import sys
                    module = sys.modules[func.__module__]
                    if hasattr(module, fallback_func_name):
                        fallback_func = getattr(module, fallback_func_name)
                        return fallback_func(*args, **kwargs)
                
                # If no fallback function exists, re-raise the original error
                raise e
        return wrapper
    return decorator


def safe_time_operation(operation_name: str, default_value: Any = None):
    """
    Decorator for safe time operations with comprehensive error handling.
    
    Args:
        operation_name: Name of the operation for logging
        default_value: Value to return if operation fails
        
    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {operation_name}: {e}")
                logger.debug(f"Args: {args}, Kwargs: {kwargs}")
                
                if default_value is not None:
                    logger.info(f"Returning default value for {operation_name}: {default_value}")
                    return default_value
                else:
                    # Re-raise if no default value provided
                    raise e
        return wrapper
    return decorator


class ActiveBookingSessionError(Exception):
    """Custom exception for active booking session logic errors."""
    
    def __init__(self, message: str, original_error: Exception = None, fallback_attempted: bool = False):
        self.message = message
        self.original_error = original_error
        self.fallback_attempted = fallback_attempted
        super().__init__(self.message)


class TimezoneHandlingError(ActiveBookingSessionError):
    """Exception for timezone handling errors."""
    pass


class ValidationError(ActiveBookingSessionError):
    """Exception for validation errors."""
    pass


def log_error_with_context(error: Exception, context: dict, operation: str):
    """
    Log an error with additional context information.
    
    Args:
        error: The exception that occurred
        context: Dictionary with context information
        operation: Name of the operation that failed
    """
    try:
        logger.error(f"Error in {operation}: {str(error)}")
        logger.error(f"Error type: {type(error).__name__}")
        
        if context:
            logger.error(f"Context: {context}")
        
        # Log stack trace for debugging
        logger.debug("Stack trace:", exc_info=True)
        
    except Exception as logging_error:
        # Don't let logging errors affect the main operation
        print(f"Failed to log error: {logging_error}")


def get_fallback_active_reservations_date_based(member_id: int, include_short_notice: bool = True) -> List:
    """
    Fallback method to get active reservations using date-based logic.
    
    This is used when the time-based logic fails.
    
    Args:
        member_id: ID of the member
        include_short_notice: Whether to include short notice bookings
        
    Returns:
        List of active Reservation objects
    """
    try:
        from app.models import Reservation
        
        today = date_class.today()
        
        query = Reservation.query.filter(
            (Reservation.booked_for_id == member_id) | (Reservation.booked_by_id == member_id),
            Reservation.status == 'active',
            Reservation.date >= today
        )
        
        if not include_short_notice:
            query = query.filter(Reservation.is_short_notice == False)
        
        return query.order_by(Reservation.date, Reservation.start_time).all()
        
    except Exception as e:
        logger.error(f"Fallback date-based logic also failed: {e}")
        return []


def validate_time_based_inputs(current_time: Optional[datetime], 
                              reservation_date: Optional[date_class] = None,
                              reservation_time: Optional[datetime.time] = None) -> Tuple[bool, str]:
    """
    Validate inputs for time-based operations.
    
    Args:
        current_time: Current datetime
        reservation_date: Reservation date (optional)
        reservation_time: Reservation time (optional)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Validate current_time
        if current_time is not None:
            if not isinstance(current_time, datetime):
                return False, f"current_time must be datetime object, got {type(current_time)}"
        
        # Validate reservation_date
        if reservation_date is not None:
            if not isinstance(reservation_date, date_class):
                return False, f"reservation_date must be date object, got {type(reservation_date)}"
        
        # Validate reservation_time
        if reservation_time is not None:
            if not isinstance(reservation_time, datetime.time):
                return False, f"reservation_time must be time object, got {type(reservation_time)}"
        
        return True, ""
        
    except Exception as e:
        return False, f"Error validating inputs: {e}"


def create_error_response(error: Exception, operation: str, user_friendly: bool = True) -> Tuple[bool, str]:
    """
    Create a standardized error response.
    
    Args:
        error: The exception that occurred
        operation: Name of the operation that failed
        user_friendly: Whether to return user-friendly message
        
    Returns:
        Tuple of (success=False, error_message)
    """
    try:
        # Log the technical error
        logger.error(f"Error in {operation}: {str(error)}")
        
        if user_friendly:
            # Return user-friendly message
            if isinstance(error, TimezoneHandlingError):
                return False, "Zeitzonenfehler aufgetreten. Bitte versuchen Sie es erneut."
            elif isinstance(error, ValidationError):
                return False, "Validierungsfehler aufgetreten. Bitte überprüfen Sie Ihre Eingaben."
            else:
                return False, "Ein unerwarteter Fehler ist aufgetreten. Bitte versuchen Sie es erneut."
        else:
            # Return technical error message
            return False, f"Error in {operation}: {str(error)}"
            
    except Exception as response_error:
        logger.error(f"Error creating error response: {response_error}")
        return False, "Ein Systemfehler ist aufgetreten."


def get_time_based_error_messages() -> dict:
    """
    Get updated error messages that reflect time-based logic.
    
    Returns:
        Dictionary of error messages with time-based descriptions
    """
    return {
        'RESERVATION_LIMIT_REGULAR': "Sie haben bereits 2 aktive Buchungen (zukünftige oder laufende Reservierungen). Aktive Buchungen sind solche, die noch nicht beendet sind.",
        'RESERVATION_LIMIT_SHORT_NOTICE': "Sie haben bereits eine aktive kurzfristige Buchung (zukünftige oder laufende Reservierung). Nur eine kurzfristige Buchung pro Mitglied ist erlaubt.",
        'AVAILABILITY_INFO': "Verfügbare Buchungsplätze: {available_slots} von 2 (basierend auf aktueller Zeit)",
        'CANCELLATION_STARTED': "Diese Buchung kann nicht mehr storniert werden (Spielzeit bereits begonnen)",
        'CANCELLATION_TOO_LATE': "Diese Buchung kann nicht mehr storniert werden (weniger als 15 Minuten bis Spielbeginn)",
        'SHORT_NOTICE_NO_CANCEL': "Kurzfristige Buchungen können nicht storniert werden",
        'BOOKING_PAST_ENDED': "Kurzfristige Buchungen sind nur möglich, solange die Spielzeit noch nicht beendet ist",
        'BOOKING_PAST_REGULAR': "Buchungen in der Vergangenheit sind nicht möglich",
        'TIME_CALCULATION_ERROR': "Fehler bei der Zeitberechnung. Bitte versuchen Sie es erneut.",
        'FALLBACK_ACTIVE': "System verwendet vereinfachte Zeitlogik aufgrund technischer Probleme"
    }


def handle_time_calculation_error(error: Exception, operation: str, context: dict = None, 
                                 fallback_func=None, fallback_args=None, fallback_kwargs=None):
    """
    Handle time calculation errors with comprehensive logging and fallback.
    
    Args:
        error: The exception that occurred
        operation: Name of the operation that failed
        context: Additional context information
        fallback_func: Fallback function to call
        fallback_args: Arguments for fallback function
        fallback_kwargs: Keyword arguments for fallback function
        
    Returns:
        Result from fallback function or raises exception
    """
    try:
        # Log the error with full context
        log_error_with_context(error, context or {}, operation)
        
        # Log system health information for debugging
        health_info = get_system_health_info()
        logger.error(f"System health at time of error: {health_info}")
        
        # Attempt fallback if provided
        if fallback_func:
            logger.warning(f"Attempting fallback for {operation}")
            try:
                args = fallback_args or []
                kwargs = fallback_kwargs or {}
                result = fallback_func(*args, **kwargs)
                logger.info(f"Fallback successful for {operation}")
                return result
            except Exception as fallback_error:
                logger.error(f"Fallback also failed for {operation}: {fallback_error}")
                raise ActiveBookingSessionError(
                    f"Both primary and fallback methods failed for {operation}",
                    original_error=error,
                    fallback_attempted=True
                )
        else:
            # No fallback available, re-raise original error
            raise ActiveBookingSessionError(
                f"Time calculation failed for {operation} and no fallback available",
                original_error=error,
                fallback_attempted=False
            )
            
    except ActiveBookingSessionError:
        # Re-raise our custom exceptions
        raise
    except Exception as handling_error:
        # Error in error handling itself
        logger.critical(f"Error in error handling for {operation}: {handling_error}")
        raise ActiveBookingSessionError(
            f"Critical error in error handling for {operation}",
            original_error=error,
            fallback_attempted=False
        )


def monitor_performance(operation_name: str, threshold_ms: int = 1000):
    """
    Decorator to monitor performance of time-based operations.
    
    Args:
        operation_name: Name of the operation
        threshold_ms: Performance threshold in milliseconds
        
    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            import time
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000
                
                if duration_ms > threshold_ms:
                    logger.warning(f"Performance warning: {operation_name} took {duration_ms:.2f}ms (threshold: {threshold_ms}ms)")
                else:
                    logger.debug(f"Performance: {operation_name} took {duration_ms:.2f}ms")
        
        return wrapper
    return decorator


def get_system_health_info() -> dict:
    """
    Get system health information for debugging time-based operations.
    
    Returns:
        Dictionary with system health information
    """
    try:
        from app.utils.timezone_utils import get_current_berlin_time
        
        health_info = {
            'current_berlin_time': get_current_berlin_time().isoformat(),
            'system_time': datetime.now().isoformat(),
            'utc_time': datetime.utcnow().isoformat(),
            'timezone_handling_available': True
        }
        
        return health_info
        
    except Exception as e:
        logger.error(f"Error getting system health info: {e}")
        return {
            'error': str(e),
            'timezone_handling_available': False,
            'system_time': datetime.now().isoformat()
        }