#!/usr/bin/env python3
"""Test script to verify past booking validation."""

import requests
from datetime import datetime, timedelta

BASE_URL = "http://127.0.0.1:5000"

# Create a session
session = requests.Session()

# Login (you'll need to provide valid credentials)
print("Testing past booking validation...")
print("=" * 50)

# Try to login first
login_data = {
    "email": "admin@example.com",  # Update with actual admin email
    "password": "admin123"  # Update with actual password
}

print("\n1. Logging in...")
response = session.post(f"{BASE_URL}/auth/login", data=login_data, allow_redirects=False)
print(f"Login response: {response.status_code}")

if response.status_code not in [200, 302]:
    print("Login failed. Please update credentials in the script.")
    exit(1)

# Try to create a reservation in the past
yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
past_booking = {
    "court_id": 1,
    "date": yesterday,
    "start_time": "10:00",
    "booked_for_id": 1
}

print(f"\n2. Attempting to create booking for {yesterday} at 10:00...")
response = session.post(
    f"{BASE_URL}/reservations/",
    json=past_booking,
    headers={"Content-Type": "application/json"}
)

print(f"Response status: {response.status_code}")
print(f"Response body: {response.json()}")

if response.status_code == 400:
    error_msg = response.json().get('error', '')
    if "Vergangenheit" in error_msg:
        print("\n✓ SUCCESS: Past booking validation is working!")
        print(f"  Error message: {error_msg}")
    else:
        print(f"\n✗ UNEXPECTED: Got 400 but wrong error message: {error_msg}")
else:
    print(f"\n✗ FAILED: Expected 400, got {response.status_code}")

# Try to create a booking 5 minutes ago
now = datetime.now()
five_min_ago = now - timedelta(minutes=5)
recent_past_booking = {
    "court_id": 2,
    "date": five_min_ago.strftime("%Y-%m-%d"),
    "start_time": five_min_ago.strftime("%H:%M"),
    "booked_for_id": 1
}

print(f"\n3. Attempting to create booking for {five_min_ago.strftime('%Y-%m-%d %H:%M')}...")
response = session.post(
    f"{BASE_URL}/reservations/",
    json=recent_past_booking,
    headers={"Content-Type": "application/json"}
)

print(f"Response status: {response.status_code}")
print(f"Response body: {response.json()}")

if response.status_code == 400:
    error_msg = response.json().get('error', '')
    if "Vergangenheit" in error_msg:
        print("\n✓ SUCCESS: Recent past booking validation is working!")
        print(f"  Error message: {error_msg}")
    else:
        print(f"\n✗ UNEXPECTED: Got 400 but wrong error message: {error_msg}")
else:
    print(f"\n✗ FAILED: Expected 400, got {response.status_code}")

print("\n" + "=" * 50)
print("Test complete!")
