"""
API Members Module

Member search and favourites management for mobile apps.
"""

from flask import request, jsonify
from flask_login import current_user
from sqlalchemy import func

from app import db
from app.models import Member, Reservation
from app.services.member_service import MemberService
from app.services.statistics_service import StatisticsService
from app.decorators.auth import jwt_or_session_required
from . import bp


@bp.route('/members/', methods=['GET'])
@jwt_or_session_required
def get_members_list():
    """List all members with booking counts (admin only)."""
    if not current_user.is_admin():
        return jsonify({'error': 'Admin-Berechtigung erforderlich'}), 403

    # Subquery for regular booking count (not short notice)
    regular_count_subq = db.session.query(
        Reservation.booked_for_id,
        func.count(Reservation.id).label('count')
    ).filter(
        Reservation.is_short_notice == False,
        Reservation.status == 'active'
    ).group_by(Reservation.booked_for_id).subquery()

    # Subquery for short notice booking count
    short_notice_subq = db.session.query(
        Reservation.booked_for_id,
        func.count(Reservation.id).label('count')
    ).filter(
        Reservation.is_short_notice == True,
        Reservation.status == 'active'
    ).group_by(Reservation.booked_for_id).subquery()

    # Main query with LEFT JOINs to get members with their booking counts
    results = db.session.query(
        Member,
        func.coalesce(regular_count_subq.c.count, 0).label('total_booking_count'),
        func.coalesce(short_notice_subq.c.count, 0).label('short_notice_count')
    ).outerjoin(
        regular_count_subq, Member.id == regular_count_subq.c.booked_for_id
    ).outerjoin(
        short_notice_subq, Member.id == short_notice_subq.c.booked_for_id
    ).filter(
        Member.is_active == True
    ).order_by(Member.lastname, Member.firstname).all()

    members = []
    for member, total_count, short_notice_count in results:
        member_data = member.to_dict(include_admin_fields=True)
        member_data['total_booking_count'] = total_count
        member_data['short_notice_count'] = short_notice_count
        members.append(member_data)

    return jsonify({
        'members': members,
        'count': len(members)
    })


@bp.route('/members/search', methods=['GET'])
@jwt_or_session_required
def search_members():
    """Search for members by name or email."""
    query = request.args.get('q', '').strip()

    if not query:
        return jsonify({'error': 'Suchbegriff erforderlich'}), 400

    try:
        results = MemberService.search_members(query, current_user.id)

        return jsonify({
            'results': [m.to_dict() for m in results],
            'count': len(results)
        })
    except Exception:
        return jsonify({'error': 'Suchfehler. Bitte versuch es nochmal.'}), 500


