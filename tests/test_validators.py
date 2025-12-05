"""Tests for input validators."""
import pytest
from datetime import datetime, date, time
from app.utils.validators import (
    ValidationError,
    validate_required_fields,
    validate_date_format,
    validate_time_format,
    validate_integer,
    validate_email_address,
    validate_string_length,
    validate_choice
)


class TestValidateRequiredFields:
    """Test validate_required_fields function."""
    
    def test_all_fields_present(self):
        """Test validation passes when all fields present."""
        data = {'name': 'Test', 'email': 'test@example.com'}
        validate_required_fields(data, ['name', 'email'])  # Should not raise
    
    def test_missing_field_raises_error(self):
        """Test validation fails when field missing."""
        data = {'name': 'Test'}
        with pytest.raises(ValidationError, match='Fehlende erforderliche Felder: email'):
            validate_required_fields(data, ['name', 'email'])
    
    def test_empty_field_raises_error(self):
        """Test validation fails when field is empty."""
        data = {'name': '', 'email': 'test@example.com'}
        with pytest.raises(ValidationError, match='name'):
            validate_required_fields(data, ['name', 'email'])


class TestValidateDateFormat:
    """Test validate_date_format function."""
    
    def test_valid_date(self):
        """Test valid date string."""
        result = validate_date_format('2025-12-05', 'date')
        assert result == date(2025, 12, 5)
    
    def test_invalid_format_raises_error(self):
        """Test invalid date format raises error."""
        with pytest.raises(ValidationError, match='Ungültiges Datumsformat'):
            validate_date_format('05-12-2025', 'date')
    
    def test_missing_date_raises_error(self):
        """Test missing date raises error."""
        with pytest.raises(ValidationError, match='ist erforderlich'):
            validate_date_format(None, 'date')
    
    def test_empty_date_raises_error(self):
        """Test empty date raises error."""
        with pytest.raises(ValidationError, match='ist erforderlich'):
            validate_date_format('', 'date')


class TestValidateTimeFormat:
    """Test validate_time_format function."""
    
    def test_valid_time(self):
        """Test valid time string."""
        result = validate_time_format('14:30', 'time')
        assert result == time(14, 30)
    
    def test_invalid_format_raises_error(self):
        """Test invalid time format raises error."""
        with pytest.raises(ValidationError, match='Ungültiges Zeitformat'):
            validate_time_format('2:30 PM', 'time')
    
    def test_missing_time_raises_error(self):
        """Test missing time raises error."""
        with pytest.raises(ValidationError, match='ist erforderlich'):
            validate_time_format(None, 'time')


class TestValidateInteger:
    """Test validate_integer function."""
    
    def test_valid_integer(self):
        """Test valid integer."""
        result = validate_integer(5, 'value')
        assert result == 5
    
    def test_string_integer(self):
        """Test string that can be converted to integer."""
        result = validate_integer('10', 'value')
        assert result == 10
    
    def test_min_value_validation(self):
        """Test minimum value validation."""
        with pytest.raises(ValidationError, match='muss mindestens 1 sein'):
            validate_integer(0, 'value', min_value=1)
    
    def test_max_value_validation(self):
        """Test maximum value validation."""
        with pytest.raises(ValidationError, match='darf höchstens 10 sein'):
            validate_integer(11, 'value', max_value=10)
    
    def test_none_raises_error(self):
        """Test None value raises error."""
        with pytest.raises(ValidationError, match='ist erforderlich'):
            validate_integer(None, 'value')
    
    def test_invalid_type_raises_error(self):
        """Test invalid type raises error."""
        with pytest.raises(ValidationError, match='muss eine Zahl sein'):
            validate_integer('abc', 'value')


class TestValidateEmailAddress:
    """Test validate_email_address function."""
    
    def test_valid_email(self):
        """Test valid email address."""
        # Use a real domain that exists
        result = validate_email_address('test@gmail.com', 'email')
        assert '@gmail.com' in result
    
    def test_invalid_email_raises_error(self):
        """Test invalid email raises error."""
        with pytest.raises(ValidationError, match='Ungültige E-Mail-Adresse'):
            validate_email_address('not-an-email', 'email')
    
    def test_missing_email_raises_error(self):
        """Test missing email raises error."""
        with pytest.raises(ValidationError, match='ist erforderlich'):
            validate_email_address(None, 'email')
    
    def test_empty_email_raises_error(self):
        """Test empty email raises error."""
        with pytest.raises(ValidationError, match='ist erforderlich'):
            validate_email_address('', 'email')


class TestValidateStringLength:
    """Test validate_string_length function."""
    
    def test_valid_string(self):
        """Test valid string."""
        result = validate_string_length('test', 'value')
        assert result == 'test'
    
    def test_min_length_validation(self):
        """Test minimum length validation."""
        with pytest.raises(ValidationError, match='muss mindestens 5 Zeichen lang sein'):
            validate_string_length('abc', 'value', min_length=5)
    
    def test_max_length_validation(self):
        """Test maximum length validation."""
        with pytest.raises(ValidationError, match='darf höchstens 5 Zeichen lang sein'):
            validate_string_length('abcdefgh', 'value', max_length=5)
    
    def test_strips_whitespace(self):
        """Test that whitespace is stripped."""
        result = validate_string_length('  test  ', 'value')
        assert result == 'test'
    
    def test_none_raises_error(self):
        """Test None value raises error."""
        with pytest.raises(ValidationError, match='ist erforderlich'):
            validate_string_length(None, 'value')


class TestValidateChoice:
    """Test validate_choice function."""
    
    def test_valid_choice(self):
        """Test valid choice."""
        result = validate_choice('a', ['a', 'b', 'c'], 'value')
        assert result == 'a'
    
    def test_invalid_choice_raises_error(self):
        """Test invalid choice raises error."""
        with pytest.raises(ValidationError, match='muss einer der folgenden Werte sein'):
            validate_choice('d', ['a', 'b', 'c'], 'value')
