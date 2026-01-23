#!/usr/bin/env python3
"""
Import test data: 50 members with profile pics and court reservations.

Usage:
    python scripts/dev/import_test_data.py           # Import test data
    python scripts/dev/import_test_data.py --clean   # Remove existing test data first
    python scripts/dev/import_test_data.py --dry-run # Preview without changes
"""
import os
import sys
import random
import argparse
import urllib.request
from io import BytesIO
from datetime import date, time, timedelta, datetime

# Add project root to path (two levels up from scripts/dev/)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
os.chdir(project_root)

# Load environment before importing app
from dotenv import load_dotenv
load_dotenv()

from PIL import Image
from app import create_app, db
from app.models import Member, Court, Reservation
from app.services.profile_picture_service import ProfilePictureService

# Test email domain - easy to identify and clean up
TEST_EMAIL_DOMAIN = "test.tcz.at"

# German first names with gender
FIRST_NAMES_MALE = [
    "Thomas", "Michael", "Andreas", "Stefan", "Christian",
    "Martin", "Peter", "Wolfgang", "Klaus", "Markus",
    "Daniel", "Alexander", "Florian", "Matthias", "Sebastian",
    "Patrick", "Christoph", "Johannes", "Tobias", "Bernhard",
    "Georg", "Franz", "Josef", "Karl", "Helmut"
]

FIRST_NAMES_FEMALE = [
    "Anna", "Maria", "Elisabeth", "Monika", "Claudia",
    "Sabine", "Petra", "Susanne", "Andrea", "Nicole",
    "Martina", "Karin", "Birgit", "Barbara", "Christine",
    "Gabriele", "Stefanie", "Julia", "Katharina", "Sandra",
    "Cornelia", "Silvia", "Renate", "Ingrid", "Eva"
]

LAST_NAMES = [
    "Gruber", "Huber", "Bauer", "Wagner", "Moser",
    "Mayer", "Hofer", "Steiner", "Berger", "Fuchs",
    "Leitner", "Fischer", "Weber", "Schwarz", "Maier",
    "Schneider", "Reiter", "Mayr", "Schmidt", "Wimmer",
    "Egger", "Brunner", "Lang", "Auer", "Koller",
    "Lehner", "Haas", "Schuster", "Wallner", "Pichler"
]

# Austrian cities with zip codes
CITIES = [
    ("Zellerndorf", "2051"), ("Hollabrunn", "2020"), ("Retz", "2070"),
    ("Pulkau", "3741"), ("Horn", "3580"), ("Krems", "3500"),
    ("Wien", "1010"), ("St. Pölten", "3100"), ("Tulln", "3430"),
    ("Stockerau", "2000"), ("Korneuburg", "2100"), ("Mistelbach", "2130")
]

STREETS = [
    "Hauptstraße", "Bahnhofstraße", "Kirchengasse", "Schulgasse",
    "Wiener Straße", "Feldgasse", "Mühlgasse", "Berggasse",
    "Ringstraße", "Sportplatzweg", "Am Anger", "Kellergasse"
]


def get_random_phone():
    """Generate random Austrian phone number."""
    prefix = random.choice(["0664", "0676", "0699", "0660", "0650"])
    number = "".join([str(random.randint(0, 9)) for _ in range(7)])
    return f"{prefix} {number[:3]} {number[3:]}"


def download_profile_picture(member_id, gender, index, dry_run=False):
    """
    Download a profile picture from randomuser.me.

    Args:
        member_id: Member's UUID
        gender: 'men' or 'women'
        index: 0-99 for unique portraits
        dry_run: If True, don't actually download

    Returns:
        bool: Success status
    """
    if dry_run:
        print(f"    [DRY-RUN] Would download picture for {member_id}")
        return True

    url = f"https://randomuser.me/api/portraits/{gender}/{index % 100}.jpg"

    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            image_data = response.read()

        # Get member to update
        member = Member.query.get(member_id)
        if not member:
            return False

        # Process and save the image
        image = Image.open(BytesIO(image_data))

        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Resize to 400x400 (center crop)
        image = ProfilePictureService._resize_and_crop(image, (400, 400))

        # Save to disk
        folder = ProfilePictureService.get_upload_folder()
        output_path = os.path.join(folder, f"{member_id}.jpg")
        image.save(output_path, 'JPEG', quality=85, optimize=True)

        # Update member record
        member.has_profile_picture = True
        member.profile_picture_version += 1
        db.session.commit()

        return True

    except Exception as e:
        print(f"    Warning: Failed to download picture: {e}")
        return False


