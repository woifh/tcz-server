"""Performance tests for active booking session logic with time-based queries."""
import pytest
import time
from datetime import date, time as dt_time, datetime, timedelta
from app import create_app, db
from app.models import Member, Court, Reservation
from app.services.reservation_service import ReservationService
from app.services.validation_service import ValidationService


class TestActiveBookingSessionPerformance:
    """Performance tests for active booking session logic with time-based queries."""
    
    @pytest.fixture
    def app(self):
        """Create test app."""
        app = create_app('testing')
        with app.app_context():
            db.create_all()
            
            # Create courts
            for i in range(1, 7):
                court = Court(number=i)
                db.session.add(court)
            db.session.commit()
            
            yield app
            
            db.session.remove()
            db.drop_all()
    
    @pytest.fixture
    def test_court(self, app):
        """Get test court."""
        with app.app_context():
            return Court.query.filter_by(number=1).first()
    
    def create_test_member(self, email="test@example.com"):
        """Create a test member in the current app context."""
        member = Member(
            firstname="Test",
            lastname="Member",
            email=email,
            role="member"
        )
        member.set_password("password123")
        db.session.add(member)
        db.session.commit()
        return member
    
    def create_large_dataset(self, app, test_court, num_members=50, reservations_per_member=20):
        """Create a large dataset for performance testing."""
        members = []
        reservations = []
        
        # Create members
        for i in range(num_members):
            member = self.create_test_member(f"member{i}@example.com")
            members.append(member.id)  # Store ID instead of object
        
        # Create reservations for each member (mix of past, current, and future)
        current_time = datetime.now()
        for member_id in members:
            for j in range(reservations_per_member):
                # Create reservations spanning from 30 days ago to 30 days in the future
                days_offset = j - (reservations_per_member // 2)
                reservation_date = date.today() + timedelta(days=days_offset)
                
                # Use different time slots
                hour = 8 + (j % 12)  # Hours 8-19
                start_time = dt_time(hour, 0)
                end_time = dt_time(hour + 1, 0)
                
                # Mix of regular and short notice bookings
                is_short_notice = (j % 5 == 0)
                
                reservation = Reservation(
                    court_id=test_court.id,
                    date=reservation_date,
                    start_time=start_time,
                    end_time=end_time,
                    booked_for_id=member_id,
                    booked_by_id=member_id,
                    status='active',
                    is_short_notice=is_short_notice
                )
                db.session.add(reservation)
                reservations.append(reservation)
        
        db.session.commit()
        return members, reservations
    
    def test_time_based_query_performance_with_large_dataset(self, app, test_court):
        """Test that time-based queries perform well with large datasets."""
        with app.app_context():
            # Create a large dataset
            member_ids, reservations = self.create_large_dataset(app, test_court, num_members=50, reservations_per_member=20)
            
            print(f"\nCreated {len(member_ids)} members with {len(reservations)} total reservations")
            
            current_time = datetime.now()
            
            # Test performance of get_member_active_booking_sessions
            performance_results = []
            
            for i, member_id in enumerate(member_ids[:10]):  # Test first 10 members
                start_time = time.time()
                
                active_sessions = ReservationService.get_member_active_booking_sessions(
                    member_id, current_time=current_time
                )
                
                end_time = time.time()
                query_time = end_time - start_time
                performance_results.append(query_time)
                
                # Verify results are correct
                assert isinstance(active_sessions, list)
                
                # All returned sessions should be active
                for session in active_sessions:
                    is_active = ReservationService.is_reservation_currently_active(
                        session, current_time
                    )
                    assert is_active is True, "All returned sessions should be active"
                
                print(f"Member {i+1}: {len(active_sessions)} active sessions, query time: {query_time:.4f}s")
            
            # Performance assertions
            avg_query_time = sum(performance_results) / len(performance_results)
            max_query_time = max(performance_results)
            
            print(f"Average query time: {avg_query_time:.4f}s")
            print(f"Maximum query time: {max_query_time:.4f}s")
            
            # Queries should complete quickly (less than 0.1 seconds on average)
            assert avg_query_time < 0.1, f"Average query time too slow: {avg_query_time:.4f}s"
            assert max_query_time < 0.5, f"Maximum query time too slow: {max_query_time:.4f}s"
    
    def test_validation_service_performance_with_large_dataset(self, app, test_court):
        """Test that validation service performs well with large datasets."""
        with app.app_context():
            # Create a large dataset
            member_ids, reservations = self.create_large_dataset(app, test_court, num_members=30, reservations_per_member=15)
            
            current_time = datetime.now()
            
            # Test performance of reservation limit validation
            performance_results = []
            
            for i, member_id in enumerate(member_ids[:10]):  # Test first 10 members
                start_time = time.time()
                
                # Test regular reservation limit validation
                can_book_regular = ValidationService.validate_member_reservation_limit(
                    member_id, is_short_notice=False, current_time=current_time
                )
                
                # Test short notice reservation limit validation
                can_book_short_notice = ValidationService.validate_member_short_notice_limit(
                    member_id, current_time=current_time
                )
                
                end_time = time.time()
                query_time = end_time - start_time
                performance_results.append(query_time)
                
                # Verify results are boolean
                assert isinstance(can_book_regular, bool)
                assert isinstance(can_book_short_notice, bool)
                
                print(f"Member {i+1}: regular={can_book_regular}, short_notice={can_book_short_notice}, query time: {query_time:.4f}s")
            
            # Performance assertions
            avg_query_time = sum(performance_results) / len(performance_results)
            max_query_time = max(performance_results)
            
            print(f"Average validation time: {avg_query_time:.4f}s")
            print(f"Maximum validation time: {max_query_time:.4f}s")
            
            # Validation should complete quickly (less than 0.05 seconds on average)
            assert avg_query_time < 0.05, f"Average validation time too slow: {avg_query_time:.4f}s"
            assert max_query_time < 0.2, f"Maximum validation time too slow: {max_query_time:.4f}s"
    
    def test_concurrent_time_based_queries_performance(self, app, test_court):
        """Test performance when multiple time-based queries are executed concurrently."""
        with app.app_context():
            # Create a moderate dataset
            member_ids, reservations = self.create_large_dataset(app, test_court, num_members=20, reservations_per_member=10)
            
            current_time = datetime.now()
            
            # Simulate concurrent queries by running multiple operations in sequence
            start_time = time.time()
            
            results = []
            for member_id in member_ids[:15]:  # Test 15 members
                # Multiple operations per member (simulating concurrent usage)
                active_sessions = ReservationService.get_member_active_booking_sessions(
                    member_id, current_time=current_time
                )
                
                short_notice_bookings = ReservationService.get_member_active_short_notice_bookings(
                    member_id, current_time=current_time
                )
                
                can_book = ValidationService.validate_member_reservation_limit(
                    member_id, current_time=current_time
                )
                
                results.append({
                    'active_sessions': len(active_sessions),
                    'short_notice_bookings': len(short_notice_bookings),
                    'can_book': can_book
                })
            
            end_time = time.time()
            total_time = end_time - start_time
            
            print(f"Processed {len(results)} members with multiple queries each")
            print(f"Total time: {total_time:.4f}s")
            print(f"Average time per member: {total_time/len(results):.4f}s")
            
            # Should handle multiple concurrent-style queries efficiently
            assert total_time < 2.0, f"Total concurrent query time too slow: {total_time:.4f}s"
            assert total_time/len(results) < 0.15, f"Average per-member time too slow: {total_time/len(results):.4f}s"
    
    def test_time_based_query_scalability(self, app, test_court):
        """Test how time-based queries scale with increasing data size."""
        with app.app_context():
            # Test with different dataset sizes
            dataset_sizes = [10, 25, 50]  # Number of reservations per member
            performance_data = []
            
            test_member = self.create_test_member("scalability_test@example.com")
            
            for size in dataset_sizes:
                # Clean up previous reservations
                Reservation.query.filter_by(booked_for_id=test_member.id).delete()
                db.session.commit()
                
                # Create reservations for this test
                current_time = datetime.now()
                for j in range(size):
                    days_offset = j - (size // 2)
                    reservation_date = date.today() + timedelta(days=days_offset)
                    
                    hour = 8 + (j % 12)
                    start_time = dt_time(hour, 0)
                    end_time = dt_time(hour + 1, 0)
                    
                    reservation = Reservation(
                        court_id=test_court.id,
                        date=reservation_date,
                        start_time=start_time,
                        end_time=end_time,
                        booked_for_id=test_member.id,
                        booked_by_id=test_member.id,
                        status='active',
                        is_short_notice=(j % 4 == 0)
                    )
                    db.session.add(reservation)
                
                db.session.commit()
                
                # Measure query performance
                start_time = time.time()
                
                active_sessions = ReservationService.get_member_active_booking_sessions(
                    test_member.id, current_time=current_time
                )
                
                end_time = time.time()
                query_time = end_time - start_time
                
                performance_data.append({
                    'dataset_size': size,
                    'query_time': query_time,
                    'active_sessions': len(active_sessions)
                })
                
                print(f"Dataset size: {size}, Query time: {query_time:.4f}s, Active sessions: {len(active_sessions)}")
            
            # Verify scalability - query time should not increase dramatically
            for i in range(1, len(performance_data)):
                prev_time = performance_data[i-1]['query_time']
                curr_time = performance_data[i]['query_time']
                size_ratio = performance_data[i]['dataset_size'] / performance_data[i-1]['dataset_size']
                
                # Query time should not increase more than proportionally to data size
                # Allow some overhead but it shouldn't be exponential
                max_acceptable_time = prev_time * size_ratio * 2  # Allow 2x overhead
                
                assert curr_time < max_acceptable_time, \
                    f"Query time increased too much: {curr_time:.4f}s vs expected max {max_acceptable_time:.4f}s"
    
    def test_database_index_effectiveness(self, app, test_court):
        """Test that database queries are using indexes effectively."""
        with app.app_context():
            # Create a dataset that would benefit from proper indexing
            member_ids, reservations = self.create_large_dataset(app, test_court, num_members=30, reservations_per_member=15)
            
            current_time = datetime.now()
            test_member_id = member_ids[0]
            
            # Test query performance multiple times to get consistent results
            query_times = []
            
            for _ in range(5):  # Run 5 times
                start_time = time.time()
                
                # This query should benefit from indexes on:
                # - booked_for_id, booked_by_id (member lookup)
                # - status (active reservations)
                # - date, end_time (time-based filtering)
                active_sessions = ReservationService.get_member_active_booking_sessions(
                    test_member_id, current_time=current_time
                )
                
                end_time = time.time()
                query_times.append(end_time - start_time)
            
            avg_query_time = sum(query_times) / len(query_times)
            
            print(f"Average query time over 5 runs: {avg_query_time:.4f}s")
            print(f"Query returned {len(active_sessions)} active sessions")
            
            # With proper indexing, queries should be very fast even with large datasets
            assert avg_query_time < 0.01, f"Query time suggests missing indexes: {avg_query_time:.4f}s"
    
    def test_real_time_updates_performance(self, app, test_court):
        """Test that real-time updates don't impact system performance."""
        with app.app_context():
            # Create a moderate dataset
            member_ids, reservations = self.create_large_dataset(app, test_court, num_members=20, reservations_per_member=10)
            
            # Simulate real-time scenario: queries at different times
            base_time = datetime.now()
            time_intervals = [
                base_time - timedelta(hours=2),  # 2 hours ago
                base_time - timedelta(hours=1),  # 1 hour ago
                base_time,                       # Now
                base_time + timedelta(hours=1),  # 1 hour from now
                base_time + timedelta(hours=2),  # 2 hours from now
            ]
            
            performance_results = []
            
            for i, test_time in enumerate(time_intervals):
                start_time = time.time()
                
                # Query multiple members at this time point
                total_active_sessions = 0
                for member_id in member_ids[:10]:
                    active_sessions = ReservationService.get_member_active_booking_sessions(
                        member_id, current_time=test_time
                    )
                    total_active_sessions += len(active_sessions)
                
                end_time = time.time()
                query_time = end_time - start_time
                performance_results.append(query_time)
                
                print(f"Time point {i+1}: {total_active_sessions} total active sessions, query time: {query_time:.4f}s")
            
            # Performance should be consistent across different time points
            avg_time = sum(performance_results) / len(performance_results)
            max_time = max(performance_results)
            min_time = min(performance_results)
            
            print(f"Average time: {avg_time:.4f}s, Min: {min_time:.4f}s, Max: {max_time:.4f}s")
            
            # Variance should be low (consistent performance)
            time_variance = max_time - min_time
            assert time_variance < 0.05, f"Performance variance too high: {time_variance:.4f}s"
            assert avg_time < 0.1, f"Average performance too slow: {avg_time:.4f}s"