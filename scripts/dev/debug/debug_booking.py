#!/usr/bin/env python3
"""Debug script to check for booking conflicts."""
from app import create_app, db
from app.models import Reservation, Court
from datetime import datetime, date, time
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Always use production config on PythonAnywhere
app = create_app('production')

with app.app_context():
    # Check for reservations on Court 3, December 5, 2025 at 07:00
    court_id = 3
    check_date = date(2025, 12, 5)
    check_time = time(7, 0)
    
    print("="*80)
    print("🔍 DEBUGGING BOOKING CONFLICT")
    print("="*80)
    print(f"Court: {court_id}")
    print(f"Date: {check_date}")
    print(f"Time: {check_time}")
    print("="*80)
    
    # Find all reservations for this court on this date
    all_reservations = Reservation.query.filter_by(
        court_id=court_id,
        date=check_date
    ).all()
    
    print(f"\n📋 ALL Reservations for Court {court_id} on {check_date}:")
    print("-"*80)
    if all_reservations:
        for r in all_reservations:
            print(f"ID: {r.id}")
            print(f"  Time: {r.start_time} - {r.end_time}")
            print(f"  Status: {r.status}")
            print(f"  Booked for: {r.booked_for.name} (ID: {r.booked_for_id})")
            print(f"  Booked by: {r.booked_by.name} (ID: {r.booked_by_id})")
            print(f"  Created: {r.created_at}")
            print("-"*80)
    else:
        print("  No reservations found")
    
    # Check specifically for the conflicting time
    print(f"\n🎯 Checking for ACTIVE reservation at {check_time}:")
    print("-"*80)
    conflict = Reservation.query.filter_by(
        court_id=court_id,
        date=check_date,
        start_time=check_time,
        status='active'
    ).first()
    
    if conflict:
        print("❌ CONFLICT FOUND!")
        print(f"  ID: {conflict.id}")
        print(f"  Time: {conflict.start_time} - {conflict.end_time}")
        print(f"  Status: {conflict.status}")
        print(f"  Booked for: {conflict.booked_for.name}")
        print(f"  Booked by: {conflict.booked_by.name}")
        print(f"  Created: {conflict.created_at}")
        print("\n💡 SOLUTION: Delete this reservation:")
        print(f"     DELETE FROM reservation WHERE id = {conflict.id};")
    else:
        print("✅ No conflict found - slot should be available!")
    
    # Check for cancelled reservations at this time
    print(f"\n🗑️  Checking for CANCELLED reservations at {check_time}:")
    print("-"*80)
    cancelled = Reservation.query.filter_by(
        court_id=court_id,
        date=check_date,
        start_time=check_time,
        status='cancelled'
    ).all()
    
    if cancelled:
        for r in cancelled:
            print(f"  ID: {r.id} - Status: {r.status} - Reason: {r.reason}")
    else:
        print("  No cancelled reservations")
    
    print("\n" + "="*80)
