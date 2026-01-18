#!/usr/bin/env python3
"""
Debug script to trace exactly what happens during a booking attempt.
"""

import os
from datetime import datetime, time, date, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app import create_app
from app.services.reservation_service import ReservationService
from app.services.validation_service import ValidationService

def debug_booking_issue():
    """Debug the exact booking issue."""
    app = create_app()
    
    with app.app_context():
        print("=== Debugging Booking Issue ===")
        print()
        
        # Simulate the exact request
        court_id = 5
        booking_date = date.today()  # 2025-12-09
        start_time = time(21, 0)
        booked_for_id = 7
        booked_by_id = 7  # Assuming same user
        
        print(f"Request details:")
        print(f"  Court ID: {court_id}")
        print(f"  Date: {booking_date}")
        print(f"  Start time: {start_time}")
        print(f"  Booked for ID: {booked_for_id}")
        print(f"  Current time: {datetime.now()}")
        print()
        
        # Step 1: Check if it's classified as short notice
        print("Step 1: Checking if booking is short notice...")
        is_short_notice = ReservationService.is_short_notice_booking(booking_date, start_time)
        print(f"  Result: {is_short_notice}")
        print()
        
        # Step 2: Test validation step by step
        print("Step 2: Testing validation constraints...")
        
        # Test past booking validation
        booking_datetime = datetime.combine(booking_date, start_time)
        now = datetime.now()
        print(f"  Booking datetime: {booking_datetime}")
        print(f"  Current datetime: {now}")
        print(f"  Is in past: {booking_datetime < now}")
        
        if is_short_notice:
            slot_end_time = booking_datetime + timedelta(hours=1)
            print(f"  Slot end time: {slot_end_time}")
            print(f"  Slot has ended: {slot_end_time <= now}")
        print()
        
        # Test full validation
        print("Step 3: Testing full validation...")
        is_valid, error_msg, _ = ValidationService.validate_all_booking_constraints(
            court_id, booking_date, start_time, booked_for_id, is_short_notice
        )
        print(f"  Validation result: {is_valid}")
        print(f"  Error message: {error_msg}")
        print()
        
        # Step 4: Test the full reservation creation
        print("Step 4: Testing full reservation creation...")
        reservation, error, _ = ReservationService.create_reservation(
            court_id=court_id,
            date=booking_date,
            start_time=start_time,
            booked_for_id=booked_for_id,
            booked_by_id=booked_by_id
        )
        
        if error:
            print(f"  ❌ Creation failed: {error}")
        else:
            print(f"  ✅ Creation successful!")
            print(f"     Reservation ID: {reservation.id}")
            print(f"     Is short notice: {reservation.is_short_notice}")
        
        print()
        print("=== Debug Complete ===")

if __name__ == "__main__":
    debug_booking_issue()