"""Member management routes."""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models import Member

bp = Blueprint('members', __name__, url_prefix='/members')


def admin_required(f):
    """Decorator to require admin role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Sie haben keine Berechtigung für diese Aktion', 'error')
            return redirect(url_for('dashboard.index')), 403
        return f(*args, **kwargs)
    return decorated_function


@bp.route('/', methods=['GET'])
@login_required
@admin_required
def list_members():
    """List all members (admin only)."""
    members = Member.query.order_by(Member.name).all()
    return render_template('members.html', members=members)


@bp.route('/', methods=['POST'])
@login_required
@admin_required
def create_member():
    """Create member (admin only)."""
    try:
        data = request.get_json() if request.is_json else request.form
        
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'member')
        
        # Validate required fields
        if not name or not email or not password:
            return jsonify({'error': 'Name, E-Mail und Passwort sind erforderlich'}), 400
        
        # Check if email already exists
        if Member.query.filter_by(email=email).first():
            return jsonify({'error': 'E-Mail-Adresse wird bereits verwendet'}), 400
        
        # Create new member
        member = Member(name=name, email=email, role=role)
        member.set_password(password)
        
        db.session.add(member)
        db.session.commit()
        
        return jsonify({
            'id': member.id,
            'name': member.name,
            'email': member.email,
            'role': member.role,
            'message': 'Mitglied erfolgreich erstellt'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:id>', methods=['PUT'])
@login_required
def update_member(id):
    """Update member (user can update self, admin can update anyone)."""
    try:
        member = Member.query.get_or_404(id)
        
        # Check authorization: user can update self, admin can update anyone
        if member.id != current_user.id and not current_user.is_admin():
            return jsonify({'error': 'Sie haben keine Berechtigung für diese Aktion'}), 403
        
        data = request.get_json() if request.is_json else request.form
        
        # Update allowed fields
        if 'name' in data:
            member.name = data['name']
        if 'email' in data:
            # Check if new email is already taken by another user
            existing = Member.query.filter_by(email=data['email']).first()
            if existing and existing.id != member.id:
                return jsonify({'error': 'E-Mail-Adresse wird bereits verwendet'}), 400
            member.email = data['email']
        if 'password' in data and data['password']:
            member.set_password(data['password'])
        
        # Only admin can change role
        if 'role' in data and current_user.is_admin():
            member.role = data['role']
        
        db.session.commit()
        
        return jsonify({
            'id': member.id,
            'name': member.name,
            'email': member.email,
            'role': member.role,
            'message': 'Mitglied erfolgreich aktualisiert'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:id>', methods=['DELETE'])
@login_required
@admin_required
def delete_member(id):
    """Delete member (admin only)."""
    try:
        member = Member.query.get_or_404(id)
        
        # Prevent deleting self
        if member.id == current_user.id:
            return jsonify({'error': 'Sie können sich nicht selbst löschen'}), 400
        
        db.session.delete(member)
        db.session.commit()
        
        return jsonify({'message': 'Mitglied erfolgreich gelöscht'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:id>/favourites', methods=['POST'])
@login_required
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


@bp.route('/<int:id>/favourites/<int:fav_id>', methods=['DELETE'])
@login_required
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
        
        return jsonify({'message': 'Favorit erfolgreich entfernt'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
