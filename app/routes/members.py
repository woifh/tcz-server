"""Member management routes."""
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Member
from app.services.member_service import MemberService
from app.decorators.auth import admin_required, member_or_admin_required, jwt_or_session_required
from app.constants.messages import SuccessMessages

bp = Blueprint('members', __name__, url_prefix='/members')


@bp.route('/', methods=['GET'])
@login_required
@admin_required
def list_members():
    """List all members page (admin only). Data loaded via API."""
    return render_template('members.html')


@bp.route('/all', methods=['GET'])
@login_required
def get_all_members():
    """Get all members (for favourites dropdown)."""
    members, error = MemberService.get_all_members(include_inactive=False)
    if error:
        return jsonify({'error': error}), 500

    return jsonify({
        'members': [
            {
                'id': m.id,
                'name': m.name,
                'email': m.email
            }
            for m in members
        ]
    }), 200


@bp.route('/search', methods=['GET'])
@jwt_or_session_required
def search_members():
    """Search for members by name or email."""
    try:
        # Get query parameter
        query = request.args.get('q', '').strip()

        # Validate query parameter (minimum 1 character)
        if not query:
            return jsonify({'error': 'Suchbegriff erforderlich'}), 400

        # Call MemberService to search members
        results = MemberService.search_members(query, current_user.id)

        # Return JSON response with results
        return jsonify({
            'results': [
                {
                    'id': member.id,
                    'name': member.name,
                    'email': member.email
                }
                for member in results
            ],
            'count': len(results)
        }), 200

    except Exception as e:
        # Handle errors (500)
        return jsonify({'error': 'Suchfehler. Bitte versuchen Sie es erneut.'}), 500


@bp.route('/favourites', methods=['GET'])
@login_required
def favourites_page():
    """Show favourites management page."""
    return render_template('favourites.html')


@bp.route('/profile', methods=['GET'])
@login_required
def profile_edit():
    """Show profile edit page for current user."""
    return render_template('profile.html', member=current_user)


@bp.route('/', methods=['POST'])
@login_required
@admin_required
def create_member():
    """Create member (admin only)."""
    try:
        data = request.get_json() if request.is_json else request.form

        firstname = data.get('firstname')
        lastname = data.get('lastname')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'member')
        membership_type = data.get('membership_type', 'full')
        street = data.get('street')
        city = data.get('city')
        zip_code = data.get('zip_code')
        phone = data.get('phone')

        # Create member via service
        member, error = MemberService.create_member(
            firstname=firstname,
            lastname=lastname,
            email=email,
            password=password,
            role=role,
            membership_type=membership_type,
            street=street,
            city=city,
            zip_code=zip_code,
            phone=phone,
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
            'id': member.id,
            'name': member.name,
            'email': member.email,
            'role': member.role,
            'membership_type': member.membership_type,
            'message': SuccessMessages.MEMBER_CREATED
        }), 201

    except Exception as e:
        return jsonify({'error': f'Unerwarteter Fehler: {str(e)}'}), 500


@bp.route('/<id>', methods=['GET'])
@login_required
@member_or_admin_required
def get_member(id):
    """Get member details (user can view self, admin can view anyone)."""
    member, error = MemberService.get_member(id)

    if error:
        return jsonify({'error': error}), 404

    # Base response with fields accessible to all authenticated users
    response = {
        'id': member.id,
        'firstname': member.firstname,
        'lastname': member.lastname,
        'name': member.name,
        'email': member.email,
        'street': member.street,
        'city': member.city,
        'zip_code': member.zip_code,
        'phone': member.phone,
        'notifications_enabled': member.notifications_enabled,
        'notify_own_bookings': member.notify_own_bookings,
        'notify_other_bookings': member.notify_other_bookings,
        'notify_court_blocked': member.notify_court_blocked,
        'notify_booking_overridden': member.notify_booking_overridden
    }

    # Add admin-only fields
    if current_user.is_admin():
        response.update({
            'role': member.role,
            'membership_type': member.membership_type,
            'fee_paid': member.fee_paid,
            'is_active': member.is_active,
            'created_at': member.created_at.isoformat() if member.created_at else None
        })

    return jsonify(response), 200


