"""Dashboard route."""
import os
import subprocess
from flask import Blueprint, render_template, redirect, url_for, jsonify
from flask_login import login_required, current_user

bp = Blueprint('dashboard', __name__)


@bp.route('/')
def index():
    """Root route - redirect based on authentication status."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))
    else:
        return redirect(url_for('dashboard.anonymous_overview'))


@bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard - main authenticated dashboard."""
    return render_template('dashboard.html')


@bp.route('/overview')
def anonymous_overview():
    """Anonymous court overview for non-authenticated users."""
    try:
        return render_template('anonymous_overview.html')
    except Exception as e:
        # If template fails, return simple HTML for debugging
        return f"""
        <html>
        <head><title>Debug - Anonymous Overview</title></head>
        <body>
            <h1>Anonymous Overview Debug</h1>
            <p>Template error: {str(e)}</p>
            <p>This should be the anonymous overview page.</p>
            <a href="/auth/login">Login</a>
        </body>
        </html>
        """


@bp.route('/debug')
def debug():
    """Debug route to test authentication status."""
    return f"""
    <html>
    <head><title>Debug Info</title></head>
    <body>
        <h1>Debug Information</h1>
        <p><strong>User authenticated:</strong> {current_user.is_authenticated}</p>
        <p><strong>Current user:</strong> {current_user}</p>
        <p><strong>Anonymous user:</strong> {current_user.is_anonymous}</p>
        <hr>
        <p><a href="/">Go to root</a></p>
        <p><a href="/overview">Go to overview</a></p>
        <p><a href="/auth/login">Go to login</a></p>
    </body>
    </html>
    """


@bp.route('/debug-short-notice')
def debug_short_notice():
    """Debug route to test short notice booking functionality."""
    from datetime import datetime, timedelta
    from app.services.reservation_service import ReservationService
    from app.utils.timezone_utils import get_current_berlin_time
    
    # Test short notice detection with different scenarios
    now_berlin = get_current_berlin_time()
    now_utc = datetime.utcnow()
    
    # Test cases
    test_cases = [
        ("5 min future (Berlin)", now_berlin.date(), (now_berlin + timedelta(minutes=5)).time(), now_berlin),
        ("20 min future (Berlin)", now_berlin.date(), (now_berlin + timedelta(minutes=20)).time(), now_berlin),
        ("5 min future (UTC)", now_utc.date(), (now_utc + timedelta(minutes=5)).time(), now_utc),
        ("20 min future (UTC)", now_utc.date(), (now_utc + timedelta(minutes=20)).time(), now_utc),
    ]
    
    results = []
    for description, test_date, test_time, current_time in test_cases:
        try:
            is_short = ReservationService.is_short_notice_booking(test_date, test_time, current_time)
            reservation_dt = datetime.combine(test_date, test_time)
            time_diff = reservation_dt - current_time
            results.append(f"{description}: Date={test_date}, Time={test_time}, Short Notice={is_short}, Time Diff={time_diff}")
        except Exception as e:
            results.append(f"{description}: ERROR - {str(e)}")
    
    # Test actual booking scenario
    try:
        from app.models import Court
        court = Court.query.first()
        if court:
            # Test with a time 10 minutes from now
            test_time_10min = (now_local + timedelta(minutes=10)).time()
            is_short_10min = ReservationService.is_short_notice_booking(now_local.date(), test_time_10min)
            booking_test = f"Booking test (10min future): Court {court.id}, Time {test_time_10min}, Would be short notice: {is_short_10min}"
        else:
            booking_test = "No courts found for booking test"
    except Exception as e:
        booking_test = f"Booking test error: {str(e)}"
    
    return f"""
    <html>
    <head><title>Short Notice Debug</title></head>
    <body>
        <h1>Short Notice Booking Debug</h1>
        <p><strong>Current time (local):</strong> {now_local}</p>
        <p><strong>Current time (UTC):</strong> {now_utc}</p>
        <p><strong>Time difference:</strong> {now_local - now_utc}</p>
        <h2>Test Results:</h2>
        <ul>
            {''.join(f'<li>{result}</li>' for result in results)}
        </ul>
        <h2>Booking Test:</h2>
        <p>{booking_test}</p>
        <hr>
        <p><a href="/">Go to root</a></p>
        <p><a href="/debug">Go to debug</a></p>
        <p><a href="/courts/availability">Check availability API</a></p>
    </body>
    </html>
    """


@bp.route('/version')
def version():
    """Version endpoint for deployment verification."""
    try:
        from app.version import get_version_info

        # Get version info from the new version module
        info = get_version_info()

        # Try to read deployment info file as well
        deployment_info = {}
        deployment_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'deployment_info.json')

        if os.path.exists(deployment_file):
            import json
            with open(deployment_file, 'r') as f:
                deployment_info = json.load(f)

        response = {
            'success': True,
            'status': 'ok',
            'version': info['version'],
            'commit_hash': info['commit_hash'],
            'branch': info['branch'],
            'last_commit_date': info['last_commit_date'],
            'deployment_time': info['deployment_time'],
            'deployment_check': 'success'
        }

        # Add deployment info if available
        if deployment_info:
            response['deployment_info'] = deployment_info
            if 'deployment_time' in deployment_info:
                response['deployment_time'] = deployment_info.get('deployment_time')
            response['deployed_git_hash'] = deployment_info.get('git_hash_short')
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'deployment_check': 'failed'
        }), 500