def create_random_members(count=50, dry_run=False):
    """
    Create random test members with profile pictures.

    Args:
        count: Number of members to create
        dry_run: If True, don't actually create

    Returns:
        list: Created Member objects (or preview data in dry-run)
    """
    print(f"\nCreating {count} test members...")

    members = []
    used_emails = set()

    # Role distribution: ~90% members, ~6% teamsters, ~4% admins
    # Membership distribution: ~90% full, ~10% sustaining

    male_index = 0
    female_index = 0

    for i in range(count):
        # Random gender
        is_male = random.random() < 0.5

        if is_male:
            firstname = random.choice(FIRST_NAMES_MALE)
            gender = "men"
            male_index += 1
            pic_index = male_index
        else:
            firstname = random.choice(FIRST_NAMES_FEMALE)
            gender = "women"
            female_index += 1
            pic_index = female_index

        lastname = random.choice(LAST_NAMES)

        # Generate unique email
        base_email = f"{firstname.lower()}.{lastname.lower()}"
        email = f"{base_email}@{TEST_EMAIL_DOMAIN}"
        suffix = 1
        while email in used_emails:
            email = f"{base_email}{suffix}@{TEST_EMAIL_DOMAIN}"
            suffix += 1
        used_emails.add(email)

        # Random role
        role_rand = random.random()
        if role_rand < 0.04:
            role = "administrator"
        elif role_rand < 0.10:
            role = "teamster"
        else:
            role = "member"

        # Random membership type
        membership_type = "sustaining" if random.random() < 0.10 else "full"

        # Random address
        city, zip_code = random.choice(CITIES)
        street = f"{random.choice(STREETS)} {random.randint(1, 150)}"
        phone = get_random_phone()

        if dry_run:
            print(f"  [{i+1}/{count}] {firstname} {lastname} <{email}> ({role}, {membership_type})")
            members.append({
                "firstname": firstname,
                "lastname": lastname,
                "email": email,
                "role": role,
                "membership_type": membership_type,
                "gender": gender
            })
        else:
            # Create member
            member = Member(
                firstname=firstname,
                lastname=lastname,
                email=email,
                role=role,
                membership_type=membership_type,
                is_active=True,
                street=street,
                city=city,
                zip_code=zip_code,
                phone=phone,
                fee_paid=random.random() < 0.85,  # 85% have paid
                email_verified=True
            )
            member.set_password("testpassword123")
            db.session.add(member)
            db.session.flush()  # Get the ID

            print(f"  [{i+1}/{count}] {firstname} {lastname} <{email}> ({role}, {membership_type})", end="")

            # Download profile picture
            if download_profile_picture(member.id, gender, pic_index):
                print(" + pic")
            else:
                print(" (no pic)")

            members.append(member)

    if not dry_run:
        db.session.commit()
        print(f"\n  Created {len(members)} members")

    return members


def get_available_slots(target_date, courts):
    """
    Get available slots for a given date.

    Returns list of (court_id, time) tuples that are not booked.
    """
    # Operating hours: 7:00 - 21:00
    all_slots = []
    for court in courts:
        for hour in range(7, 21):
            slot_time = time(hour, 0)
            all_slots.append((court.id, slot_time))

    # Get existing reservations for this date
    existing = Reservation.query.filter(
        Reservation.date == target_date,
        Reservation.status == 'active'
    ).all()

    booked = {(r.court_id, r.start_time) for r in existing}

    return [(c, t) for c, t in all_slots if (c, t) not in booked]


