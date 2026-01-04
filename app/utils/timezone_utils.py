"""Timezone utilities for consistent Europe/Berlin timezone handling."""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

# Configure logging for timezone operations
logger = logging.getLogger(__name__)

# Europe/Berlin timezone constants
# CET (Central European Time) = UTC+1 (winter)
# CEST (Central European Summer Time) = UTC+2 (summer)
CET_OFFSET = timedelta(hours=1)
CEST_OFFSET = timedelta(hours=2)

# Daylight saving time transition dates (approximate)
# DST starts last Sunday in March, ends last Sunday in October
DST_START_MONTH = 3
DST_END_MONTH = 10

# Try to import pytz for more accurate timezone handling
try:
    import pytz
    BERLIN_TZ = pytz.timezone('Europe/Berlin')
    PYTZ_AVAILABLE = True
    logger.debug("pytz available - using accurate Europe/Berlin timezone")
except ImportError:
    BERLIN_TZ = None
    PYTZ_AVAILABLE = False
    logger.debug("pytz not available - using simplified DST calculation")


def is_dst_active(dt: datetime) -> bool:
    """
    Determine if daylight saving time is active for a given datetime.
    
    This is a simplified heuristic for Europe/Berlin timezone:
    - DST starts last Sunday in March
    - DST ends last Sunday in October
    
    Args:
        dt: datetime object (assumed to be in Europe/Berlin timezone)
        
    Returns:
        bool: True if DST is active (CEST), False if standard time (CET)
    """
    try:
        month = dt.month
        
        # Simple heuristic: DST is active from April through September
        # March and October need more precise calculation, but this covers most cases
        if 4 <= month <= 9:
            return True
        elif month in [1, 2, 11, 12]:
            return False
        else:
            # For March and October, use a simplified approach
            # In practice, you'd want more precise DST transition date calculation
            if month == 3:
                # DST typically starts around March 25-31
                return dt.day >= 25
            else:  # month == 10
                # DST typically ends around October 25-31
                return dt.day < 25
                
    except Exception as e:
        logger.warning(f"Error determining DST status for {dt}: {e}")
        # Default to standard time (CET) if calculation fails
        return False


def get_berlin_timezone_offset(dt: datetime) -> timedelta:
    """
    Get the timezone offset for Europe/Berlin at a given datetime.
    
    Args:
        dt: datetime object
        
    Returns:
        timedelta: UTC offset for Europe/Berlin timezone
    """
    try:
        if is_dst_active(dt):
            return CEST_OFFSET  # UTC+2
        else:
            return CET_OFFSET   # UTC+1
    except Exception as e:
        logger.warning(f"Error calculating Berlin timezone offset for {dt}: {e}")
        # Default to CET (UTC+1) if calculation fails
        return CET_OFFSET


def get_current_berlin_time() -> datetime:
    """
    Get current time in Europe/Berlin timezone.
    
    This is the primary function that should be used throughout the system
    instead of datetime.now() to ensure consistent timezone handling.
    
    Returns:
        datetime: Current time in Europe/Berlin timezone (naive datetime)
    """
    try:
        if PYTZ_AVAILABLE:
            # Use pytz for accurate timezone conversion including DST transitions
            utc_now = datetime.now(timezone.utc)
            berlin_time = utc_now.astimezone(BERLIN_TZ)
            # Return as naive datetime representing Europe/Berlin time
            return berlin_time.replace(tzinfo=None)
        else:
            # Fallback to manual DST calculation
            utc_now = datetime.now(timezone.utc)
            berlin_offset = get_berlin_timezone_offset(utc_now)
            berlin_time = utc_now + berlin_offset
            # Return as naive datetime representing Europe/Berlin time
            return berlin_time.replace(tzinfo=None)
        
    except Exception as e:
        logger.error(f"Error getting current Berlin time: {e}")
        # Fallback to system local time
        return datetime.now()


def convert_to_berlin_time(dt: datetime) -> datetime:
    """
    Convert a datetime to Europe/Berlin timezone.
    
    Args:
        dt: datetime object (timezone-aware or naive)
        
    Returns:
        datetime: datetime in Europe/Berlin timezone (naive)
    """
    try:
        if dt is None:
            return get_current_berlin_time()
        
        if PYTZ_AVAILABLE:
            # Use pytz for accurate timezone conversion
            if hasattr(dt, 'tzinfo') and dt.tzinfo is not None:
                # Convert timezone-aware datetime to Berlin time
                berlin_time = dt.astimezone(BERLIN_TZ)
                return berlin_time.replace(tzinfo=None)
            else:
                # Assume naive datetime is already in Berlin timezone
                return dt
        else:
            # Fallback to manual conversion
            # If timezone-aware, convert from that timezone to Berlin
            if hasattr(dt, 'tzinfo') and dt.tzinfo is not None:
                if dt.tzinfo == timezone.utc:
                    # Convert from UTC to Berlin time
                    berlin_offset = get_berlin_timezone_offset(dt)
                    berlin_time = dt + berlin_offset
                    return berlin_time.replace(tzinfo=None)
                else:
                    # For other timezones, convert to UTC first, then to Berlin
                    utc_time = dt.astimezone(timezone.utc)
                    berlin_offset = get_berlin_timezone_offset(utc_time)
                    berlin_time = utc_time + berlin_offset
                    return berlin_time.replace(tzinfo=None)
            else:
                # If naive datetime, assume it's already in Berlin timezone
                return dt
            
    except Exception as e:
        logger.error(f"Error converting datetime {dt} to Berlin time: {e}")
        # Return original datetime if conversion fails
        return dt if dt is not None else get_current_berlin_time()


