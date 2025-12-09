#!/usr/bin/env python3
"""
Script to delete all reservation entries from the database.
This is useful for testing and development purposes.

⚠️  WARNING: This will permanently delete ALL reservations!
"""

import sys
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app import create_app
from app.models import Reservation
from app import db

def show_reservation_summary():
    """Show a summary of current reservations before deletion."""
    app = create_app()
    
    with app.app_context():
        total_reservations = Reservation.query.count()
        active_reservations = Reservation.query.filter_by(status='active').count()
        cancelled_reservations = Reservation.query.filter_by(status='cancelled').count()
        short_notice_reservations = Reservation.query.filter_by(is_short_notice=True).count()
        
        print("📊 Current Reservation Summary:")
        print(f"   Total reservations: {total_reservations}")
        print(f"   Active reservations: {active_reservations}")
        print(f"   Cancelled reservations: {cancelled_reservations}")
        print(f"   Short notice reservations: {short_notice_reservations}")
        print()
        
        if total_reservations > 0:
            print("📅 Recent reservations:")
            recent = Reservation.query.order_by(Reservation.created_at.desc()).limit(5).all()
            for res in recent:
                status_emoji = "✅" if res.status == 'active' else "❌"
                short_notice_emoji = "🟠" if res.is_short_notice else "🔴"
                print(f"   {status_emoji} {short_notice_emoji} Court {res.court.number} - {res.date} {res.start_time} ({res.status})")
        
        return total_reservations

def delete_all_reservations():
    """Delete all reservations from the database."""
    app = create_app()
    
    with app.app_context():
        try:
            # Get count before deletion
            count = Reservation.query.count()
            
            if count == 0:
                print("✅ No reservations found to delete.")
                return
            
            # Delete all reservations
            deleted_count = Reservation.query.delete()
            db.session.commit()
            
            print(f"✅ Successfully deleted {deleted_count} reservations from the database.")
            print("🔄 Database has been cleaned.")
            
        except Exception as e:
            print(f"❌ Error deleting reservations: {e}")
            db.session.rollback()
            sys.exit(1)

def delete_by_status(status):
    """Delete reservations by status (active, cancelled, etc.)."""
    app = create_app()
    
    with app.app_context():
        try:
            # Get count before deletion
            count = Reservation.query.filter_by(status=status).count()
            
            if count == 0:
                print(f"✅ No {status} reservations found to delete.")
                return
            
            # Delete reservations with specific status
            deleted_count = Reservation.query.filter_by(status=status).delete()
            db.session.commit()
            
            print(f"✅ Successfully deleted {deleted_count} {status} reservations from the database.")
            
        except Exception as e:
            print(f"❌ Error deleting {status} reservations: {e}")
            db.session.rollback()
            sys.exit(1)

def delete_old_reservations(days_old=30):
    """Delete reservations older than specified days."""
    app = create_app()
    
    with app.app_context():
        try:
            from datetime import date, timedelta
            cutoff_date = date.today() - timedelta(days=days_old)
            
            # Get count before deletion
            count = Reservation.query.filter(Reservation.date < cutoff_date).count()
            
            if count == 0:
                print(f"✅ No reservations older than {days_old} days found to delete.")
                return
            
            # Delete old reservations
            deleted_count = Reservation.query.filter(Reservation.date < cutoff_date).delete()
            db.session.commit()
            
            print(f"✅ Successfully deleted {deleted_count} reservations older than {days_old} days.")
            
        except Exception as e:
            print(f"❌ Error deleting old reservations: {e}")
            db.session.rollback()
            sys.exit(1)

def main():
    """Main function with interactive menu."""
    print("🗑️  Reservation Deletion Script")
    print("=" * 50)
    print()
    
    # Show current state
    total_count = show_reservation_summary()
    
    if total_count == 0:
        print("✅ No reservations to delete. Exiting.")
        return
    
    print()
    print("⚠️  WARNING: This action cannot be undone!")
    print()
    print("Choose deletion option:")
    print("1. Delete ALL reservations (everything)")
    print("2. Delete only ACTIVE reservations")
    print("3. Delete only CANCELLED reservations")
    print("4. Delete reservations older than 30 days")
    print("5. Delete reservations older than 7 days")
    print("6. Cancel (exit without deleting)")
    print()
    
    while True:
        choice = input("Enter your choice (1-6): ").strip()
        
        if choice == "6":
            print("✅ Operation cancelled. No reservations were deleted.")
            return
        
        if choice in ["1", "2", "3", "4", "5"]:
            break
        
        print("❌ Invalid choice. Please enter 1-6.")
    
    # Confirm the action
    print()
    if choice == "1":
        action_desc = "delete ALL reservations"
    elif choice == "2":
        action_desc = "delete all ACTIVE reservations"
    elif choice == "3":
        action_desc = "delete all CANCELLED reservations"
    elif choice == "4":
        action_desc = "delete reservations older than 30 days"
    elif choice == "5":
        action_desc = "delete reservations older than 7 days"
    
    print(f"🚨 You are about to {action_desc}.")
    print("This action CANNOT be undone!")
    print()
    
    confirmation = input("Type 'DELETE' (in capital letters) to confirm: ").strip()
    
    if confirmation != "DELETE":
        print("✅ Operation cancelled. Confirmation text did not match.")
        return
    
    print()
    print("🔄 Processing deletion...")
    
    # Execute the chosen action
    if choice == "1":
        delete_all_reservations()
    elif choice == "2":
        delete_by_status("active")
    elif choice == "3":
        delete_by_status("cancelled")
    elif choice == "4":
        delete_old_reservations(30)
    elif choice == "5":
        delete_old_reservations(7)
    
    print()
    print("🎉 Deletion completed successfully!")
    print("💡 You can now create fresh test reservations to test the short notice feature.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✅ Operation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)