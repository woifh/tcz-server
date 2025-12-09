#!/usr/bin/env python3
"""
Check the current reservation status and update if needed.
"""

import os
from datetime import date, time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app import create_app
from app.models import Reservation
from app import db

def check_and_fix_reservation():
    """Check the 21:00 reservation and fix its short notice status if needed."""
    app = create_app()
    
    with app.app_context():
        print("=== Checking 21:00 Reservation ===")
        
        # Find the 21:00 reservation for today
        today = date.today()
        reservation = Reservation.query.filter_by(
            date=today,
            start_time=time(21, 0),
            status='active'
        ).first()
        
        if reservation:
            print(f"Found reservation {reservation.id}:")
            print(f"  Court: {reservation.court.number}")
            print(f"  Time: {reservation.start_time}")
            print(f"  Booked for: {reservation.booked_for.firstname} {reservation.booked_for.lastname}")
            print(f"  is_short_notice: {reservation.is_short_notice}")
            print(f"  Created at: {reservation.created_at}")
            
            # If it's not marked as short notice, fix it
            if not reservation.is_short_notice:
                print()
                print("🔧 This should be a short notice booking! Fixing...")
                reservation.is_short_notice = True
                db.session.commit()
                print("✅ Updated reservation to short notice")
                print("🔄 Please refresh your browser to see the orange color!")
            else:
                print("✅ Reservation is correctly marked as short notice")
        else:
            print("❌ No 21:00 reservation found for today")
            print("   Try making the booking again")

if __name__ == "__main__":
    check_and_fix_reservation()