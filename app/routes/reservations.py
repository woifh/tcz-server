"""Reservation routes."""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date
from app import db, limiter
from app.models import Reservation
from app.services.reservation_service import ReservationService
from app.utils.validators import (
    ValidationError,
    validate_date_format,
    validate_time_format,
    validate_integer
)

bp = Blueprint('reservations', __name__, url_prefix='/reservations')


@bp.route('/', methods=['GET'])
@login_required
def list_reservations():
    """List user's reservations or all reservations for a date."""
    date_str = request.args.get('date')
    
    if date_str:
        # List all reservations for a specific date (for admin/viewing)
        try:
            query_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            reservations = ReservationService.get_reservations_by_date(query_date)
            
            # Format for JSON response (only if explicitly requested via query param or content type)
            if request.args.get('format') == 'json' or (request.is_json and request.accept_mimetypes.best == 'application/json'):
                return jsonify({
                    'date': date_str,
                    'reservations': [
                        {
                            'id': r.id,
                            'court_id': r.court_id,
                            'court_number': r.court.number,
                            'start_time': r.start_time.strftime('%H:%M'),
                            'end_time': r.end_time.strftime('%H:%M'),
                            'booked_for': r.booked_for.name,
                            'booked_for_id': r.booked_for_id,
                            'booked_by': r.booked_by.name,
                            'booked_by_id': r.booked_by_id,
                            'status': r.status,
                            'is_short_notice': r.is_short_notice
                        }
                        for r in reservations
                    ]
                })
            
            return render_template('reservations.html', reservations=reservations, date=query_date)
        except ValueError:
            flash('Ungültiges Datumsformat', 'error')
            return redirect(url_for('reservations.list_reservations'))
    else:
        # List user's own reservations
        reservations = ReservationService.get_member_active_reservations(current_user.id)
        
        # Only return JSON if explicitly requested
        if request.args.get('format') == 'json' or (request.is_json and request.accept_mimetypes.best == 'application/json'):
            return jsonify({
                'reservations': [
                    {
                        'id': r.id,
                        'court_id': r.court_id,
                        'court_number': r.court.number,
                        'date': r.date.isoformat(),
                        'start_time': r.start_time.strftime('%H:%M'),
                        'end_time': r.end_time.strftime('%H:%M'),
                        'booked_for': r.booked_for.name,
                        'booked_for_id': r.booked_for_id,
                        'booked_by': r.booked_by.name,
                        'booked_by_id': r.booked_by_id,
                        'status': r.status,
                        'is_short_notice': r.is_short_notice
                    }
                    for r in reservations
                ]
            })
        
        return render_template('reservations.html', reservations=reservations)


@bp.route('/', methods=['POST'])
@login_required
@limiter.limit("10 per minute")
def create_reservation():
    """Create a new reservation."""
    try:
        data = request.get_json() if request.is_json else request.form
        
        # Validate input data
        try:
            court_id = validate_integer(data.get('court_id'), 'court_id', min_value=1, max_value=6)
            reservation_date = validate_date_format(data.get('date'), 'date')
            start_time = validate_time_format(data.get('start_time'), 'start_time')
            booked_for_id = validate_integer(
                data.get('booked_for_id', current_user.id), 
                'booked_for_id', 
                min_value=1
            )
        except ValidationError as e:
            if request.is_json:
                return jsonify({'error': str(e)}), 400
            flash(str(e), 'error')
            return redirect(url_for('dashboard.index'))
        
        # Create reservation
        reservation, error = ReservationService.create_reservation(
            court_id=court_id,
            date=reservation_date,
            start_time=start_time,
            booked_for_id=booked_for_id,
            booked_by_id=current_user.id
        )
        
        if error:
            if request.is_json:
                return jsonify({'error': error}), 400
            flash(error, 'error')
            return redirect(url_for('dashboard.index'))
        else:
            # Determine success message based on booking type
            success_message = 'Kurzfristige Buchung erfolgreich erstellt!' if reservation.is_short_notice else 'Buchung erfolgreich erstellt!'
            
            if request.is_json:
                return jsonify({
                    'id': reservation.id,
                    'message': success_message,
                    'reservation': {
                        'id': reservation.id,
                        'court_id': reservation.court_id,
                        'date': reservation.date.isoformat(),
                        'start_time': reservation.start_time.strftime('%H:%M'),
                        'end_time': reservation.end_time.strftime('%H:%M'),
                        'is_short_notice': reservation.is_short_notice
                    }
                }), 201
            flash(success_message, 'success')
            return redirect(url_for('reservations.list_reservations'))
    
    except Exception as e:
        if request.is_json:
            return jsonify({'error': 'Ein Fehler ist aufgetreten'}), 500
        flash('Ein Fehler ist aufgetreten', 'error')
        return redirect(url_for('dashboard.index'))


@bp.route('/<int:id>', methods=['PUT'])
@login_required
def update_reservation(id):
    """Update a reservation."""
    try:
        reservation = Reservation.query.get_or_404(id)
        
        # Check authorization: only booked_for or booked_by can modify
        if (reservation.booked_for_id != current_user.id and 
            reservation.booked_by_id != current_user.id):
            return jsonify({'error': 'Sie haben keine Berechtigung für diese Aktion'}), 403
        
        data = request.get_json() if request.is_json else request.form
        
        # Prepare update data
        updates = {}
        if 'court_id' in data:
            updates['court_id'] = int(data['court_id'])
        if 'date' in data:
            updates['date'] = datetime.strptime(data['date'], '%Y-%m-%d').date()
        if 'start_time' in data:
            updates['start_time'] = datetime.strptime(data['start_time'], '%H:%M').time()
        
        # Update reservation
        updated_reservation, error = ReservationService.update_reservation(id, **updates)
        
        if error:
            return jsonify({'error': error}), 400
        
        return jsonify({
            'message': 'Buchung erfolgreich aktualisiert',
            'reservation': {
                'id': updated_reservation.id,
                'court_id': updated_reservation.court_id,
                'date': updated_reservation.date.isoformat(),
                'start_time': updated_reservation.start_time.strftime('%H:%M'),
                'end_time': updated_reservation.end_time.strftime('%H:%M')
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:id>', methods=['DELETE'])
@login_required
def delete_reservation(id):
    """Cancel a reservation."""
    try:
        reservation = Reservation.query.get_or_404(id)
        
        # Check authorization: only booked_for or booked_by can cancel
        if (reservation.booked_for_id != current_user.id and 
            reservation.booked_by_id != current_user.id):
            return jsonify({'error': 'Sie haben keine Berechtigung für diese Aktion'}), 403
        
        success, error = ReservationService.cancel_reservation(id)
        
        if error:
            return jsonify({'error': error}), 400
        
        return jsonify({'message': 'Buchung erfolgreich storniert'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:id>/cancel', methods=['POST'])
@login_required
def cancel_reservation_form(id):
    """Cancel a reservation (form submission)."""
    try:
        reservation = Reservation.query.get_or_404(id)
        
        # Check authorization: only booked_for or booked_by can cancel
        if (reservation.booked_for_id != current_user.id and 
            reservation.booked_by_id != current_user.id):
            flash('Sie haben keine Berechtigung für diese Aktion', 'error')
            return redirect(url_for('reservations.list_reservations')), 403
        
        success, error = ReservationService.cancel_reservation(id)
        
        if error:
            flash(error, 'error')
        else:
            flash('Buchung erfolgreich storniert', 'success')
        
        return redirect(url_for('reservations.list_reservations'))
        
    except Exception as e:
        flash(str(e), 'error')
        return redirect(url_for('reservations.list_reservations'))
