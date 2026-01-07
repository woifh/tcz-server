#!/usr/bin/env python3
"""
Test script to verify short notice booking logic works correctly.
"""

import os
from datetime import datetime, time, date, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app import create_app
from app.services.reservation_service import ReservationService
from app.services.validation_service import ValidationService

def test_short_notice_booking_at_2109():
    """Test booking 21:00-22:00 slot at 21:09 (should be allowed as short notice)."""
    app = create_app()
    
    with app.app_context():
        print("=== Testing Short Notice Booking Logic ===")
        
        # Simulate current time: 21:09
        current_time = datetime.combine(date.today(), time(21, 9))
        booking_time = time(21, 0)
        booking_date = date.today()
        
        print(f"Current time: {current_time}")
        print(f"Trying to book: {booking_date} {booking_time}-{time(22, 0)}")
        print()
        
        # Test 1: Check if this is classified as short notice
        is_short_notice = ReservationService.is_short_notice_booking(
            booking_date, booking_time, current_time
        )
        print(f"✓ Is classified as short notice: {is_short_notice}")
        
        # Test 2: Check validation with short notice flag
        court_id = 1  # Assuming court 1 exists
        member_id = 1  # Assuming member 1 exists
        
        is_valid, error_msg = ValidationService.validate_all_booking_constraints(
            court_id, booking_date, booking_time, member_id, is_short_notice
        )
        
        print(f"✓ Validation result: {is_valid}")
        if not is_valid:
            print(f"  Error: {error_msg}")
        else:
            print("  ✅ Booking should be allowed!")
        
        print()
        
        # Test 3: Test with a slot that has already ended (should fail)
        past_time = time(19, 0)  # 19:00-20:00 slot at 21:09 (ended)
        is_valid_past, error_msg_past = ValidationService.validate_all_booking_constraints(
            court_id, booking_date, past_time, member_id, True  # Force short notice
        )
        
        print(f"✓ Booking ended slot (19:00-20:00): {is_valid_past}")
        if not is_valid_past:
            print(f"  Error: {error_msg_past}")
        
        print()
        print("=== Test Complete ===")

if __name__ == "__main__":
    test_short_notice_booking_at_2109()