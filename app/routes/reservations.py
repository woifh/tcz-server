"""Reservation routes."""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date
from app import db  # Removed limiter import for local development
from app.models import Reservation
from app.services.reservation_service import ReservationService
from app.decorators.auth import jwt_or_session_required
from app.utils.validators import (
    ValidationError,
    validate_date_format,
    validate_time_format,
    validate_integer,
    validate_uuid
)

bp = Blueprint('reservations', __name__, url_prefix='/reservations')


@bp.route('/', methods=['GET'])
@jwt_or_session_required
def list_reservations():
    """
    List user's reservations or all reservations for a date.
    
    Enhanced with time-based filtering and active/past status indicators.
    Supports both HTML and JSON responses with backward compatibility.
    
    Query Parameters:
    - date: Specific date to query (YYYY-MM-DD format)
    - include_past: Include past reservations (true/false, default: false)
    - format: Response format ('json' for JSON response)
    
    Returns:
    - HTML: Rendered reservations template
    - JSON: Structured reservation data with active/past status indicators
    """
    date_str = request.args.get('date')
    include_past = request.args.get('include_past', 'false').lower() == 'true'
    # Use consistent Europe/Berlin timezone
    from app.utils.timezone_utils import get_current_berlin_time
    current_time = get_current_berlin_time()
    
    if date_str:
        # List all reservations for a specific date (for admin/viewing)
        try:
            query_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            reservations = ReservationService.get_reservations_by_date(query_date)
            
            # Format for JSON response (only if explicitly requested via query param or content type)
            if request.args.get('format') == 'json' or (request.is_json and request.accept_mimetypes.best == 'application/json'):
                return jsonify({
                    'date': date_str,
                    'current_time': current_time.isoformat(),
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
                            'is_short_notice': r.is_short_notice,
                            'is_active': ReservationService.is_reservation_currently_active(r, current_time),
                            'booking_status': 'active' if ReservationService.is_reservation_currently_active(r, current_time) else 'past'
                        }
                        for r in reservations
                    ],
                    'metadata': {
                        'total_count': len(reservations),
                        'active_count': len([r for r in reservations if ReservationService.is_reservation_currently_active(r, current_time)]),
                        'past_count': len([r for r in reservations if not ReservationService.is_reservation_currently_active(r, current_time)]),
                        'uses_time_based_logic': True,
                        'timezone': 'Europe/Berlin'
                    }
                })
            
            return render_template('reservations.html', reservations=reservations, date=query_date)
        except ValueError:
            flash('Ungültiges Datumsformat', 'error')
            return redirect(url_for('reservations.list_reservations'))
    else:
        # List user's own reservations using enhanced time-based logic
        if include_past:
            # Get all reservations (active and past) for the user
            from app.models import Reservation
            all_reservations = Reservation.query.filter(
                (Reservation.booked_for_id == current_user.id) | (Reservation.booked_by_id == current_user.id),
                Reservation.status == 'active'
            ).order_by(Reservation.date.desc(), Reservation.start_time.desc()).all()
            reservations = all_reservations
        else:
            # Get only active booking sessions using time-based logic (default behavior)
            # include_bookings_for_others=True to show bookings made for others in display
            reservations = ReservationService.get_member_active_booking_sessions(
                current_user.id, include_short_notice=True, current_time=current_time,
                include_bookings_for_others=True
            )
        
        # Return JSON if explicitly requested
        if request.args.get('format') == 'json' or (request.is_json and request.accept_mimetypes.best == 'application/json'):
            # Calculate statistics for enhanced response
            active_reservations = [r for r in reservations if ReservationService.is_reservation_currently_active(r, current_time)]
            past_reservations = [r for r in reservations if not ReservationService.is_reservation_currently_active(r, current_time)]

            # For limit counting, only count reservations where user is booked_for (not bookings made for others)
            my_active_reservations = [r for r in active_reservations if r.booked_for_id == current_user.id]
            regular_active = [r for r in my_active_reservations if not r.is_short_notice]
            short_notice_active = [r for r in my_active_reservations if r.is_short_notice]

            return jsonify({
                'current_time': current_time.isoformat(),
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
                        'is_short_notice': r.is_short_notice,
                        'is_active': ReservationService.is_reservation_currently_active(r, current_time),
                        'booking_status': 'active' if ReservationService.is_reservation_currently_active(r, current_time) else 'past'
                    }
                    for r in reservations
                ],
                'filter': {
                    'include_past': include_past,
                    'uses_time_based_filtering': not include_past
                },
                'statistics': {
                    'total_count': len(reservations),
                    'active_count': len(active_reservations),
                    'past_count': len(past_reservations),
                    'regular_active_count': len(regular_active),
                    'short_notice_active_count': len(short_notice_active),
                    'regular_limit_usage': f"{len(regular_active)}/2",
                    'short_notice_limit_usage': f"{len(short_notice_active)}/1"
                },
                'metadata': {
                    'uses_time_based_logic': True,
                    'timezone': 'Europe/Berlin',
                    'api_version': '1.1'
                }
            })
        
        return render_template('reservations.html', reservations=reservations)


