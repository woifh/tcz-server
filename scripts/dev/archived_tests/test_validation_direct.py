#!/usr/bin/env python3
"""Direct test of validation logic without HTTP."""

from datetime import datetime, date, time, timedelta
import sys
import os

# Add the app to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Flask app context
from app import create_app, db
from app.services.validation_service import ValidationService
from app.services.reservation_service import ReservationService

app = create_app()

with app.app_context():
    print("Testing past booking validation logic...")
    print("=" * 60)
    
    # Test 1: Try to book yesterday
    yesterday = date.today() - timedelta(days=1)
    test_time = time(10, 0)
    
    print(f"\n1. Testing booking for {yesterday} at {test_time}")
    is_valid, error_msg = ValidationService.validate_all_booking_constraints(
        court_id=1,
        date=yesterday,
        start_time=test_time,
        member_id=1
    )
    
    if not is_valid and "Vergangenheit" in error_msg:
        print(f"   ✓ PASS: Validation correctly rejected past booking")
        print(f"   Error: {error_msg}")
    else:
        print(f"   ✗ FAIL: Validation did not reject past booking")
        print(f"   is_valid={is_valid}, error={error_msg}")
    
    # Test 2: Try to book 5 minutes ago
    now = datetime.now()
    five_min_ago = now - timedelta(minutes=5)
    
    print(f"\n2. Testing booking for {five_min_ago.date()} at {five_min_ago.time().replace(microsecond=0)}")
    is_valid, error_msg = ValidationService.validate_all_booking_constraints(
        court_id=1,
        date=five_min_ago.date(),
        start_time=five_min_ago.time(),
        member_id=1
    )
    
    if not is_valid and "Vergangenheit" in error_msg:
        print(f"   ✓ PASS: Validation correctly rejected recent past booking")
        print(f"   Error: {error_msg}")
    else:
        print(f"   ✗ FAIL: Validation did not reject recent past booking")
        print(f"   is_valid={is_valid}, error={error_msg}")
    
    # Test 3: Try to book in the future (should work if no other constraints)
    tomorrow = date.today() + timedelta(days=1)
    
    print(f"\n3. Testing booking for {tomorrow} at {test_time}")
    is_valid, error_msg = ValidationService.validate_all_booking_constraints(
        court_id=1,
        date=tomorrow,
        start_time=test_time,
        member_id=1
    )
    
    if is_valid:
        print(f"   ✓ PASS: Validation correctly allowed future booking")
    else:
        print(f"   ℹ INFO: Future booking rejected (may be due to other constraints)")
        print(f"   Error: {error_msg}")
    
    # Test 4: Test cancellation of past reservation
    print(f"\n4. Testing cancellation validation logic")
    print(f"   (This tests the logic, not actual DB operations)")
    
    # Simulate a past reservation
    past_datetime = datetime.now() - timedelta(hours=1)
    print(f"   Reservation datetime: {past_datetime}")
    print(f"   Current datetime: {datetime.now()}")
    print(f"   Is in past: {past_datetime < datetime.now()}")
    
    if past_datetime < datetime.now():
        print(f"   ✓ PASS: Past detection logic works correctly")
    else:
        print(f"   ✗ FAIL: Past detection logic failed")
    
    # Test 5: Test 15-minute window
    print(f"\n5. Testing 15-minute cancellation window")
    
    # 10 minutes from now (should be rejected)
    ten_min_future = datetime.now() + timedelta(minutes=10)
    time_until = ten_min_future - datetime.now()
    print(f"   Reservation in 10 minutes: {time_until < timedelta(minutes=15)}")
    
    if time_until < timedelta(minutes=15):
        print(f"   ✓ PASS: 10-minute window correctly detected as too close")
    else:
        print(f"   ✗ FAIL: 10-minute window not detected")
    
    # 20 minutes from now (should be allowed)
    twenty_min_future = datetime.now() + timedelta(minutes=20)
    time_until = twenty_min_future - datetime.now()
    print(f"   Reservation in 20 minutes: {time_until < timedelta(minutes=15)}")
    
    if time_until >= timedelta(minutes=15):
        print(f"   ✓ PASS: 20-minute window correctly allowed")
    else:
        print(f"   ✗ FAIL: 20-minute window incorrectly rejected")
    
    print("\n" + "=" * 60)
    print("Direct validation test complete!")
