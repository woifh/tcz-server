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
    return render_template('anonymous_overview.html')


@bp.route('/version')
def version():
    """Version endpoint for deployment verification."""
    try:
        # Try to read deployment info file first
        deployment_info = {}
        deployment_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'deployment_info.json')
        
        if os.path.exists(deployment_file):
            import json
            with open(deployment_file, 'r') as f:
                deployment_info = json.load(f)
        
        # Get current git info as fallback
        git_hash = subprocess.check_output(['git', 'rev-parse', 'HEAD'], 
                                         cwd=os.path.dirname(os.path.dirname(__file__)),
                                         universal_newlines=True).strip()[:8]
        
        git_message = subprocess.check_output(['git', 'log', '-1', '--pretty=%s'], 
                                            cwd=os.path.dirname(os.path.dirname(__file__)),
                                            universal_newlines=True).strip()
        
        git_date = subprocess.check_output(['git', 'log', '-1', '--pretty=%ci'], 
                                         cwd=os.path.dirname(os.path.dirname(__file__)),
                                         universal_newlines=True).strip()
        
        response = {
            'status': 'ok',
            'current_git_hash': git_hash,
            'current_git_message': git_message,
            'current_git_date': git_date,
            'deployment_check': 'success'
        }
        
        # Add deployment info if available
        if deployment_info:
            response['deployment_info'] = deployment_info
            response['deployment_time'] = deployment_info.get('deployment_time')
            response['deployed_git_hash'] = deployment_info.get('git_hash_short')
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'deployment_check': 'failed'
        }), 500
