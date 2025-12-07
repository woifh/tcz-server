"""Tests for MemberService."""
import pytest
from app import create_app, db
from app.models import Member
from app.services.member_service import MemberService


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


class TestMemberServiceSearch:
    """Test MemberService search_members method."""
    
    def test_search_members_by_name(self, app):
        """Test searching members by name."""
        with app.app_context():
            # Create test members
            member1 = Member(firstname="Alice", lastname="Smith", email="alice@example.com", role="member")
            member1.set_password("password123")
            member2 = Member(firstname="Bob", lastname="Johnson", email="bob@example.com", role="member")
            member2.set_password("password123")
            member3 = Member(firstname="Alice", lastname="Brown", email="alice.brown@example.com", role="member")
            member3.set_password("password123")
            
            db.session.add_all([member1, member2, member3])
            db.session.commit()
            
            # Search for "Alice"
            results = MemberService.search_members("Alice", member1.id)
            
            # Should return member3 (Alice Brown) but not member1 (current member)
            assert len(results) == 1
            assert results[0].id == member3.id
    
    def test_search_members_by_email(self, app):
        """Test searching members by email."""
        with app.app_context():
            # Create test members
            member1 = Member(firstname="Alice", lastname="Smith", email="alice@example.com", role="member")
            member1.set_password("password123")
            member2 = Member(firstname="Bob", lastname="Johnson", email="bob@test.com", role="member")
            member2.set_password("password123")
            member3 = Member(firstname="Charlie", lastname="Davis", email="charlie@example.com", role="member")
            member3.set_password("password123")
            
            db.session.add_all([member1, member2, member3])
            db.session.commit()
            
            # Search for "example"
            results = MemberService.search_members("example", member1.id)
            
            # Should return member3 but not member1 (current member)
            assert len(results) == 1
            assert results[0].id == member3.id
    
    def test_search_excludes_current_member(self, app):
        """Test that search excludes the current member."""
        with app.app_context():
            # Create test members
            member1 = Member(firstname="Alice", lastname="Smith", email="alice@example.com", role="member")
            member1.set_password("password123")
            member2 = Member(firstname="Bob", lastname="Johnson", email="bob@example.com", role="member")
            member2.set_password("password123")
            
            db.session.add_all([member1, member2])
            db.session.commit()
            
            # Search for "alice" as member1
            results = MemberService.search_members("alice", member1.id)
            
            # Should not return member1
            assert len(results) == 0
    
    def test_search_excludes_existing_favourites(self, app):
        """Test that search excludes existing favourites."""
        with app.app_context():
            # Create test members
            member1 = Member(firstname="Alice", lastname="Smith", email="alice@example.com", role="member")
            member1.set_password("password123")
            member2 = Member(firstname="Bob", lastname="Johnson", email="bob@example.com", role="member")
            member2.set_password("password123")
            member3 = Member(firstname="Charlie", lastname="Davis", email="charlie@example.com", role="member")
            member3.set_password("password123")
            
            db.session.add_all([member1, member2, member3])
            db.session.commit()
            
            # Add member2 to member1's favourites
            member1.favourites.append(member2)
            db.session.commit()
            
            # Search for members with "example" in email
            results = MemberService.search_members("example", member1.id)
            
            # Should return member3 but not member2 (favourite) or member1 (current)
            assert len(results) == 1
            assert results[0].id == member3.id
    
    def test_search_case_insensitive(self, app):
        """Test that search is case-insensitive."""
        with app.app_context():
            # Create test members
            member1 = Member(firstname="Alice", lastname="Smith", email="alice@example.com", role="member")
            member1.set_password("password123")
            member2 = Member(firstname="Bob", lastname="Johnson", email="bob@example.com", role="member")
            member2.set_password("password123")
            
            db.session.add_all([member1, member2])
            db.session.commit()
            
            # Search with different cases
            results_lower = MemberService.search_members("bob", member1.id)
            results_upper = MemberService.search_members("BOB", member1.id)
            results_mixed = MemberService.search_members("BoB", member1.id)
            
            # All should return the same result
            assert len(results_lower) == 1
            assert len(results_upper) == 1
            assert len(results_mixed) == 1
            assert results_lower[0].id == member2.id
            assert results_upper[0].id == member2.id
            assert results_mixed[0].id == member2.id
    
    def test_search_alphabetical_order(self, app):
        """Test that results are ordered alphabetically by name."""
        with app.app_context():
            # Create test members
            member1 = Member(firstname="Current", lastname="User", email="current@example.com", role="member")
            member1.set_password("password123")
            member2 = Member(firstname="Zoe", lastname="Wilson", email="zoe@example.com", role="member")
            member2.set_password("password123")
            member3 = Member(firstname="Alice", lastname="Brown", email="alice@example.com", role="member")
            member3.set_password("password123")
            member4 = Member(firstname="Bob", lastname="Smith", email="bob@example.com", role="member")
            member4.set_password("password123")
            
            db.session.add_all([member1, member2, member3, member4])
            db.session.commit()
            
            # Search for "example"
            results = MemberService.search_members("example", member1.id)
            
            # Should return in alphabetical order: Alice, Bob, Zoe
            assert len(results) == 3
            assert results[0].name == "Alice Brown"
            assert results[1].name == "Bob Smith"
            assert results[2].name == "Zoe Wilson"
    
    def test_search_empty_query(self, app):
        """Test that empty query returns empty results."""
        with app.app_context():
            # Create test member
            member1 = Member(firstname="Alice", lastname="Smith", email="alice@example.com", role="member")
            member1.set_password("password123")
            
            db.session.add(member1)
            db.session.commit()
            
            # Search with empty query
            results = MemberService.search_members("", member1.id)
            
            # Should return empty list
            assert len(results) == 0
    
    def test_search_whitespace_query(self, app):
        """Test that whitespace-only query returns empty results."""
        with app.app_context():
            # Create test member
            member1 = Member(firstname="Alice", lastname="Smith", email="alice@example.com", role="member")
            member1.set_password("password123")
            
            db.session.add(member1)
            db.session.commit()
            
            # Search with whitespace query
            results = MemberService.search_members("   ", member1.id)
            
            # Should return empty list
            assert len(results) == 0
    
    def test_search_limit_50_members(self, app):
        """Test that search limits results to 50 members."""
        with app.app_context():
            # Create current member
            current = Member(firstname="Current", lastname="User", email="current@example.com", role="member")
            current.set_password("password123")
            db.session.add(current)
            db.session.commit()
            
            # Create 60 test members with "test" in their name
            members = []
            for i in range(60):
                member = Member(
                    firstname="Test",
                    lastname=f"User{i:03d}",
                    email=f"test{i}@example.com",
                    role="member"
                )
                member.set_password("password123")
                members.append(member)
            
            db.session.add_all(members)
            db.session.commit()
            
            # Search for "test"
            results = MemberService.search_members("test", current.id)
            
            # Should return exactly 50 members
            assert len(results) == 50
