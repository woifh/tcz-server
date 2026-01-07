#!/usr/bin/env python3
"""Debug script to check for booking conflicts - simplified version."""
import os
import sys

# Print environment check
print("="*80)
print("🔍 ENVIRONMENT CHECK")
print("="*80)
print(f"DATABASE_URL set: {'Yes' if os.environ.get('DATABASE_URL') else 'No'}")
if os.environ.get('DATABASE_URL'):
    # Mask password in output
    db_url = os.environ.get('DATABASE_URL')
    if '@' in db_url:
        parts = db_url.split('@')
        masked = parts[0].split(':')[0] + ':****@' + parts[1]
        print(f"DATABASE_URL: {masked}")
print("="*80)
print()

# Now try to load the app
try:
    from app import create_app, db
    from app.models import Reservation, Court
    from datetime import datetime, date, time
    
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
            print("\n💡 SOLUTION: Run this Python code to delete the reservation:")
            print(f"""
from app import create_app, db
from app.models import Reservation

app = create_app('production')
with app.app_context():
    r = Reservation.query.get({conflict.id})
    if r:
        db.session.delete(r)
        db.session.commit()
        print("✓ Deleted reservation {conflict.id}")
    else:
        print("✗ Reservation not found")
""")
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

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