@bp.route('/<id>', methods=['PUT'])
@login_required
def update_member(id):
    """Update member (user can update self, admin can update anyone)."""
    try:
        # Check authorization: user can update self, admin can update anyone
        if id != current_user.id and not current_user.is_admin():
            return jsonify({'error': 'Sie haben keine Berechtigung für diese Aktion'}), 403

        data = request.get_json() if request.is_json else request.form

        # Build updates dictionary
        updates = {}
        if 'firstname' in data:
            updates['firstname'] = data['firstname']
        if 'lastname' in data:
            updates['lastname'] = data['lastname']
        if 'email' in data:
            updates['email'] = data['email']
        if 'password' in data and data['password']:
            updates['password'] = data['password']

        # Only admin can change role
        if 'role' in data and current_user.is_admin():
            updates['role'] = data['role']

        # Only admin can change membership type
        if 'membership_type' in data and current_user.is_admin():
            updates['membership_type'] = data['membership_type']

        # Only admin can change fee_paid status
        if 'fee_paid' in data and current_user.is_admin():
            # Handle string 'true'/'false' or boolean
            fee_paid_value = data['fee_paid']
            if isinstance(fee_paid_value, str):
                updates['fee_paid'] = fee_paid_value.lower() in ('true', '1', 'yes')
            else:
                updates['fee_paid'] = bool(fee_paid_value)

        # Address and phone fields (can be updated by user or admin)
        if 'street' in data:
            updates['street'] = data['street']
        if 'city' in data:
            updates['city'] = data['city']
        if 'zip_code' in data:
            updates['zip_code'] = data['zip_code']
        if 'phone' in data:
            updates['phone'] = data['phone']

        # Notification preferences (can be updated by user or admin)
        if 'notifications_enabled' in data:
            updates['notifications_enabled'] = bool(data['notifications_enabled'])
        if 'notify_own_bookings' in data:
            updates['notify_own_bookings'] = bool(data['notify_own_bookings'])
        if 'notify_other_bookings' in data:
            updates['notify_other_bookings'] = bool(data['notify_other_bookings'])
        if 'notify_court_blocked' in data:
            updates['notify_court_blocked'] = bool(data['notify_court_blocked'])
        if 'notify_booking_overridden' in data:
            updates['notify_booking_overridden'] = bool(data['notify_booking_overridden'])

        # Update member via service
        member, error = MemberService.update_member(
            member_id=id,
            updates=updates,
            admin_id=current_user.id
        )

        if error:
            return jsonify({'error': error}), 400

        return jsonify({
            'id': member.id,
            'name': member.name,
            'email': member.email,
            'role': member.role,
            'membership_type': member.membership_type,
            'fee_paid': member.fee_paid,
            'message': SuccessMessages.MEMBER_UPDATED
        }), 200

    except Exception as e:
        return jsonify({'error': f'Unerwarteter Fehler: {str(e)}'}), 500


@bp.route('/<id>', methods=['DELETE'])
@login_required
@admin_required
def delete_member(id):
    """Delete member (admin only)."""
    try:
        force = request.args.get('force', 'false').lower() == 'true'

        success, error = MemberService.delete_member(
            member_id=id,
            admin_id=current_user.id,
            force=force
        )

        if not success:
            return jsonify({'error': error}), 400

        return jsonify({'message': SuccessMessages.MEMBER_DELETED}), 200

    except Exception as e:
        return jsonify({'error': f'Unerwarteter Fehler: {str(e)}'}), 500


@bp.route('/<id>/deactivate', methods=['POST'])
@login_required
@admin_required
def deactivate_member(id):
    """Deactivate member account (admin only, soft delete)."""
    try:
        success, error = MemberService.deactivate_member(
            member_id=id,
            admin_id=current_user.id
        )

        if not success:
            return jsonify({'error': error}), 400

        return jsonify({'message': SuccessMessages.MEMBER_DEACTIVATED}), 200

    except Exception as e:
        return jsonify({'error': f'Unerwarteter Fehler: {str(e)}'}), 500


@bp.route('/<id>/reactivate', methods=['POST'])
@login_required
@admin_required
def reactivate_member(id):
    """Reactivate member account (admin only)."""
    try:
        success, error = MemberService.reactivate_member(
            member_id=id,
            admin_id=current_user.id
        )

        if not success:
            return jsonify({'error': error}), 400

        return jsonify({'message': SuccessMessages.MEMBER_REACTIVATED}), 200

    except Exception as e:
        return jsonify({'error': f'Unerwarteter Fehler: {str(e)}'}), 500


@bp.route('/<id>/favourites', methods=['POST'])
@jwt_or_session_required
def add_favourite(id):
    """Add favourite (user can add to own favourites)."""
    try:
        member = Member.query.get_or_404(id)

        # Check authorization: user can only modify own favourites
        if member.id != current_user.id:
            return jsonify({'error': 'Sie haben keine Berechtigung für diese Aktion'}), 403

        data = request.get_json() if request.is_json else request.form
        favourite_id = data.get('favourite_id')

        if not favourite_id:
            return jsonify({'error': 'favourite_id ist erforderlich'}), 400

        favourite = Member.query.get_or_404(favourite_id)

        # Prevent adding self as favourite
        if favourite.id == member.id:
            return jsonify({'error': 'Sie können sich nicht selbst als Favorit hinzufügen'}), 400

        # Check if already a favourite
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
            'favourite': {
                'id': favourite.id,
                'name': favourite.name,
                'email': favourite.email
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/<id>/favourites', methods=['GET'])
@jwt_or_session_required
def get_favourites(id):
    """Get user's favourites."""
    try:
        member = Member.query.get_or_404(id)

        # Check authorization: user can only view own favourites
        if member.id != current_user.id:
            return jsonify({'error': 'Sie haben keine Berechtigung für diese Aktion'}), 403

        favourites = member.favourites.all()

        # Only return full members (exclude sustaining members who cannot book)
        return jsonify({
            'favourites': [
                {
                    'id': fav.id,
                    'name': fav.name,
                    'email': fav.email
                }
                for fav in favourites
                if fav.membership_type == 'full' and fav.is_active
            ]
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/<id>/favourites/<fav_id>', methods=['DELETE'])
@jwt_or_session_required
def remove_favourite(id, fav_id):
    """Remove favourite (user can remove from own favourites)."""
    try:
        member = Member.query.get_or_404(id)

        # Check authorization: user can only modify own favourites
        if member.id != current_user.id:
            return jsonify({'error': 'Sie haben keine Berechtigung für diese Aktion'}), 403

        favourite = Member.query.get_or_404(fav_id)

        # Check if is a favourite
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

        return jsonify({'message': 'Favorit erfolgreich entfernt'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
