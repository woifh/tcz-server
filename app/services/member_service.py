"""Member service for business logic."""
from datetime import datetime
from sqlalchemy import or_, func
from app import db
from app.models import Member, MemberAuditLog, Reservation, favourites
from app.constants.messages import ErrorMessages, SuccessMessages
from app.constants.roles import UserRole
from app.constants.membership import MembershipType
from app.utils.validators import (
    validate_required_fields,
    validate_email_address,
    validate_string_length,
    validate_choice,
    ValidationError
)
import logging

logger = logging.getLogger(__name__)


class MemberService:
    """Service for managing members with comprehensive CRUD operations."""

    @staticmethod
    def _serialize_for_json(value):
        """Convert date/time objects (including nested structures) to JSON-safe strings."""
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, dict):
            return {k: MemberService._serialize_for_json(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [MemberService._serialize_for_json(v) for v in value]
        return value

    @staticmethod
    def create_member(firstname, lastname, email, password, role='member', membership_type='full',
                      street=None, city=None, zip_code=None, phone=None, admin_id=None,
                      notifications_enabled=True, notify_own_bookings=True,
                      notify_other_bookings=True, notify_court_blocked=True,
                      notify_booking_overridden=True):
        """
        Create a new member with validation.

        Args:
            firstname: Member's first name
            lastname: Member's last name
            email: Member's email address
            password: Plain text password
            role: Member role (default: 'member')
            membership_type: Membership type 'full' or 'sustaining' (default: 'full')
            street: Street address (optional)
            city: City (optional)
            zip_code: ZIP/postal code (optional)
            phone: Phone number (optional)
            admin_id: ID of administrator creating the member
            notifications_enabled: Enable notifications (default: True)
            notify_own_bookings: Notify on own bookings (default: True)
            notify_other_bookings: Notify on other bookings (default: True)
            notify_court_blocked: Notify on court blocked (default: True)
            notify_booking_overridden: Notify on booking overridden (default: True)

        Returns:
            tuple: (Member object or None, error message or None)
        """
        try:
            # Validate required fields
            if not firstname or not firstname.strip():
                return None, ErrorMessages.MEMBER_FIRSTNAME_REQUIRED
            if not lastname or not lastname.strip():
                return None, ErrorMessages.MEMBER_LASTNAME_REQUIRED
            if not email or not email.strip():
                return None, ErrorMessages.MEMBER_EMAIL_REQUIRED
            if not password:
                return None, ErrorMessages.MEMBER_PASSWORD_REQUIRED

            # Validate string lengths
            try:
                firstname = validate_string_length(firstname, 'Vorname', min_length=1, max_length=50)
                lastname = validate_string_length(lastname, 'Nachname', min_length=1, max_length=50)
            except ValidationError as e:
                return None, str(e)

            # Validate email format
            try:
                email = validate_email_address(email, 'E-Mail')
            except ValidationError as e:
                return None, ErrorMessages.MEMBER_INVALID_EMAIL

            # Check for duplicate email
            existing = Member.query.filter(func.lower(Member.email) == func.lower(email)).first()
            if existing:
                return None, ErrorMessages.MEMBER_EMAIL_ALREADY_EXISTS

            # Validate password strength
            if len(password) < 8:
                return None, ErrorMessages.MEMBER_PASSWORD_TOO_SHORT

            # Validate role
            if not UserRole.is_valid(role):
                return None, ErrorMessages.MEMBER_INVALID_ROLE

            # Validate membership type
            if not MembershipType.is_valid(membership_type):
                return None, ErrorMessages.MEMBER_INVALID_MEMBERSHIP_TYPE

            # Create member
            member = Member(
                firstname=firstname.strip(),
                lastname=lastname.strip(),
                email=email.lower(),
                role=role,
                membership_type=membership_type,
                street=street.strip() if street else None,
                city=city.strip() if city else None,
                zip_code=zip_code.strip() if zip_code else None,
                phone=phone.strip() if phone else None,
                notifications_enabled=notifications_enabled,
                notify_own_bookings=notify_own_bookings,
                notify_other_bookings=notify_other_bookings,
                notify_court_blocked=notify_court_blocked,
                notify_booking_overridden=notify_booking_overridden
            )
            member.set_password(password)

            db.session.add(member)
            db.session.flush()  # Get member.id before commit

            # Log the operation
            if admin_id:
                MemberService.log_member_operation(
                    operation='create',
                    member_id=member.id,
                    operation_data={
                        'firstname': firstname,
                        'lastname': lastname,
                        'email': email,
                        'role': role,
                        'membership_type': membership_type,
                        'street': street,
                        'city': city,
                        'zip_code': zip_code,
                        'phone': phone
                    },
                    performed_by_id=admin_id
                )

            db.session.commit()

            logger.info(f"Member created: {member.id} ({email}) by admin {admin_id}")

            return member, None

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create member: {str(e)}")
            return None, f"Fehler beim Erstellen des Mitglieds: {str(e)}"

    @staticmethod
    def get_member(member_id):
        """
        Get a member by ID.

        Args:
            member_id: ID of the member

        Returns:
            tuple: (Member object or None, error message or None)
        """
        try:
            member = Member.query.get(member_id)
            if not member:
                return None, ErrorMessages.MEMBER_NOT_FOUND
            return member, None
        except Exception as e:
            logger.error(f"Failed to get member {member_id}: {str(e)}")
            return None, f"Fehler beim Abrufen des Mitglieds: {str(e)}"

    @staticmethod
    def get_all_members(include_inactive=False):
        """
        Get all members, optionally including inactive ones.

        Args:
            include_inactive: Whether to include deactivated members

        Returns:
            tuple: (List of Member objects or None, error message or None)
        """
        try:
            query = Member.query
            if not include_inactive:
                query = query.filter_by(is_active=True)

            members = query.order_by(Member.lastname, Member.firstname).all()
            return members, None
        except Exception as e:
            logger.error(f"Failed to get all members: {str(e)}")
            return None, f"Fehler beim Abrufen der Mitglieder: {str(e)}"

    @staticmethod
    def update_member(member_id, updates, admin_id=None):
        """
        Update a member with validation.

        Args:
            member_id: ID of the member to update
            updates: Dictionary of fields to update (firstname, lastname, email, password, role)
            admin_id: ID of user performing the update (can be member themselves or admin)

        Returns:
            tuple: (Member object or None, error message or None)
        """
        try:
            member = Member.query.get(member_id)
            if not member:
                return None, ErrorMessages.MEMBER_NOT_FOUND

            changes = {}
            role_changed = False

            # Update firstname
            if 'firstname' in updates:
                try:
                    new_firstname = validate_string_length(
                        updates['firstname'], 'Vorname', min_length=1, max_length=50
                    )
                    if member.firstname != new_firstname:
                        changes['firstname'] = {'old': member.firstname, 'new': new_firstname}
                        member.firstname = new_firstname
                except ValidationError as e:
                    return None, str(e)

            # Update lastname
            if 'lastname' in updates:
                try:
                    new_lastname = validate_string_length(
                        updates['lastname'], 'Nachname', min_length=1, max_length=50
                    )
                    if member.lastname != new_lastname:
                        changes['lastname'] = {'old': member.lastname, 'new': new_lastname}
                        member.lastname = new_lastname
                except ValidationError as e:
                    return None, str(e)

            # Update email
            if 'email' in updates:
                try:
                    new_email = validate_email_address(updates['email'], 'E-Mail').lower()
                    if member.email != new_email:
                        # Check for duplicate
                        existing = Member.query.filter(
                            func.lower(Member.email) == new_email,
                            Member.id != member_id
                        ).first()
                        if existing:
                            return None, ErrorMessages.MEMBER_EMAIL_ALREADY_EXISTS
                        changes['email'] = {'old': member.email, 'new': new_email}
                        member.email = new_email
                except ValidationError:
                    return None, ErrorMessages.MEMBER_INVALID_EMAIL

            # Update password
            if 'password' in updates and updates['password']:
                password = updates['password']
                if len(password) < 8:
                    return None, ErrorMessages.MEMBER_PASSWORD_TOO_SHORT
                member.set_password(password)
                changes['password'] = 'changed'

            # Update role (admin only)
            if 'role' in updates:
                new_role = updates['role']
                if not UserRole.is_valid(new_role):
                    return None, ErrorMessages.MEMBER_INVALID_ROLE
                if member.role != new_role:
                    changes['role'] = {'old': member.role, 'new': new_role}
                    member.role = new_role
                    role_changed = True

            # Update membership type (admin only)
            membership_changed = False
            if 'membership_type' in updates:
                new_membership_type = updates['membership_type']
                if not MembershipType.is_valid(new_membership_type):
                    return None, ErrorMessages.MEMBER_INVALID_MEMBERSHIP_TYPE
                if member.membership_type != new_membership_type:
                    changes['membership_type'] = {'old': member.membership_type, 'new': new_membership_type}
                    member.membership_type = new_membership_type
                    membership_changed = True

            # Update fee_paid (admin only)
            payment_changed = False
            if 'fee_paid' in updates:
                value = updates['fee_paid']
                new_fee_paid = value if isinstance(value, bool) else str(value).lower() in ('true', '1', 'yes')
                if member.fee_paid != new_fee_paid:
                    changes['fee_paid'] = {'old': member.fee_paid, 'new': new_fee_paid}
                    member.fee_paid = new_fee_paid
                    if new_fee_paid:
                        from datetime import date
                        member.fee_paid_date = date.today()
                        member.fee_paid_by_id = admin_id
                    else:
                        member.fee_paid_date = None
                        member.fee_paid_by_id = None
                    payment_changed = True

            # Update address fields
            if 'street' in updates:
                new_street = updates['street'].strip() if updates['street'] else None
                if member.street != new_street:
                    changes['street'] = {'old': member.street, 'new': new_street}
                    member.street = new_street

            if 'city' in updates:
                new_city = updates['city'].strip() if updates['city'] else None
                if member.city != new_city:
                    changes['city'] = {'old': member.city, 'new': new_city}
                    member.city = new_city

            if 'zip_code' in updates:
                new_zip_code = updates['zip_code'].strip() if updates['zip_code'] else None
                if member.zip_code != new_zip_code:
                    changes['zip_code'] = {'old': member.zip_code, 'new': new_zip_code}
                    member.zip_code = new_zip_code

            # Update phone
            if 'phone' in updates:
                new_phone = updates['phone'].strip() if updates['phone'] else None
                if member.phone != new_phone:
                    changes['phone'] = {'old': member.phone, 'new': new_phone}
                    member.phone = new_phone

            # Update notification preferences
            # Helper to convert various boolean representations
            def to_bool(value):
                if isinstance(value, bool):
                    return value
                return str(value).lower() in ('true', '1', 'yes')

            if 'notifications_enabled' in updates:
                new_notifications_enabled = to_bool(updates['notifications_enabled'])
                if member.notifications_enabled != new_notifications_enabled:
                    changes['notifications_enabled'] = {'old': member.notifications_enabled, 'new': new_notifications_enabled}
                    member.notifications_enabled = new_notifications_enabled

            if 'notify_own_bookings' in updates:
                new_notify_own = to_bool(updates['notify_own_bookings'])
                if member.notify_own_bookings != new_notify_own:
                    changes['notify_own_bookings'] = {'old': member.notify_own_bookings, 'new': new_notify_own}
                    member.notify_own_bookings = new_notify_own

            if 'notify_other_bookings' in updates:
                new_notify_other = to_bool(updates['notify_other_bookings'])
                if member.notify_other_bookings != new_notify_other:
                    changes['notify_other_bookings'] = {'old': member.notify_other_bookings, 'new': new_notify_other}
                    member.notify_other_bookings = new_notify_other

            if 'notify_court_blocked' in updates:
                new_notify_court_blocked = to_bool(updates['notify_court_blocked'])
                if member.notify_court_blocked != new_notify_court_blocked:
                    changes['notify_court_blocked'] = {'old': member.notify_court_blocked, 'new': new_notify_court_blocked}
                    member.notify_court_blocked = new_notify_court_blocked

            if 'notify_booking_overridden' in updates:
                new_notify_booking_overridden = to_bool(updates['notify_booking_overridden'])
                if member.notify_booking_overridden != new_notify_booking_overridden:
                    changes['notify_booking_overridden'] = {'old': member.notify_booking_overridden, 'new': new_notify_booking_overridden}
                    member.notify_booking_overridden = new_notify_booking_overridden

            # If no changes, return early
            if not changes:
                return member, None

            db.session.flush()

            # Log the operation
            if admin_id:
                # Determine operation type based on what changed
                if role_changed and len(changes) == 1:
                    operation = 'role_change'
                elif membership_changed and len(changes) == 1:
                    operation = 'membership_change'
                elif payment_changed and len(changes) == 1:
                    operation = 'payment_update'
                else:
                    operation = 'update'
                MemberService.log_member_operation(
                    operation=operation,
                    member_id=member_id,
                    operation_data={
                        'member_name': member.name,
                        'changes': changes
                    },
                    performed_by_id=admin_id
                )

            db.session.commit()

            logger.info(f"Member updated: {member_id} by {admin_id}, changes: {list(changes.keys())}")

            return member, None

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to update member {member_id}: {str(e)}")
            return None, f"Fehler beim Aktualisieren des Mitglieds: {str(e)}"

    @staticmethod
    def delete_member(member_id, admin_id, force=False):
        """
        Delete a member (hard delete or soft delete based on active reservations).

        Args:
            member_id: ID of the member to delete
            admin_id: ID of administrator performing the deletion
            force: If True, perform hard delete even with active reservations (cancels them)

        Returns:
            tuple: (success boolean, error message or None)
        """
        try:
            member = Member.query.get(member_id)
            if not member:
                return False, ErrorMessages.MEMBER_NOT_FOUND

            # Prevent self-deletion
            if member_id == admin_id:
                return False, ErrorMessages.MEMBER_CANNOT_DELETE_SELF

            # Check for active reservations
            active_reservations_count = Reservation.query.filter(
                or_(
                    Reservation.booked_by_id == member_id,
                    Reservation.booked_for_id == member_id
                ),
                Reservation.status == 'active',
                Reservation.date >= datetime.now().date()
            ).count()

            if active_reservations_count > 0 and not force:
                return False, f"{ErrorMessages.MEMBER_HAS_ACTIVE_RESERVATIONS} ({active_reservations_count} Buchungen)"

            # Store member data for audit log before deletion
            member_data = {
                'firstname': member.firstname,
                'lastname': member.lastname,
                'email': member.email,
                'role': member.role,
                'created_at': member.created_at.isoformat() if member.created_at else None,
                'active_reservations_cancelled': active_reservations_count if force else 0
            }

            # If force delete, cancel all active reservations
            if force and active_reservations_count > 0:
                Reservation.query.filter(
                    or_(
                        Reservation.booked_by_id == member_id,
                        Reservation.booked_for_id == member_id
                    ),
                    Reservation.status == 'active'
                ).update({
                    'status': 'cancelled',
                    'reason': 'Mitglied gelöscht durch Administrator'
                }, synchronize_session=False)

            # Log the operation BEFORE deletion
            MemberService.log_member_operation(
                operation='delete',
                member_id=member_id,
                operation_data=member_data,
                performed_by_id=admin_id
            )

            # Delete member (cascade will handle favourites, notifications)
            db.session.delete(member)
            db.session.commit()

            logger.info(f"Member deleted: {member_id} ({member_data['email']}) by admin {admin_id}")

            return True, None

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to delete member {member_id}: {str(e)}")
            return False, f"Fehler beim Löschen des Mitglieds: {str(e)}"

    @staticmethod
    def deactivate_member(member_id, admin_id):
        """
        Soft delete: Deactivate a member account (prevents login).

        Args:
            member_id: ID of the member to deactivate
            admin_id: ID of administrator performing the deactivation

        Returns:
            tuple: (success boolean, error message or None)
        """
        try:
            member = Member.query.get(member_id)
            if not member:
                return False, ErrorMessages.MEMBER_NOT_FOUND

            # Prevent self-deactivation
            if member_id == admin_id:
                return False, ErrorMessages.MEMBER_CANNOT_DEACTIVATE_SELF

            if not member.is_active:
                return False, ErrorMessages.MEMBER_ALREADY_DEACTIVATED

            member.is_active = False
            member.deactivated_at = datetime.utcnow()
            member.deactivated_by_id = admin_id

            # Log the operation
            MemberService.log_member_operation(
                operation='deactivate',
                member_id=member_id,
                operation_data={
                    'firstname': member.firstname,
                    'lastname': member.lastname,
                    'email': member.email,
                    'role': member.role
                },
                performed_by_id=admin_id
            )

            db.session.commit()

            logger.info(f"Member deactivated: {member_id} by admin {admin_id}")

            return True, None

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to deactivate member {member_id}: {str(e)}")
            return False, f"Fehler beim Deaktivieren des Mitglieds: {str(e)}"

    @staticmethod
    def reactivate_member(member_id, admin_id):
        """
        Reactivate a deactivated member account.

        Args:
            member_id: ID of the member to reactivate
            admin_id: ID of administrator performing the reactivation

        Returns:
            tuple: (success boolean, error message or None)
        """
        try:
            member = Member.query.get(member_id)
            if not member:
                return False, ErrorMessages.MEMBER_NOT_FOUND

            if member.is_active:
                return False, ErrorMessages.MEMBER_NOT_DEACTIVATED

            member.is_active = True
            member.deactivated_at = None
            member.deactivated_by_id = None

            # Log the operation
            MemberService.log_member_operation(
                operation='reactivate',
                member_id=member_id,
                operation_data={
                    'firstname': member.firstname,
                    'lastname': member.lastname,
                    'email': member.email,
                    'role': member.role
                },
                performed_by_id=admin_id
            )

            db.session.commit()

            logger.info(f"Member reactivated: {member_id} by admin {admin_id}")

            return True, None

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to reactivate member {member_id}: {str(e)}")
            return False, f"Fehler beim Reaktivieren des Mitglieds: {str(e)}"

    @staticmethod
    def log_member_operation(operation, member_id, operation_data, performed_by_id=None):
        """
        Log a member operation for audit purposes.

        Args:
            operation: Type of operation ('create', 'update', 'delete', 'role_change', 'deactivate', 'reactivate',
                       'add_favourite', 'remove_favourite', 'csv_import', 'annual_fee_reset')
            member_id: ID of the member being operated on (can be 'system' for batch operations)
            operation_data: Dictionary containing operation details
            performed_by_id: ID of user performing the operation (None for system-initiated actions)
        """
        try:
            # Add role to operation data for audit trail
            if operation_data is None:
                operation_data = {}

            if performed_by_id is not None:
                # Get user to include role information
                performer = Member.query.get(performed_by_id)
                if performer:
                    operation_data['performer_role'] = performer.role
            else:
                # System-initiated action
                operation_data['performer_role'] = 'system'

            safe_operation_data = MemberService._serialize_for_json(operation_data) if operation_data else None

            audit_log = MemberAuditLog(
                operation=operation,
                member_id=str(member_id),
                operation_data=safe_operation_data,
                performed_by_id=performed_by_id
            )

            db.session.add(audit_log)
            db.session.commit()

            performer_desc = operation_data.get('performer_role', 'system')
            logger.info(f"Member operation logged: {operation} on member {member_id} by {performer_desc} {performed_by_id or 'system'}")

        except Exception as e:
            logger.error(f"Failed to log member operation: {str(e)}")
            # Don't fail the main operation if logging fails

    @staticmethod
    def get_audit_log(filters=None):
        """
        Get audit log entries with optional filtering.

        Args:
            filters: Dictionary with optional filters (member_id, performed_by_id, operation, date_range)

        Returns:
            list: List of MemberAuditLog objects
        """
        try:
            query = MemberAuditLog.query

            if filters:
                # Filter by member
                if 'member_id' in filters:
                    query = query.filter(MemberAuditLog.member_id == filters['member_id'])

                # Filter by performer
                if 'performed_by_id' in filters:
                    query = query.filter(MemberAuditLog.performed_by_id == filters['performed_by_id'])

                # Filter by operation type
                if 'operation' in filters:
                    query = query.filter(MemberAuditLog.operation == filters['operation'])

                # Filter by date range
                if 'date_range' in filters:
                    start_date, end_date = filters['date_range']
                    query = query.filter(
                        MemberAuditLog.timestamp >= start_date,
                        MemberAuditLog.timestamp <= end_date
                    )

            return query.order_by(MemberAuditLog.timestamp.desc()).all()
        except Exception as e:
            logger.error(f"Failed to get audit log: {str(e)}")
            return []

    @staticmethod
    def search_members(query, current_member_id):
        """
        Search for members by firstname, lastname, or email, excluding current member and existing favourites.

        Args:
            query: Search string (case-insensitive)
            current_member_id: ID of the member performing the search

        Returns:
            list: List of Member objects matching the search criteria
        """
        if not query or not query.strip():
            return []

        # Get IDs of current member's favourites
        favourite_ids_subquery = db.session.query(favourites.c.favourite_id).filter(
            favourites.c.member_id == current_member_id
        ).subquery()

        # Build the search query
        search_pattern = f"%{query.strip()}%"

        results = db.session.query(Member).filter(
            # Search in firstname, lastname, or email (case-insensitive)
            or_(
                func.lower(Member.firstname).like(func.lower(search_pattern)),
                func.lower(Member.lastname).like(func.lower(search_pattern)),
                func.lower(Member.email).like(func.lower(search_pattern))
            ),
            # Exclude current member
            Member.id != current_member_id,
            # Exclude existing favourites
            ~Member.id.in_(favourite_ids_subquery),
            # Only active members
            Member.is_active == True,
            # Only full members (exclude sustaining members who cannot book)
            Member.membership_type == 'full'
        ).order_by(
            # Order alphabetically by lastname, then firstname
            Member.lastname,
            Member.firstname
        ).limit(50).all()  # Limit to 50 members

        return results

    @staticmethod
    def import_members_from_csv(csv_content, admin_id):
        """
        Import members from CSV content.

        CSV format: Firstname;Lastname;Email;ZIP;City;Address;Phone

        For bulk imported members:
        - Email address is used as password
        - Membership type is 'full'
        - Payment status (fee_paid) is False

        Args:
            csv_content: String content of the CSV file
            admin_id: ID of administrator performing the import

        Returns:
            tuple: (dict with results, error message or None)
                   Results dict contains: imported, skipped, errors
        """
        import csv
        from io import StringIO

        results = {
            'imported': 0,
            'skipped': 0,
            'errors': []
        }

        try:
            # Parse CSV content
            reader = csv.reader(StringIO(csv_content), delimiter=';')

            for line_num, row in enumerate(reader, start=1):
                # Skip empty rows
                if not row or all(not cell.strip() for cell in row):
                    continue

                # Validate row has expected number of columns
                if len(row) < 7:
                    results['errors'].append(f"Zeile {line_num}: Nicht genügend Spalten (erwartet: 7, gefunden: {len(row)})")
                    results['skipped'] += 1
                    continue

                # Extract fields (strip whitespace)
                firstname = row[0].strip()
                lastname = row[1].strip()
                email = row[2].strip()
                zip_code = row[3].strip()
                city = row[4].strip()
                street = row[5].strip()
                phone = row[6].strip()

                # Validate required fields
                if not firstname:
                    results['errors'].append(f"Zeile {line_num}: Vorname fehlt")
                    results['skipped'] += 1
                    continue
                if not lastname:
                    results['errors'].append(f"Zeile {line_num}: Nachname fehlt")
                    results['skipped'] += 1
                    continue
                if not email:
                    results['errors'].append(f"Zeile {line_num}: E-Mail fehlt")
                    results['skipped'] += 1
                    continue

                # Use email as password for bulk imports
                password = email

                # Create member with full membership, fee_paid=False
                member, error = MemberService.create_member(
                    firstname=firstname,
                    lastname=lastname,
                    email=email,
                    password=password,
                    role='member',
                    membership_type='full',
                    street=street if street else None,
                    city=city if city else None,
                    zip_code=zip_code if zip_code else None,
                    phone=phone if phone else None,
                    admin_id=admin_id
                )

                if error:
                    results['errors'].append(f"Zeile {line_num} ({email}): {error}")
                    results['skipped'] += 1
                else:
                    results['imported'] += 1

            logger.info(f"CSV import completed by admin {admin_id}: {results['imported']} imported, {results['skipped']} skipped")

            # Log the CSV import operation summary
            if results['imported'] > 0 or results['skipped'] > 0:
                MemberService.log_member_operation(
                    operation='csv_import',
                    member_id='system',
                    operation_data={
                        'imported': results['imported'],
                        'skipped': results['skipped'],
                        'error_count': len(results['errors'])
                    },
                    performed_by_id=admin_id
                )

            return results, None

        except Exception as e:
            logger.error(f"CSV import failed: {str(e)}")
            return None, f"CSV-Import fehlgeschlagen: {str(e)}"

    @staticmethod
    def reset_all_payment_status(admin_id=None):
        """
        Reset payment status for all members (for annual fee reset).
        This is called on January 1st each year.

        Args:
            admin_id: ID of admin performing the reset (None for system/CLI-initiated)

        Returns:
            tuple: (count of members reset, error message or None)
        """
        try:
            # Count members that will be affected
            count = Member.query.filter(Member.fee_paid == True).count()

            if count == 0:
                logger.info("No members with paid status to reset")
                return 0, None

            # Reset all payment statuses
            Member.query.update({
                'fee_paid': False,
                'fee_paid_date': None,
                'fee_paid_by_id': None
            }, synchronize_session=False)

            db.session.commit()

            # Log the operation
            MemberService.log_member_operation(
                operation='annual_fee_reset',
                member_id='system',
                operation_data={
                    'members_reset': count,
                    'year': datetime.now().year
                },
                performed_by_id=admin_id
            )

            logger.info(f"Reset payment status for {count} members (annual reset)")

            return count, None

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to reset payment status: {str(e)}")
            return 0, f"Fehler beim Zurücksetzen der Beitragszahlungen: {str(e)}"
