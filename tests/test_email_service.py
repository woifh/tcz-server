"""Property-based tests for email service."""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import date, time, timedelta
from app.models import Member, Court, Reservation
from app.services.email_service import EmailService
from app import db
import random
import time as time_module


# German keywords that should appear in emails
GERMAN_KEYWORDS = ['Guten Tag', 'Platz', 'Datum', 'Uhrzeit', 'Gebucht', 'freundlichen Grüßen']


court_numbers = st.integers(min_value=1, max_value=6)
future_dates = st.dates(min_value=date.today(), max_value=date.today() + timedelta(days=90))
booking_times = st.times(min_value=time(6, 0), max_value=time(20, 0))


@given(court_num=court_numbers, booking_date=future_dates, start=booking_times)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_24_german_email_language(app, mail, court_num, booking_date, start):
    """Feature: tennis-club-reservation, Property 24: All email notifications use German language
    Validates: Requirements 8.1, 8.2, 8.3, 8.5
    
    For any email notification sent by the system (creation, modification, cancellation, 
    admin override), the subject line and body content should be in German.
    """
    with app.app_context():
        with mail.record_messages() as outbox:
            # Create test data
            # Get existing court (created by app fixture)
            court = Court.query.filter_by(number=court_num).first()
            assert court is not None, f"Court {court_num} should exist"
            unique_id = int(time_module.time() * 1000000) % 1000000000
            member1 = Member(name="Test Member 1", email=f"test1_{unique_id}_{court_num}_{booking_date}@example.com", role="member")
            member1.set_password("password123")
            member2 = Member(name="Test Member 2", email=f"test2_{unique_id}_{court_num}_{booking_date}@example.com", role="member")
            member2.set_password("password123")
            db.session.add(member1)
            db.session.add(member2)
            db.session.commit()
            
            end = time(start.hour + 1, start.minute) if start.hour < 20 else time(21, 0)
            
            reservation = Reservation(
                court_id=court.id,
                date=booking_date,
                start_time=start,
                end_time=end,
                booked_for_id=member1.id,
                booked_by_id=member2.id,
                status='active'
            )
            db.session.add(reservation)
            db.session.commit()
            
            # Test booking created email
            EmailService.send_booking_created(reservation)
            
            # Verify emails were sent
            assert len(outbox) >= 1, "At least one email should be sent"
            
            # Check that emails contain German keywords
            for message in outbox:
                body = message.body
                # At least some German keywords should be present
                german_found = any(keyword in body for keyword in GERMAN_KEYWORDS)
                assert german_found, f"Email should contain German text. Body: {body[:100]}"
            
            # Clear outbox
            outbox.clear()
            
            # Test booking modified email
            EmailService.send_booking_modified(reservation)
            assert len(outbox) >= 1, "At least one email should be sent for modification"
            for message in outbox:
                german_found = any(keyword in message.body for keyword in GERMAN_KEYWORDS)
                assert german_found, "Modified email should contain German text"
            
            outbox.clear()
            
            # Test booking cancelled email
            EmailService.send_booking_cancelled(reservation, "Test reason")
            assert len(outbox) >= 1, "At least one email should be sent for cancellation"
            for message in outbox:
                german_found = any(keyword in message.body for keyword in GERMAN_KEYWORDS)
                assert german_found, "Cancelled email should contain German text"
            
            # Cleanup
            db.session.delete(reservation)
            db.session.delete(member1)
            db.session.delete(member2)
            db.session.commit()



@given(court_num=court_numbers, booking_date=future_dates, start=booking_times)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_3_booking_notifications_both_parties(app, mail, court_num, booking_date, start):
    """Feature: tennis-club-reservation, Property 3: Booking notifications sent to both parties
    Validates: Requirements 1.4
    
    For any reservation creation, the system should send email notifications to both 
    the booked_by member and the booked_for member.
    """
    with app.app_context():
        with mail.record_messages() as outbox:
            # Create test data
            # Get existing court (created by app fixture)
            court = Court.query.filter_by(number=court_num).first()
            assert court is not None, f"Court {court_num} should exist"
            unique_id = int(time_module.time() * 1000000) % 1000000000
            member1 = Member(name="Member For", email=f"for_{unique_id}_{court_num}_{booking_date}@example.com", role="member")
            member1.set_password("password123")
            member2 = Member(name="Member By", email=f"by_{unique_id}_{court_num}_{booking_date}@example.com", role="member")
            member2.set_password("password123")
            db.session.add(member1)
            db.session.add(member2)
            db.session.commit()
            
            end = time(start.hour + 1, start.minute) if start.hour < 20 else time(21, 0)
            
            reservation = Reservation(
                court_id=court.id,
                date=booking_date,
                start_time=start,
                end_time=end,
                booked_for_id=member1.id,
                booked_by_id=member2.id,
                status='active'
            )
            db.session.add(reservation)
            db.session.commit()
            
            # Send booking created notification
            EmailService.send_booking_created(reservation)
            
            # Verify both members received emails
            assert len(outbox) == 2, f"Two emails should be sent (one to each member), got {len(outbox)}"
            
            recipients = [msg.recipients[0] for msg in outbox]
            assert member1.email in recipients, "booked_for member should receive email"
            assert member2.email in recipients, "booked_by member should receive email"
            
            # Cleanup
            db.session.delete(reservation)
            db.session.delete(member1)
            db.session.delete(member2)
            db.session.commit()


@given(court_num=court_numbers, booking_date=future_dates, start=booking_times)
@settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_3_booking_notifications_same_member(app, mail, court_num, booking_date, start):
    """Feature: tennis-club-reservation, Property 3: Booking notifications sent to both parties
    Validates: Requirements 1.4
    
    When booked_for and booked_by are the same member, only one email should be sent.
    """
    with app.app_context():
        with mail.record_messages() as outbox:
            # Create test data
            # Get existing court (created by app fixture)
            court = Court.query.filter_by(number=court_num).first()
            assert court is not None, f"Court {court_num} should exist"
            unique_id = int(time_module.time() * 1000000) % 1000000000
            member = Member(name="Member", email=f"same_{unique_id}_{court_num}_{booking_date}@example.com", role="member")
            member.set_password("password123")
            db.session.add(member)
            db.session.commit()
            
            end = time(start.hour + 1, start.minute) if start.hour < 20 else time(21, 0)
            
            reservation = Reservation(
                court_id=court.id,
                date=booking_date,
                start_time=start,
                end_time=end,
                booked_for_id=member.id,
                booked_by_id=member.id,
                status='active'
            )
            db.session.add(reservation)
            db.session.commit()
            
            # Send booking created notification
            EmailService.send_booking_created(reservation)
            
            # Verify only one email is sent when same member
            assert len(outbox) == 1, f"One email should be sent when same member, got {len(outbox)}"
            assert outbox[0].recipients[0] == member.email
            
            # Cleanup
            db.session.delete(reservation)
            db.session.delete(member)
            db.session.commit()
