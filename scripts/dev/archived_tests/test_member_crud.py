"""Test Member CRUD operations with the new MemberService."""
import requests
import json

BASE_URL = "http://localhost:5050"

# Test credentials
ADMIN_EMAIL = "admin@test.com"
ADMIN_PASSWORD = "admin123"

def print_section(title):
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f"{title}")
    print('='*60)

def login(email, password):
    """Login and return session."""
    session = requests.Session()

    # Get login page first to get any CSRF tokens
    response = session.get(f"{BASE_URL}/auth/login")

    # Login
    response = session.post(
        f"{BASE_URL}/auth/login",
        data={'email': email, 'password': password},
        allow_redirects=False
    )

    if response.status_code in [200, 302]:
        print(f"✅ Logged in as {email}")
        return session
    else:
        print(f"❌ Login failed: {response.status_code}")
        return None

def test_create_member(session):
    """Test creating a new member."""
    print_section("TEST 1: Create Member")

    new_member = {
        'firstname': 'John',
        'lastname': 'Doe',
        'email': 'john.doe@test.com',
        'password': 'password123',
        'role': 'member'
    }

    response = session.post(
        f"{BASE_URL}/members/",
        json=new_member
    )

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code == 201:
        print("✅ Member created successfully")
        return response.json()['id']
    else:
        print("❌ Failed to create member")
        return None

def test_create_duplicate_email(session):
    """Test creating member with duplicate email (should fail)."""
    print_section("TEST 2: Create Member with Duplicate Email (Should Fail)")

    duplicate_member = {
        'firstname': 'Jane',
        'lastname': 'Doe',
        'email': 'john.doe@test.com',  # Same as previous
        'password': 'password123',
        'role': 'member'
    }

    response = session.post(
        f"{BASE_URL}/members/",
        json=duplicate_member
    )

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code == 400 and 'bereits verwendet' in response.json().get('error', ''):
        print("✅ Correctly rejected duplicate email")
    else:
        print("❌ Should have rejected duplicate email")

def test_create_short_password(session):
    """Test creating member with short password (should fail)."""
    print_section("TEST 3: Create Member with Short Password (Should Fail)")

    weak_member = {
        'firstname': 'Weak',
        'lastname': 'Password',
        'email': 'weak@test.com',
        'password': 'short',  # Less than 8 characters
        'role': 'member'
    }

    response = session.post(
        f"{BASE_URL}/members/",
        json=weak_member
    )

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code == 400 and '8 Zeichen' in response.json().get('error', ''):
        print("✅ Correctly rejected short password")
    else:
        print("❌ Should have rejected short password")

def test_get_member(session, member_id):
    """Test getting member details."""
    print_section("TEST 4: Get Member Details")

    response = session.get(f"{BASE_URL}/members/{member_id}")

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code == 200:
        print("✅ Successfully retrieved member details")
    else:
        print("❌ Failed to get member details")

def test_update_member(session, member_id):
    """Test updating member details."""
    print_section("TEST 5: Update Member")

    updates = {
        'firstname': 'Johnny',
        'lastname': 'Updated'
    }

    response = session.put(
        f"{BASE_URL}/members/{member_id}",
        json=updates
    )

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code == 200:
        print("✅ Member updated successfully")
    else:
        print("❌ Failed to update member")

def test_update_member_role(session, member_id):
    """Test updating member role (admin only)."""
    print_section("TEST 6: Update Member Role")

    updates = {
        'role': 'teamster'
    }

    response = session.put(
        f"{BASE_URL}/members/{member_id}",
        json=updates
    )

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code == 200 and response.json()['role'] == 'teamster':
        print("✅ Member role updated successfully")
    else:
        print("❌ Failed to update member role")

def test_deactivate_member(session, member_id):
    """Test deactivating member (soft delete)."""
    print_section("TEST 7: Deactivate Member")

    response = session.post(f"{BASE_URL}/members/{member_id}/deactivate")

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code == 200:
        print("✅ Member deactivated successfully")
    else:
        print("❌ Failed to deactivate member")

def test_login_deactivated(member_email):
    """Test logging in with deactivated account (should fail)."""
    print_section("TEST 8: Login with Deactivated Account (Should Fail)")

    session = requests.Session()

    response = session.post(
        f"{BASE_URL}/auth/login",
        data={'email': member_email, 'password': 'password123'},
        allow_redirects=True
    )

    print(f"Status Code: {response.status_code}")

    if 'deaktiviert' in response.text:
        print("✅ Correctly prevented deactivated account login")
    else:
        print("❌ Should have prevented deactivated account login")

def test_reactivate_member(session, member_id):
    """Test reactivating member."""
    print_section("TEST 9: Reactivate Member")

    response = session.post(f"{BASE_URL}/members/{member_id}/reactivate")

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code == 200:
        print("✅ Member reactivated successfully")
    else:
        print("❌ Failed to reactivate member")

def test_delete_member(session, member_id):
    """Test deleting member (hard delete)."""
    print_section("TEST 10: Delete Member")

    response = session.delete(f"{BASE_URL}/members/{member_id}")

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code == 200:
        print("✅ Member deleted successfully")
    else:
        print("❌ Failed to delete member")

def test_search_members(session):
    """Test member search functionality."""
    print_section("TEST 11: Search Members")

    response = session.get(f"{BASE_URL}/members/search?q=admin")

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code == 200:
        print("✅ Search executed successfully")
    else:
        print("❌ Search failed")

def run_all_tests():
    """Run all tests in sequence."""
    print("\n" + "="*60)
    print("MEMBER CRUD OPERATIONS TEST SUITE")
    print("="*60)

    # Login as admin
    session = login(ADMIN_EMAIL, ADMIN_PASSWORD)
    if not session:
        print("❌ Cannot proceed without admin session")
        return

    # Run tests
    member_id = test_create_member(session)
    if not member_id:
        print("❌ Cannot proceed without created member")
        return

    test_create_duplicate_email(session)
    test_create_short_password(session)
    test_get_member(session, member_id)
    test_update_member(session, member_id)
    test_update_member_role(session, member_id)
    test_deactivate_member(session, member_id)
    test_login_deactivated('john.doe@test.com')
    test_reactivate_member(session, member_id)
    test_delete_member(session, member_id)
    test_search_members(session)

    print_section("TEST SUITE COMPLETED")
    print("All CRUD operations have been tested!")

if __name__ == "__main__":
    run_all_tests()
