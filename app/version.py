"""Version information for the application."""
from datetime import datetime
import subprocess
import os

# Application version
VERSION = "1.0.0"

def get_git_commit_hash():
    """Get the current git commit hash."""
    try:
        return subprocess.check_output(
            ['git', 'rev-parse', '--short', 'HEAD'],
            stderr=subprocess.DEVNULL,
            cwd=os.path.dirname(os.path.dirname(__file__))
        ).decode('utf-8').strip()
    except:
        return "unknown"

def get_git_branch():
    """Get the current git branch."""
    try:
        return subprocess.check_output(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            stderr=subprocess.DEVNULL,
            cwd=os.path.dirname(os.path.dirname(__file__))
        ).decode('utf-8').strip()
    except:
        return "unknown"

def get_last_commit_date():
    """Get the date of the last commit."""
    try:
        timestamp = subprocess.check_output(
            ['git', 'log', '-1', '--format=%ct'],
            stderr=subprocess.DEVNULL,
            cwd=os.path.dirname(os.path.dirname(__file__))
        ).decode('utf-8').strip()
        return datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
    except:
        return "unknown"

def get_version_info():
    """Get complete version information."""
    return {
        'version': VERSION,
        'commit_hash': get_git_commit_hash(),
        'branch': get_git_branch(),
        'last_commit_date': get_last_commit_date(),
        'deployment_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
