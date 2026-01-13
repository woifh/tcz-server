"""Input validation utilities."""
import uuid as uuid_module
from datetime import datetime, date, time
from functools import wraps
from flask import request, jsonify
from email_validator import validate_email, EmailNotValidError


class ValidationError(Exception):
    """Custom validation error."""
    pass


def validate_required_fields(data, required_fields):
    """
    Validate that all required fields are present in data.
    
    Args:
        data: Dictionary of data to validate
        required_fields: List of required field names
        
    Raises:
        ValidationError: If any required field is missing
    """
    missing = [field for field in required_fields if not data.get(field)]
    if missing:
        raise ValidationError(f"Fehlende erforderliche Felder: {', '.join(missing)}")


def validate_date_format(date_str, field_name="date"):
    """
    Validate and parse date string in YYYY-MM-DD format.
    
    Args:
        date_str: Date string to validate
        field_name: Name of the field (for error messages)
        
    Returns:
        date: Parsed date object
        
    Raises:
        ValidationError: If date format is invalid
    """
    if not date_str:
        raise ValidationError(f"{field_name} ist erforderlich")
    
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        raise ValidationError(f"Ungültiges Datumsformat für {field_name}. Erwartet: YYYY-MM-DD")


def validate_time_format(time_str, field_name="time"):
    """
    Validate and parse time string in HH:MM format.
    
    Args:
        time_str: Time string to validate
        field_name: Name of the field (for error messages)
        
    Returns:
        time: Parsed time object
        
    Raises:
        ValidationError: If time format is invalid
    """
    if not time_str:
        raise ValidationError(f"{field_name} ist erforderlich")
    
    try:
        return datetime.strptime(time_str, '%H:%M').time()
    except ValueError:
        raise ValidationError(f"Ungültiges Zeitformat für {field_name}. Erwartet: HH:MM")


def validate_integer(value, field_name="value", min_value=None, max_value=None):
    """
    Validate integer value with optional range check.
    
    Args:
        value: Value to validate
        field_name: Name of the field (for error messages)
        min_value: Optional minimum value
        max_value: Optional maximum value
        
    Returns:
        int: Validated integer
        
    Raises:
        ValidationError: If value is invalid
    """
    if value is None:
        raise ValidationError(f"{field_name} ist erforderlich")
    
    try:
        int_value = int(value)
    except (ValueError, TypeError):
        raise ValidationError(f"{field_name} muss eine Zahl sein")
    
    if min_value is not None and int_value < min_value:
        raise ValidationError(f"{field_name} muss mindestens {min_value} sein")
    
    if max_value is not None and int_value > max_value:
        raise ValidationError(f"{field_name} darf höchstens {max_value} sein")
    
    return int_value


def validate_uuid(value, field_name="id"):
    """
    Validate UUID string format.

    Args:
        value: Value to validate
        field_name: Name of the field (for error messages)

    Returns:
        str: Validated UUID string

    Raises:
        ValidationError: If value is not a valid UUID
    """
    if value is None:
        raise ValidationError(f"{field_name} ist erforderlich")

    str_value = str(value).strip()

    try:
        # Validate it's a proper UUID format
        uuid_module.UUID(str_value)
        return str_value
    except (ValueError, AttributeError):
        raise ValidationError(f"{field_name} muss eine gültige UUID sein")


def validate_email_address(email, field_name="email"):
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
        field_name: Name of the field (for error messages)
        
    Returns:
        str: Normalized email address
        
    Raises:
        ValidationError: If email is invalid
    """
    if not email:
        raise ValidationError(f"{field_name} ist erforderlich")
    
    try:
        # Allow test domains in development
        valid = validate_email(email, check_deliverability=False)
        return valid.email
    except EmailNotValidError:
        raise ValidationError(f"Ungültige E-Mail-Adresse: {email}")


def validate_string_length(value, field_name="value", min_length=None, max_length=None):
    """
    Validate string length.
    
    Args:
        value: String to validate
        field_name: Name of the field (for error messages)
        min_length: Optional minimum length
        max_length: Optional maximum length
        
    Returns:
        str: Validated string
        
    Raises:
        ValidationError: If string length is invalid
    """
    if value is None:
        raise ValidationError(f"{field_name} ist erforderlich")
    
    str_value = str(value).strip()
    
    if min_length is not None and len(str_value) < min_length:
        raise ValidationError(f"{field_name} muss mindestens {min_length} Zeichen lang sein")
    
    if max_length is not None and len(str_value) > max_length:
        raise ValidationError(f"{field_name} darf höchstens {max_length} Zeichen lang sein")
    
    return str_value


def validate_choice(value, choices, field_name="value"):
    """
    Validate that value is one of the allowed choices.
    
    Args:
        value: Value to validate
        choices: List of allowed values
        field_name: Name of the field (for error messages)
        
    Returns:
        Value if valid
        
    Raises:
        ValidationError: If value not in choices
    """
    if value not in choices:
        raise ValidationError(f"{field_name} muss einer der folgenden Werte sein: {', '.join(map(str, choices))}")
    
    return value


def validate_request_data(required_fields=None, optional_fields=None):
    """
    Decorator to validate request data before processing.
    
    Args:
        required_fields: Dict of {field_name: validator_function}
        optional_fields: Dict of {field_name: validator_function}
        
    Returns:
        Decorator function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Get data from request
                data = request.get_json() if request.is_json else request.form
                
                validated_data = {}
                
                # Validate required fields
                if required_fields:
                    for field_name, validator in required_fields.items():
                        if field_name not in data:
                            return jsonify({'error': f'Fehlendes Feld: {field_name}'}), 400
                        
                        try:
                            validated_data[field_name] = validator(data[field_name])
                        except ValidationError as e:
                            return jsonify({'error': str(e)}), 400
                
                # Validate optional fields
                if optional_fields:
                    for field_name, validator in optional_fields.items():
                        if field_name in data and data[field_name]:
                            try:
                                validated_data[field_name] = validator(data[field_name])
                            except ValidationError as e:
                                return jsonify({'error': str(e)}), 400
                
                # Add validated data to kwargs
                kwargs['validated_data'] = validated_data
                
                return f(*args, **kwargs)
                
            except Exception as e:
                return jsonify({'error': f'Validierungsfehler: {str(e)}'}), 400
        
        return decorated_function
    return decorator