# /members/me/favourites routes (convenience alias for current user)
@bp.route('/members/me/favourites', methods=['GET'])
@jwt_or_session_required
def get_my_favourites():
    """Get current user's favourites."""
    try:
        favourites = current_user.favourites.order_by(Member.firstname, Member.lastname).all()

        return jsonify({
            'favourites': [
                fav.to_dict()
                for fav in favourites
                if fav.membership_type == 'full' and fav.is_active
            ]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/members/me/favourites', methods=['POST'])
@jwt_or_session_required
def add_my_favourite():
    """Add a favourite member for current user."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'JSON body required'}), 400

        favourite_id = data.get('favourite_id')
        if not favourite_id:
            return jsonify({'error': 'favourite_id ist erforderlich'}), 400

        favourite = Member.query.get_or_404(favourite_id)

        if favourite.id == current_user.id:
            return jsonify({'error': 'Du kannst dich nicht selbst als Favorit hinzufügen'}), 400

        if favourite in current_user.favourites.all():
            return jsonify({'error': 'Mitglied ist bereits ein Favorit'}), 400

        current_user.favourites.append(favourite)
        db.session.commit()

        MemberService.log_member_operation(
            operation='add_favourite',
            member_id=current_user.id,
            operation_data={
                'member_name': current_user.name,
                'favourite_name': favourite.name,
                'favourite_id': favourite.id
            },
            performed_by_id=current_user.id
        )

        return jsonify({
            'message': 'Favorit erfolgreich hinzugefügt',
            'favourite': favourite.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/members/me/favourites/<fav_id>', methods=['DELETE'])
@jwt_or_session_required
def remove_my_favourite(fav_id):
    """Remove a favourite member for current user."""
    try:
        favourite = Member.query.get_or_404(fav_id)

        if favourite not in current_user.favourites.all():
            return jsonify({'error': 'Mitglied ist kein Favorit'}), 404

        current_user.favourites.remove(favourite)
        db.session.commit()

        MemberService.log_member_operation(
            operation='remove_favourite',
            member_id=current_user.id,
            operation_data={
                'member_name': current_user.name,
                'favourite_name': favourite.name,
                'favourite_id': favourite.id
            },
            performed_by_id=current_user.id
        )

        return jsonify({'message': 'Favorit erfolgreich entfernt'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/members/<id>/favourites', methods=['GET'])
@jwt_or_session_required
def get_favourites(id):
    """Get user's favourites."""
    try:
        member = Member.query.get_or_404(id)

        if member.id != current_user.id:
            return jsonify({'error': 'Du hast keine Berechtigung für diese Aktion'}), 403

        favourites = member.favourites.order_by(Member.firstname, Member.lastname).all()

        return jsonify({
            'favourites': [
                fav.to_dict()
                for fav in favourites
                if fav.membership_type == 'full' and fav.is_active
            ]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/members/<id>/favourites', methods=['POST'])
@jwt_or_session_required
def add_favourite(id):
    """Add a favourite member."""
    try:
        member = Member.query.get_or_404(id)

        if member.id != current_user.id:
            return jsonify({'error': 'Du hast keine Berechtigung für diese Aktion'}), 403

        data = request.get_json()
        if not data:
            return jsonify({'error': 'JSON body required'}), 400

        favourite_id = data.get('favourite_id')
        if not favourite_id:
            return jsonify({'error': 'favourite_id ist erforderlich'}), 400

        favourite = Member.query.get_or_404(favourite_id)

        if favourite.id == member.id:
            return jsonify({'error': 'Du kannst dich nicht selbst als Favorit hinzufügen'}), 400

        if favourite in member.favourites.all():
            return jsonify({'error': 'Mitglied ist bereits ein Favorit'}), 400

        member.favourites.append(favourite)
        db.session.commit()

        # Log the operation
        MemberService.log_member_operation(
            operation='add_favourite',
            member_id=member.id,
            operation_data={
                'member_name': member.name,
                'favourite_name': favourite.name,
                'favourite_id': favourite.id
            },
            performed_by_id=current_user.id
        )

        return jsonify({
            'message': 'Favorit erfolgreich hinzugefügt',
            'favourite': favourite.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/members/<id>/favourites/<fav_id>', methods=['DELETE'])
@jwt_or_session_required
def remove_favourite(id, fav_id):
    """Remove a favourite member."""
    try:
        member = Member.query.get_or_404(id)

        if member.id != current_user.id:
            return jsonify({'error': 'Du hast keine Berechtigung für diese Aktion'}), 403

        favourite = Member.query.get_or_404(fav_id)

        if favourite not in member.favourites.all():
            return jsonify({'error': 'Mitglied ist kein Favorit'}), 404

        member.favourites.remove(favourite)
        db.session.commit()

        # Log the operation
        MemberService.log_member_operation(
            operation='remove_favourite',
            member_id=member.id,
            operation_data={
                'member_name': member.name,
                'favourite_name': favourite.name,
                'favourite_id': favourite.id
            },
            performed_by_id=current_user.id
        )

        return jsonify({'message': 'Favorit erfolgreich entfernt'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ----- Member Profile Routes -----

@bp.route('/members/me', methods=['GET'])
@jwt_or_session_required
def get_current_member():
    """Get current authenticated member's profile."""
    return jsonify({
        'member': current_user.to_dict(include_own_profile_fields=True)
    })


@bp.route('/members/me', methods=['PATCH'])
@jwt_or_session_required
def update_current_member():
    """Update current user's profile."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'JSON body required'}), 400

        # Fields users can update on their own profile
        allowed_fields = ['firstname', 'lastname', 'email', 'phone', 'street', 'city', 'zip_code',
                          'notifications_enabled', 'notify_own_bookings', 'notify_other_bookings',
                          'notify_court_blocked', 'notify_booking_overridden', 'push_notifications_enabled',
                          'push_notify_own_bookings', 'push_notify_other_bookings',
                          'push_notify_court_blocked', 'push_notify_booking_overridden']

        updates = {}
        for field in allowed_fields:
            if field in data:
                updates[field] = data[field]

        member_result, error = MemberService.update_member(
            member_id=current_user.id,
            updates=updates,
            admin_id=None
        )

        if error:
            return jsonify({'error': error}), 400

        return jsonify({
            'message': 'Profil erfolgreich aktualisiert',
            'member': member_result.to_dict(include_own_profile_fields=True)
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/members/<id>', methods=['GET'])
@jwt_or_session_required
def get_member_profile(id):
    """Get member profile (own profile or admin access)."""
    try:
        member = Member.query.get_or_404(id)

        # Users can only view their own profile (admins use /api/admin/members/<id>)
        if member.id != current_user.id and not current_user.is_admin():
            return jsonify({'error': 'Du hast keine Berechtigung für diese Aktion'}), 403

        is_own_profile = (member.id == current_user.id)
        include_admin = current_user.is_admin()
        return jsonify(member.to_dict(
            include_admin_fields=include_admin,
            include_own_profile_fields=is_own_profile
        ))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/members/<id>', methods=['PUT'])
@jwt_or_session_required
def update_member_profile(id):
    """Update member profile."""
    try:
        member = Member.query.get_or_404(id)

        # Users can only update their own profile
        if member.id != current_user.id and not current_user.is_admin():
            return jsonify({'error': 'Du hast keine Berechtigung für diese Aktion'}), 403

        data = request.get_json()
        if not data:
            return jsonify({'error': 'JSON body required'}), 400

        # Fields users can update on their own profile
        allowed_fields = ['firstname', 'lastname', 'email', 'phone', 'street', 'city', 'zip_code',
                          'notifications_enabled', 'notify_own_bookings', 'notify_other_bookings',
                          'notify_court_blocked', 'notify_booking_overridden', 'push_notifications_enabled',
                          'push_notify_own_bookings', 'push_notify_other_bookings',
                          'push_notify_court_blocked', 'push_notify_booking_overridden']

        # Admin-only fields
        admin_fields = ['role', 'membership_type', 'fee_paid', 'is_active']

        updates = {}
        for field in allowed_fields:
            if field in data:
                updates[field] = data[field]

        # Include admin fields if user is admin
        if current_user.is_admin():
            for field in admin_fields:
                if field in data:
                    updates[field] = data[field]

        # Handle password separately
        if 'password' in data and data['password']:
            updates['password'] = data['password']

        member_result, error = MemberService.update_member(
            member_id=id,
            updates=updates,
            admin_id=current_user.id if current_user.is_admin() else None
        )

        if error:
            return jsonify({'error': error}), 400

        return jsonify({
            'message': 'Profil erfolgreich aktualisiert',
            'member': member_result.to_dict(
                include_admin_fields=current_user.is_admin(),
                include_own_profile_fields=True
            )
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/members/', methods=['POST'])
@jwt_or_session_required
def create_member_by_admin():
    """Create a new member (admin only)."""
    if not current_user.is_admin():
        return jsonify({'error': 'Admin-Berechtigung erforderlich'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON body required'}), 400

    try:
        member, error = MemberService.create_member(
            firstname=data.get('firstname'),
            lastname=data.get('lastname'),
            email=data.get('email'),
            password=data.get('password'),
            role=data.get('role', 'member'),
            membership_type=data.get('membership_type', 'full'),
            street=data.get('street'),
            city=data.get('city'),
            zip_code=data.get('zip_code'),
            phone=data.get('phone'),
            admin_id=current_user.id,
            notifications_enabled=bool(data.get('notifications_enabled', True)),
            notify_own_bookings=bool(data.get('notify_own_bookings', True)),
            notify_other_bookings=bool(data.get('notify_other_bookings', True)),
            notify_court_blocked=bool(data.get('notify_court_blocked', True)),
            notify_booking_overridden=bool(data.get('notify_booking_overridden', True))
        )

        if error:
            return jsonify({'error': error}), 400

        return jsonify({
            'message': 'Mitglied erfolgreich erstellt',
            'member': member.to_dict(include_admin_fields=True)
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/members/<id>', methods=['DELETE'])
@jwt_or_session_required
def delete_member_by_admin(id):
    """Delete a member (admin only)."""
    if not current_user.is_admin():
        return jsonify({'error': 'Admin-Berechtigung erforderlich'}), 403

    force = request.args.get('force', 'false').lower() == 'true'

    try:
        success, error = MemberService.delete_member(
            member_id=id,
            admin_id=current_user.id,
            force=force
        )

        if not success:
            return jsonify({'error': error}), 400

        return jsonify({'message': 'Mitglied erfolgreich gelöscht'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/members/<id>/deactivate', methods=['POST'])
@jwt_or_session_required
def deactivate_member_by_admin(id):
    """Deactivate a member (admin only)."""
    if not current_user.is_admin():
        return jsonify({'error': 'Admin-Berechtigung erforderlich'}), 403

    try:
        success, error = MemberService.deactivate_member(
            member_id=id,
            admin_id=current_user.id
        )

        if not success:
            return jsonify({'error': error}), 400

        return jsonify({'message': 'Mitglied erfolgreich deaktiviert'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/members/<id>/reactivate', methods=['POST'])
@jwt_or_session_required
def reactivate_member_by_admin(id):
    """Reactivate a member (admin only)."""
    if not current_user.is_admin():
        return jsonify({'error': 'Admin-Berechtigung erforderlich'}), 403

    try:
        success, error = MemberService.reactivate_member(
            member_id=id,
            admin_id=current_user.id
        )

        if not success:
            return jsonify({'error': error}), 400

        return jsonify({'message': 'Mitglied erfolgreich reaktiviert'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ----- Payment Confirmation Routes -----

@bp.route('/members/me/confirm-payment', methods=['POST'])
@jwt_or_session_required
def confirm_payment():
    """Request payment confirmation for current user."""
    try:
        success, error = MemberService.request_payment_confirmation(current_user.id)

        if not success:
            return jsonify({'error': error}), 400

        return jsonify({
            'message': 'Zahlungsbestätigung wurde angefordert',
            'payment_confirmation_requested': True
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ----- Email Verification Routes -----

@bp.route('/members/<id>/resend-verification', methods=['POST'])
@jwt_or_session_required
def resend_verification_email(id):
    """Resend verification email to a member (admin only)."""
    if not current_user.is_admin():
        return jsonify({'error': 'Admin-Berechtigung erforderlich'}), 403

    try:
        member = Member.query.get_or_404(id)

        if member.email_verified:
            return jsonify({'error': 'E-Mail bereits bestätigt'}), 400

        from app.services.verification_service import VerificationService

        success = VerificationService.send_verification_email(
            member,
            triggered_by='admin_triggered',
            admin_id=current_user.id
        )

        if success:
            return jsonify({'message': 'Bestätigungs-E-Mail wurde gesendet'})
        else:
            return jsonify({'error': 'E-Mail konnte nicht gesendet werden'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ----- Profile Picture Routes -----

# Current user profile picture (must be before /<id>/ routes)
@bp.route('/members/me/profile-picture', methods=['POST'])
@jwt_or_session_required
def upload_my_profile_picture():
    """Upload profile picture for current user."""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Keine Datei ausgewählt'}), 400

        file = request.files['file']

        from app.services.profile_picture_service import ProfilePictureService

        success, error = ProfilePictureService.save_profile_picture(current_user.id, file)

        if not success:
            return jsonify({'error': error}), 400

        db.session.refresh(current_user)

        return jsonify({
            'message': 'Profilbild erfolgreich hochgeladen',
            'has_profile_picture': current_user.has_profile_picture,
            'profile_picture_version': current_user.profile_picture_version
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/members/me/profile-picture', methods=['DELETE'])
@jwt_or_session_required
def delete_my_profile_picture():
    """Delete profile picture for current user."""
    try:
        from app.services.profile_picture_service import ProfilePictureService

        success, error = ProfilePictureService.delete_profile_picture(current_user.id)

        if not success:
            return jsonify({'error': error}), 400

        return jsonify({
            'message': 'Profilbild erfolgreich gelöscht',
            'has_profile_picture': False
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Profile picture by ID (admin or own profile)
@bp.route('/members/<id>/profile-picture', methods=['POST'])
@jwt_or_session_required
def upload_profile_picture(id):
    """Upload profile picture for a member."""
    try:
        member = Member.query.get_or_404(id)

        # Users can only update their own profile picture
        if member.id != current_user.id and not current_user.is_admin():
            return jsonify({'error': 'Du hast keine Berechtigung für diese Aktion'}), 403

        if 'file' not in request.files:
            return jsonify({'error': 'Keine Datei ausgewählt'}), 400

        file = request.files['file']

        from app.services.profile_picture_service import ProfilePictureService

        success, error = ProfilePictureService.save_profile_picture(id, file)

        if not success:
            return jsonify({'error': error}), 400

        # Refresh member data
        db.session.refresh(member)

        return jsonify({
            'message': 'Profilbild erfolgreich hochgeladen',
            'has_profile_picture': member.has_profile_picture,
            'profile_picture_version': member.profile_picture_version
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/members/<id>/profile-picture', methods=['GET'])
@jwt_or_session_required
def get_profile_picture(id):
    """Get profile picture for a member."""
    from flask import Response
    from app.services.profile_picture_service import ProfilePictureService

    try:
        data, error = ProfilePictureService.get_profile_picture_data(id)

        if error:
            return jsonify({'error': error}), 404

        return Response(
            data,
            mimetype='image/jpeg',
            headers={
                'Cache-Control': 'private, max-age=31536000, immutable'
            }
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/members/<id>/profile-picture', methods=['DELETE'])
@jwt_or_session_required
def delete_profile_picture(id):
    """Delete profile picture for a member."""
    try:
        member = Member.query.get_or_404(id)

        # Users can only delete their own profile picture
        if member.id != current_user.id and not current_user.is_admin():
            return jsonify({'error': 'Du hast keine Berechtigung für diese Aktion'}), 403

        from app.services.profile_picture_service import ProfilePictureService

        success, error = ProfilePictureService.delete_profile_picture(id)

        if not success:
            return jsonify({'error': error}), 400

        return jsonify({
            'message': 'Profilbild erfolgreich gelöscht',
            'has_profile_picture': False
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ----- Statistics Routes -----

@bp.route('/members/<id>/statistics', methods=['GET'])
@jwt_or_session_required
def get_member_statistics(id):
    """
    Get statistics for a member.

    Privacy: Users can only view their own statistics.

    Query params:
        year (optional): Filter by year (e.g., 2025). Omit for all-time stats.
    """
    try:
        member = Member.query.get_or_404(id)

        # Users can only view their own statistics
        if member.id != current_user.id:
            return jsonify({'error': 'Du hast keine Berechtigung für diese Aktion'}), 403

        # Parse optional year filter
        year = request.args.get('year')
        if year:
            try:
                year = int(year)
            except ValueError:
                return jsonify({'error': 'Ungültiges Jahr'}), 400

        stats, error = StatisticsService.get_member_statistics(id, year)

        if error:
            return jsonify({'error': error}), 400

        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
