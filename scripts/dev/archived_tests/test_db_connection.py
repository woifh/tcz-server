#!/usr/bin/env python3
"""Test database connection"""
from dotenv import load_dotenv
load_dotenv()

from app import create_app, db
from app.models import Member, Court, Reservation
from datetime import date

app = create_app('development')

with app.app_context():
    try:
        # Test basic queries
        member_count = Member.query.count()
        print(f"✅ Members in database: {member_count}")
        
        court_count = Court.query.count()
        print(f"✅ Courts in database: {court_count}")
        
        reservation_count = Reservation.query.count()
        print(f"✅ Reservations in database: {reservation_count}")
        
        # Test the specific query used in availability endpoint
        from app.services.reservation_service import ReservationService
        reservations = ReservationService.get_reservations_by_date(date.today())
        print(f"✅ Reservations for today: {len(reservations)}")
        
        print("\n✅ All database operations successful!")
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        import traceback
        traceback.print_exc()