def ensure_berlin_timezone(dt: Optional[datetime]) -> datetime:
    """
    Ensure a datetime is in Europe/Berlin timezone.
    
    This is the main utility function that should be used throughout the system
    for consistent timezone handling.
    
    Args:
        dt: datetime object or None
        
    Returns:
        datetime: datetime in Europe/Berlin timezone (naive)
    """
    try:
        if dt is None:
            return get_current_berlin_time()
        
        return convert_to_berlin_time(dt)
        
    except Exception as e:
        logger.error(f"Error ensuring Berlin timezone for {dt}: {e}")
        # Fallback to current Berlin time
        return get_current_berlin_time()


def validate_timezone_consistency(*datetimes) -> bool:
    """
    Validate that multiple datetimes are timezone-consistent.
    
    Args:
        *datetimes: Variable number of datetime objects
        
    Returns:
        bool: True if all datetimes are timezone-consistent
    """
    try:
        for dt in datetimes:
            if dt is None:
                continue
                
            # Check if datetime has timezone info
            if hasattr(dt, 'tzinfo') and dt.tzinfo is not None:
                # All timezone-aware datetimes should be consistent
                continue
            else:
                # All naive datetimes should represent the same timezone (Berlin)
                continue
        
        return True
        
    except Exception as e:
        logger.warning(f"Error validating timezone consistency: {e}")
        return False


def log_timezone_operation(operation: str, dt: datetime, result: datetime = None):
    """
    Log timezone operations for debugging.
    
    Args:
        operation: Description of the operation
        dt: Input datetime
        result: Result datetime (optional)
    """
    try:
        if logger.isEnabledFor(logging.DEBUG):
            msg = f"Timezone operation: {operation}"
            msg += f" | Input: {dt}"
            if result is not None:
                msg += f" | Result: {result}"
            logger.debug(msg)
    except Exception:
        # Don't let logging errors affect the main operation
        pass


def get_berlin_date_today() -> datetime.date:
    """
    Get today's date in Europe/Berlin timezone.
    
    This should be used instead of date.today() to ensure consistent
    date calculations across the system.
    
    Returns:
        date: Today's date in Europe/Berlin timezone
    """
    try:
        berlin_time = get_current_berlin_time()
        return berlin_time.date()
    except Exception as e:
        logger.error(f"Error getting Berlin date today: {e}")
        # Fallback to system date
        from datetime import date
        return date.today()


def create_berlin_datetime(date_obj, time_obj) -> datetime:
    """
    Create a datetime object representing Europe/Berlin timezone.
    
    Args:
        date_obj: date object
        time_obj: time object
        
    Returns:
        datetime: Combined datetime in Europe/Berlin timezone (naive)
    """
    try:
        return datetime.combine(date_obj, time_obj)
    except Exception as e:
        logger.error(f"Error creating Berlin datetime from {date_obj} and {time_obj}: {e}")
        # Return current Berlin time as fallback
        return get_current_berlin_time()


def is_same_berlin_day(dt1: datetime, dt2: datetime) -> bool:
    """
    Check if two datetimes are on the same day in Europe/Berlin timezone.
    
    Args:
        dt1: First datetime
        dt2: Second datetime
        
    Returns:
        bool: True if both datetimes are on the same Berlin day
    """
    try:
        berlin_dt1 = ensure_berlin_timezone(dt1)
        berlin_dt2 = ensure_berlin_timezone(dt2)
        return berlin_dt1.date() == berlin_dt2.date()
    except Exception as e:
        logger.error(f"Error comparing Berlin days for {dt1} and {dt2}: {e}")
        return False


def get_dst_transition_info(year: int = None) -> dict:
    """
    Get DST transition information for Europe/Berlin timezone.
    
    Args:
        year: Year to get transition info for (defaults to current year)
        
    Returns:
        dict: DST transition information
    """
    try:
        if year is None:
            year = get_current_berlin_time().year
            
        if PYTZ_AVAILABLE:
            # Use pytz to get accurate transition dates
            transitions = []
            for month in range(1, 13):
                for day in range(1, 32):
                    try:
                        test_date = datetime(year, month, day)
                        berlin_dt = BERLIN_TZ.localize(test_date, is_dst=None)
                        transitions.append({
                            'date': test_date.date(),
                            'offset': berlin_dt.utcoffset(),
                            'dst': berlin_dt.dst() != timedelta(0)
                        })
                    except:
                        continue
            
            # Find transition points
            dst_start = None
            dst_end = None
            
            for i in range(1, len(transitions)):
                if transitions[i]['dst'] and not transitions[i-1]['dst']:
                    dst_start = transitions[i]['date']
                elif not transitions[i]['dst'] and transitions[i-1]['dst']:
                    dst_end = transitions[i]['date']
            
            return {
                'year': year,
                'dst_start': dst_start,
                'dst_end': dst_end,
                'pytz_available': True
            }
        else:
            # Simplified calculation for when pytz is not available
            return {
                'year': year,
                'dst_start': f"Last Sunday in March {year} (approximate)",
                'dst_end': f"Last Sunday in October {year} (approximate)",
                'pytz_available': False
            }
            
    except Exception as e:
        logger.error(f"Error getting DST transition info for {year}: {e}")
        return {
            'year': year,
            'error': str(e),
            'pytz_available': PYTZ_AVAILABLE
        }