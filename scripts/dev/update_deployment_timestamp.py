#!/usr/bin/env python3
"""Update deployment timestamp for version tracking."""

import json
import datetime
import subprocess
import os

def update_deployment_info():
    """Update deployment information."""
    try:
        # Get git information
        git_hash = subprocess.check_output(['git', 'rev-parse', 'HEAD'], 
                                         universal_newlines=True).strip()
        git_message = subprocess.check_output(['git', 'log', '-1', '--pretty=%s'], 
                                            universal_newlines=True).strip()
        git_date = subprocess.check_output(['git', 'log', '-1', '--pretty=%ci'], 
                                         universal_newlines=True).strip()
        
        deployment_info = {
            'deployment_time': datetime.datetime.now().isoformat(),
            'git_hash': git_hash,
            'git_hash_short': git_hash[:8],
            'git_message': git_message,
            'git_date': git_date,
            'deployed_by': os.environ.get('USER', 'unknown')
        }
        
        # Write to deployment info file
        with open('deployment_info.json', 'w') as f:
            json.dump(deployment_info, f, indent=2)
        
        print("✅ Deployment info updated:")
        print(f"   Commit: {deployment_info['git_hash_short']} - {git_message}")
        print(f"   Deployed: {deployment_info['deployment_time']}")
        
    except Exception as e:
        print(f"❌ Error updating deployment info: {e}")

if __name__ == '__main__':
    update_deployment_info()