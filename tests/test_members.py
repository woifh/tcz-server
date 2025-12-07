"""Property-based tests for member management functionality."""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from app import create_app, db
from app.models import Member


# Hypothesis strategies
valid_emails = st.emails()
valid_passwords = st.text(min_size=8, max_size=50, alphabet=st.characters(min_codepoint=33, max_codepoint=126))
valid_names = st.text(min_size=1, max_size=100, alphabet=st.characters(
    whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'),
    blacklist_characters='\x00'
))


@given(
    original_firstname=valid_names,
    original_lastname=valid_names,
    original_email=valid_emails,
    new_firstname=valid_names,
    new_lastname=valid_names,
    new_email=valid_emails,
    password=valid_passwords
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_18_member_updates_modify_stored_data(original_firstname, original_lastname, original_email, new_firstname, new_lastname, new_email, password):
    """Feature: tennis-club-reservation, Property 18: Member updates modify stored data
    Validates: Requirements 6.2
    
    For any existing member and valid field updates, updating the member should result 
    in the database record reflecting the new values.
    """
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        
        # Create a member with original data
        member = Member(firstname=original_firstname, lastname=original_lastname, email=original_email, role="member")
        member.set_password(password)
        db.session.add(member)
        db.session.commit()
        member_id = member.id
    
    try:
        with app.app_context():
            # Retrieve the member
            member = Member.query.get(member_id)
            
            # Update the member
            member.firstname = new_firstname
            member.lastname = new_lastname
            # Only update email if it's different to avoid unique constraint issues
            if new_email != original_email:
                member.email = new_email
            db.session.commit()
            
            # Retrieve again to verify changes persisted
            updated_member = Member.query.get(member_id)
            
            assert updated_member.firstname == new_firstname, \
                f"Firstname should be updated to {new_firstname}, got {updated_member.firstname}"
            assert updated_member.lastname == new_lastname, \
                f"Lastname should be updated to {new_lastname}, got {updated_member.lastname}"
            
            if new_email != original_email:
                assert updated_member.email == new_email, \
                    f"Email should be updated to {new_email}, got {updated_member.email}"
    
    finally:
        with app.app_context():
            db.session.remove()
            db.drop_all()


@given(
    firstname=valid_names,
    lastname=valid_names,
    email=valid_emails,
    password=valid_passwords
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_19_member_deletion_removes_from_database(firstname, lastname, email, password):
    """Feature: tennis-club-reservation, Property 19: Member deletion removes from database
    Validates: Requirements 6.3
    
    For any existing member, deleting that member should result in the member 
    no longer appearing in database queries.
    """
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        
        # Create a member
        member = Member(firstname=firstname, lastname=lastname, email=email, role="member")
        member.set_password(password)
        db.session.add(member)
        db.session.commit()
        member_id = member.id
        
        # Verify member exists
        assert Member.query.get(member_id) is not None, "Member should exist before deletion"
    
    try:
        with app.app_context():
            # Delete the member
            member = Member.query.get(member_id)
            db.session.delete(member)
            db.session.commit()
            
            # Verify member no longer exists
            deleted_member = Member.query.get(member_id)
            assert deleted_member is None, \
                "Member should not exist after deletion"
            
            # Verify member doesn't appear in queries
            all_members = Member.query.all()
            assert member_id not in [m.id for m in all_members], \
                "Deleted member should not appear in query results"
    
    finally:
        with app.app_context():
            db.session.remove()
            db.drop_all()


@given(
    member1_firstname=valid_names,
    member1_lastname=valid_names,
    member1_email=valid_emails,
    member2_firstname=valid_names,
    member2_lastname=valid_names,
    member2_email=valid_emails,
    password=valid_passwords
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_7_favourites_add_and_remove_operations(
    member1_firstname, member1_lastname, member1_email, member2_firstname, member2_lastname, member2_email, password
):
    """Feature: tennis-club-reservation, Property 7: Favourites add and remove operations
    Validates: Requirements 3.1, 3.2
    
    For any two distinct members A and B, adding B to A's favourites should result 
    in B appearing in A's favourites list; removing B should result in B no longer 
    appearing in the list.
    """
    # Ensure emails are different to avoid unique constraint issues
    if member1_email == member2_email:
        member2_email = "alt_" + member2_email
    
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        
        # Create two members
        member1 = Member(firstname=member1_firstname, lastname=member1_lastname, email=member1_email, role="member")
        member1.set_password(password)
        member2 = Member(firstname=member2_firstname, lastname=member2_lastname, email=member2_email, role="member")
        member2.set_password(password)
        
        db.session.add(member1)
        db.session.add(member2)
        db.session.commit()
        
        member1_id = member1.id
        member2_id = member2.id
    
    try:
        with app.app_context():
            # Test adding favourite
            member1 = Member.query.get(member1_id)
            member2 = Member.query.get(member2_id)
            
            # Initially, member2 should not be in member1's favourites
            assert member2 not in member1.favourites.all(), \
                "Member2 should not be in favourites initially"
            
            # Add member2 to member1's favourites
            member1.favourites.append(member2)
            db.session.commit()
            
            # Verify member2 is now in member1's favourites
            member1 = Member.query.get(member1_id)
            favourites = member1.favourites.all()
            assert member2_id in [f.id for f in favourites], \
                "Member2 should be in favourites after adding"
            
            # Test removing favourite
            member1.favourites.remove(member2)
            db.session.commit()
            
            # Verify member2 is no longer in member1's favourites
            member1 = Member.query.get(member1_id)
            favourites = member1.favourites.all()
            assert member2_id not in [f.id for f in favourites], \
                "Member2 should not be in favourites after removing"
    
    finally:
        with app.app_context():
            db.session.remove()
            db.drop_all()