def create_random_reservations(members, dry_run=False):
    """
    Create random reservations for test members.

    - ~70% self-bookings
    - ~30% on-behalf bookings
    - ~10% short-notice (past dates only)
    """
    print("\nCreating reservations...")

    # Filter to full members only (sustaining can't book)
    if dry_run:
        full_members = [m for m in members if m.get("membership_type") == "full"]
    else:
        full_members = [m for m in members if m.membership_type == "full"]

    if not full_members:
        print("  No full members to create reservations for!")
        return

    courts = Court.query.all()
    if not courts:
        print("  No courts found!")
        return

    today = date.today()

    # Date ranges: past 3 days + next 7 days
    past_dates = [today - timedelta(days=i) for i in range(1, 4)]
    future_dates = [today + timedelta(days=i) for i in range(0, 8)]

    reservations_created = 0
    short_notice_count = 0
    on_behalf_count = 0

    # Track reservations per member (max 2 regular future reservations)
    member_future_reservations = {m.id if not dry_run else m["email"]: 0 for m in full_members}

    # Create ~15-20 reservations per day
    all_dates = past_dates + future_dates

    for target_date in all_dates:
        is_past = target_date < today
        available_slots = get_available_slots(target_date, courts)

        if not available_slots:
            continue

        # Random number of reservations for this day
        num_reservations = random.randint(12, 20)
        slots_to_book = random.sample(available_slots, min(num_reservations, len(available_slots)))

        for court_id, slot_time in slots_to_book:
            # Pick random member for the reservation
            booked_for = random.choice(full_members)

            # Respect 2-reservation limit for future dates
            if not is_past and not dry_run:
                if member_future_reservations.get(booked_for.id, 0) >= 2:
                    # Find another member
                    eligible = [m for m in full_members
                               if member_future_reservations.get(m.id, 0) < 2]
                    if not eligible:
                        continue
                    booked_for = random.choice(eligible)

            # Decide if on-behalf booking (~30%)
            is_on_behalf = random.random() < 0.30
            if is_on_behalf:
                booked_by = random.choice(full_members)
                # Make sure it's a different member
                while not dry_run and booked_by.id == booked_for.id and len(full_members) > 1:
                    booked_by = random.choice(full_members)
            else:
                booked_by = booked_for

            # Decide if short-notice (only for past dates, ~30% of past)
            is_short_notice = is_past and random.random() < 0.30

            if dry_run:
                status = "short-notice" if is_short_notice else "active"
                on_behalf_str = f" (by {booked_by['firstname']})" if is_on_behalf else ""
                print(f"  {target_date} {slot_time.strftime('%H:%M')} Court {court_id}: "
                      f"{booked_for['firstname']} {booked_for['lastname']}{on_behalf_str} [{status}]")
            else:
                reservation = Reservation(
                    court_id=court_id,
                    date=target_date,
                    start_time=slot_time,
                    end_time=time(slot_time.hour + 1, 0),
                    booked_for_id=booked_for.id,
                    booked_by_id=booked_by.id,
                    status='active',
                    is_short_notice=is_short_notice
                )
                db.session.add(reservation)

                # Update tracking
                if not is_past and not is_short_notice:
                    member_future_reservations[booked_for.id] = \
                        member_future_reservations.get(booked_for.id, 0) + 1

            reservations_created += 1
            if is_short_notice:
                short_notice_count += 1
            if is_on_behalf:
                on_behalf_count += 1

    if not dry_run:
        db.session.commit()

    print(f"\n  Created {reservations_created} reservations")
    print(f"    - {on_behalf_count} on-behalf bookings")
    print(f"    - {short_notice_count} short-notice bookings")


def clean_test_data():
    """Remove all test data (members with @test.tcz.at email)."""
    print("\nCleaning existing test data...")

    # Find test members
    test_members = Member.query.filter(
        Member.email.like(f"%@{TEST_EMAIL_DOMAIN}")
    ).all()

    if not test_members:
        print("  No test data found")
        return

    member_ids = [m.id for m in test_members]

    # Delete reservations for/by test members
    reservations_deleted = Reservation.query.filter(
        (Reservation.booked_for_id.in_(member_ids)) |
        (Reservation.booked_by_id.in_(member_ids))
    ).delete(synchronize_session=False)

    # Delete profile pictures
    folder = ProfilePictureService.get_upload_folder()
    pics_deleted = 0
    for member_id in member_ids:
        pic_path = os.path.join(folder, f"{member_id}.jpg")
        if os.path.exists(pic_path):
            os.remove(pic_path)
            pics_deleted += 1

    # Delete members
    members_deleted = Member.query.filter(
        Member.email.like(f"%@{TEST_EMAIL_DOMAIN}")
    ).delete(synchronize_session=False)

    db.session.commit()

    print(f"  Deleted {members_deleted} members")
    print(f"  Deleted {reservations_deleted} reservations")
    print(f"  Deleted {pics_deleted} profile pictures")


def check_existing_test_data():
    """Check if test data already exists."""
    count = Member.query.filter(
        Member.email.like(f"%@{TEST_EMAIL_DOMAIN}")
    ).count()
    return count


def main():
    parser = argparse.ArgumentParser(description="Import test data for TCZ")
    parser.add_argument("--clean", action="store_true",
                        help="Remove existing test data first")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview changes without making them")
    parser.add_argument("--count", type=int, default=50,
                        help="Number of members to create (default: 50)")
    args = parser.parse_args()

    app = create_app('development')

    with app.app_context():
        if args.dry_run:
            print("=" * 60)
            print("DRY RUN - No changes will be made")
            print("=" * 60)

        # Check for existing test data
        existing_count = check_existing_test_data()
        if existing_count > 0 and not args.clean and not args.dry_run:
            print(f"\nWarning: {existing_count} test members already exist!")
            print("Use --clean to remove them first, or --dry-run to preview.")
            response = input("Continue anyway? (y/N): ")
            if response.lower() != 'y':
                print("Aborted.")
                return

        # Clean if requested
        if args.clean and not args.dry_run:
            clean_test_data()

        # Create members
        members = create_random_members(count=args.count, dry_run=args.dry_run)

        # Create reservations
        create_random_reservations(members, dry_run=args.dry_run)

        print("\n" + "=" * 60)
        if args.dry_run:
            print("DRY RUN COMPLETE - No changes were made")
        else:
            print("IMPORT COMPLETE")
            print(f"\nTest login credentials:")
            print(f"  Email: any @{TEST_EMAIL_DOMAIN} email")
            print(f"  Password: testpassword123")
        print("=" * 60)


if __name__ == "__main__":
    main()
