#!/usr/bin/env python3
"""
Script to test short notice booking display.
This script will help you create a test short notice booking to verify the orange color display.
"""

import os
from datetime import datetime, time, date, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app import create_app
from app.models import Reservation, Member, Court
from app.services.reservation_service import ReservationService
from app import db

def create_test_short_notice_booking():
    """Create a test short notice booking for tomorrow."""
    app = create_app()
    
    with app.app_context():
        print("=== Creating Test Short Notice Booking ===")
        
        # Get the first available member and court
        member = Member.query.first()
        court = Court.query.first()
        
        if not member or not court:
            print("❌ No members or courts found in database")
            return
        
        print(f"Using member: {member.firstname} {member.lastname} (ID: {member.id})")
        print(f"Using court: {court.number} (ID: {court.id})")
        
        # Create a booking for tomorrow at 10:00 but mark it as short notice
        tomorrow = date.today() + timedelta(days=1)
        start_time = time(10, 0)
        end_time = time(11, 0)
        
        # Create the reservation directly with is_short_notice=True
        test_reservation = Reservation(
            court_id=court.id,
            date=tomorrow,
            start_time=start_time,
            end_time=end_time,
            booked_for_id=member.id,
            booked_by_id=member.id,
            status='active',
            is_short_notice=True  # Force this to be a short notice booking
        )
        
        try:
            db.session.add(test_reservation)
            db.session.commit()
            
            print(f"✅ Created test short notice booking:")
            print(f"   Court: {court.number}")
            print(f"   Date: {tomorrow}")
            print(f"   Time: {start_time} - {end_time}")
            print(f"   is_short_notice: {test_reservation.is_short_notice}")
            print(f"   Reservation ID: {test_reservation.id}")
            print()
            print("🔍 Now check the dashboard for tomorrow's date to see the orange cell!")
            print(f"   URL: http://localhost:5001 (change date to {tomorrow})")
            
        except Exception as e:
            print(f"❌ Error creating test booking: {e}")
            db.session.rollback()

def update_existing_reservations():
    """Update existing reservations to be short notice for testing."""
    app = create_app()
    
    with app.app_context():
        print("=== Updating Existing Reservations for Testing ===")
        
        # Find reservations for today at 21:00 (these should be short notice)
        today = date.today()
        reservations = Reservation.query.filter(
            Reservation.date == today,
            Reservation.start_time == time(21, 0),
            Reservation.status == 'active'
        ).all()
        
        if not reservations:
            print("❌ No reservations found for today at 21:00")
            return
        
        print(f"Found {len(reservations)} reservations for today at 21:00")
        
        for reservation in reservations:
            print(f"Updating reservation {reservation.id} to short notice...")
            reservation.is_short_notice = True
        
        try:
            db.session.commit()
            print("✅ Updated reservations to short notice")
            print("🔍 Refresh the dashboard to see orange cells!")
            
        except Exception as e:
            print(f"❌ Error updating reservations: {e}")
            db.session.rollback()

def check_reservation_status():
    """Check the status of existing reservations."""
    app = create_app()
    
    with app.app_context():
        print("=== Checking Existing Reservations ===")
        
        today = date.today()
        reservations = Reservation.query.filter(
            Reservation.date == today,
            Reservation.status == 'active'
        ).order_by(Reservation.start_time).all()
        
        if not reservations:
            print("❌ No active reservations found for today")
            return
        
        print(f"Found {len(reservations)} active reservations for today:")
        print()
        
        for reservation in reservations:
            print(f"Reservation {reservation.id}:")
            print(f"  Court: {reservation.court.number}")
            print(f"  Time: {reservation.start_time} - {reservation.end_time}")
            print(f"  Booked for: {reservation.booked_for.firstname} {reservation.booked_for.lastname}")
            print(f"  is_short_notice: {reservation.is_short_notice}")
            
            # Check if this should be short notice based on current time
            current_time = datetime.now()
            should_be_short_notice = ReservationService.is_short_notice_booking(
                reservation.date, reservation.start_time, current_time
            )
            print(f"  Should be short notice: {should_be_short_notice}")
            print()

if __name__ == "__main__":
    print("🧪 Short Notice Booking Test Script")
    print()
    print("Choose an option:")
    print("1. Check existing reservation status")
    print("2. Create test short notice booking for tomorrow")
    print("3. Update existing 21:00 reservations to short notice")
    print()
    
    choice = input("Enter choice (1-3): ").strip()
    
    if choice == "1":
        check_reservation_status()
    elif choice == "2":
        create_test_short_notice_booking()
    elif choice == "3":
        update_existing_reservations()
    else:
        print("Invalid choice")