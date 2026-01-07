#!/usr/bin/env python3
"""Test script to verify short-notice booking API response"""

import os
from datetime import datetime, date, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app import create_app
from app.models import Reservation

app = create_app()
with app.app_context():
    # Test today's availability
    today = date.today()
    print(f"Testing availability for {today}")
    
    # Get reservations directly from database
    reservations = Reservation.query.filter_by(date=today).all()
    print(f"\nDirect database query - Found {len(reservations)} reservations for today:")
    for res in reservations:
        print(f"  ID: {res.id}, Court: {res.court_id}, Time: {res.start_time}, Short notice: {res.is_short_notice}")
    
    # Test the availability API logic manually
    from app.services.reservation_service import ReservationService
    from app.models import Court
    from datetime import time
    
    # Get all courts
    courts = Court.query.order_by(Court.number).all()
    
    # Get reservations for the date
    reservations = ReservationService.get_reservations_by_date(today)
    
    print(f"\nReservationService query - Found {len(reservations)} reservations:")
    for res in reservations:
        print(f"  ID: {res.id}, Court: {res.court_id}, Time: {res.start_time}, Short notice: {res.is_short_notice}")
    
    # Build a sample of the grid for 14:00 slot (where we have short-notice bookings)
    slot_time = time(14, 0)
    print(f"\nChecking slot {slot_time} across all courts:")
    
    for court in courts:
        slot_status = 'available'
        slot_details = None
        
        for reservation in reservations:
            if (reservation.court_id == court.id and 
                reservation.start_time == slot_time and
                reservation.status == 'active'):
                # Set status based on whether it's a short notice booking
                slot_status = 'short_notice' if reservation.is_short_notice else 'reserved'
                slot_details = {
                    'booked_for': f"{reservation.booked_for.firstname} {reservation.booked_for.lastname}",
                    'booked_for_id': reservation.booked_for_id,
                    'booked_by': f"{reservation.booked_by.firstname} {reservation.booked_by.lastname}",
                    'booked_by_id': reservation.booked_by_id,
                    'reservation_id': reservation.id,
                    'is_short_notice': reservation.is_short_notice
                }
                print(f"  Court {court.number}: {slot_status} - Reservation {reservation.id} (is_short_notice: {reservation.is_short_notice})")
                break
        
        if slot_status == 'available':
            print(f"  Court {court.number}: {slot_status}")