@bp.route('/status', methods=['GET'])
@jwt_or_session_required
def reservation_status():
    """
    Get reservation status information for the current user.
    
    This endpoint provides real-time status information about the user's reservations,
    including active booking session counts and limit usage. Useful for dashboard
    widgets and real-time availability displays.
    
    Returns:
        JSON response with reservation status and limit information
    """
    # Use consistent Europe/Berlin timezone
    from app.utils.timezone_utils import get_current_berlin_time
    current_time = get_current_berlin_time()
    
    # Get active booking sessions (regular reservations for limit enforcement)
    active_regular_sessions = ReservationService.get_member_active_booking_sessions(
        current_user.id, include_short_notice=False, current_time=current_time
    )
    
    # Get active short notice bookings
    active_short_notice = ReservationService.get_member_active_short_notice_bookings(
        current_user.id, current_time=current_time
    )
    
    # Get all active reservations (including short notice)
    all_active_reservations = ReservationService.get_member_active_booking_sessions(
        current_user.id, include_short_notice=True, current_time=current_time
    )
    
    return jsonify({
        'current_time': current_time.isoformat(),
        'user_id': current_user.id,
        'limits': {
            'regular_reservations': {
                'limit': 2,
                'current': len(active_regular_sessions),
                'available': 2 - len(active_regular_sessions),
                'can_book': len(active_regular_sessions) < 2
            },
            'short_notice_bookings': {
                'limit': 1,
                'current': len(active_short_notice),
                'available': 1 - len(active_short_notice),
                'can_book': len(active_short_notice) < 1
            }
        },
        'active_reservations': {
            'total': len(all_active_reservations),
            'regular': len(active_regular_sessions),
            'short_notice': len(active_short_notice)
        },
        'next_reservations': [
            {
                'id': r.id,
                'court_number': r.court.number,
                'date': r.date.isoformat(),
                'start_time': r.start_time.strftime('%H:%M'),
                'end_time': r.end_time.strftime('%H:%M'),
                'is_short_notice': r.is_short_notice,
                'booking_status': 'active'
            }
            for r in sorted(all_active_reservations, key=lambda x: (x.date, x.start_time))[:3]
        ],
        'metadata': {
            'uses_time_based_logic': True,
            'timezone': 'Europe/Berlin',
            'api_version': '1.1'
        }
    })


@bp.route('/', methods=['POST'])
@jwt_or_session_required
# @limiter.limit("10 per minute")  # Disabled for local development
def create_reservation():
    """Create a new reservation."""
    try:
        data = request.get_json() if request.is_json else request.form
        
        # Validate input data
        try:
            court_id = validate_integer(data.get('court_id'), 'court_id', min_value=1, max_value=6)
            reservation_date = validate_date_format(data.get('date'), 'date')
            start_time = validate_time_format(data.get('start_time'), 'start_time')
            booked_for_id = validate_uuid(
                data.get('booked_for_id', current_user.id),
                'booked_for_id'
            )
        except ValidationError as e:
            if request.is_json:
                return jsonify({'error': str(e)}), 400
            flash(str(e), 'error')
            return redirect(url_for('dashboard.index'))
        
        # Create reservation
        # Pass current_user as booked_for_member when booking for self to avoid redundant query
        booked_for_member = current_user if booked_for_id == current_user.id else None
        reservation, error, active_sessions = ReservationService.create_reservation(
            court_id=court_id,
            date=reservation_date,
            start_time=start_time,
            booked_for_id=booked_for_id,
            booked_by_id=current_user.id,
            booked_for_member=booked_for_member
        )

        if error:
            if request.is_json:
                response = {'error': error}
                if active_sessions:
                    response['active_sessions'] = [
                        {
                            'date': s.date.isoformat(),
                            'start_time': s.start_time.strftime('%H:%M'),
                            'court_number': s.court.number if s.court else None
                        } for s in active_sessions
                    ]
                return jsonify(response), 400
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


@bp.route('/<int:id>', methods=['DELETE'])
@jwt_or_session_required
def delete_reservation(id):
    """Cancel a reservation."""
    try:
        reservation = Reservation.query.get_or_404(id)
        
        # Check authorization: only booked_for or booked_by can cancel
        if (reservation.booked_for_id != current_user.id and
            reservation.booked_by_id != current_user.id):
            return jsonify({'error': 'Du hast keine Berechtigung für diese Aktion'}), 403
        
        success, error = ReservationService.cancel_reservation(id, cancelled_by_id=current_user.id)

        if error:
            return jsonify({'error': error}), 400

        return jsonify({'message': 'Buchung erfolgreich storniert'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
