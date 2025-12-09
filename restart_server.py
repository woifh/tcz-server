#!/usr/bin/env python3
"""
Script to restart the local Flask development server.
Stops any existing Flask processes and starts a new one.
"""

import os
import sys
import time
import signal
import subprocess
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def find_flask_processes():
    """Find all Flask server processes."""
    try:
        result = subprocess.run(['pgrep', '-f', 'flask run'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            pids = [int(pid.strip()) for pid in result.stdout.strip().split('\n') if pid.strip()]
            return pids
        return []
    except Exception as e:
        print(f"Error finding Flask processes: {e}")
        return []

def stop_flask_server():
    """Stop any existing Flask server processes."""
    print("🛑 Stopping existing Flask server...")
    
    pids = find_flask_processes()
    
    if not pids:
        print("✅ No existing Flask server found")
        return True
    
    print(f"📍 Found Flask processes: {pids}")
    
    # Try graceful termination first
    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)
            print(f"   Sent SIGTERM to process {pid}")
        except ProcessLookupError:
            print(f"   Process {pid} already terminated")
        except Exception as e:
            print(f"   Error terminating process {pid}: {e}")
    
    # Wait for processes to terminate
    time.sleep(2)
    
    # Check if any processes are still running
    remaining_pids = find_flask_processes()
    
    if remaining_pids:
        print("⚠️  Some processes still running, force killing...")
        for pid in remaining_pids:
            try:
                os.kill(pid, signal.SIGKILL)
                print(f"   Force killed process {pid}")
            except ProcessLookupError:
                print(f"   Process {pid} already terminated")
            except Exception as e:
                print(f"   Error force killing process {pid}: {e}")
        
        time.sleep(1)
    
    # Final check
    final_pids = find_flask_processes()
    if final_pids:
        print(f"❌ Failed to stop processes: {final_pids}")
        return False
    else:
        print("✅ All Flask processes stopped")
        return True

def start_flask_server():
    """Start the Flask development server."""
    print("🚀 Starting Flask server...")
    
    # Set environment variables
    env = os.environ.copy()
    env['FLASK_APP'] = 'wsgi.py'
    env['FLASK_ENV'] = 'development'
    
    try:
        # Start the server
        process = subprocess.Popen([
            sys.executable, '-m', 'flask', 'run', 
            '--host=0.0.0.0', '--port=5001'
        ], env=env)
        
        # Wait a moment for server to start
        time.sleep(3)
        
        # Check if process is still running
        if process.poll() is None:
            print("✅ Flask server started successfully!")
            print("📍 Server running at: http://localhost:5001")
            print(f"🆔 Process ID: {process.pid}")
            print()
            print("💡 To stop the server later, run:")
            print("   python3 restart_server.py --stop")
            print("   or")
            print("   pkill -f 'flask run'")
            print()
            print("📋 Server is running in the background.")
            print("   Check server logs with: tail -f flask.log")
            return True
        else:
            print("❌ Flask server failed to start")
            return False
            
    except Exception as e:
        print(f"❌ Error starting Flask server: {e}")
        return False

def main():
    """Main function."""
    print("🔄 Flask Development Server Manager")
    print("=" * 50)
    
    # Check for stop-only flag
    if len(sys.argv) > 1 and sys.argv[1] == '--stop':
        print("🛑 Stop-only mode")
        if stop_flask_server():
            print("🎉 Server stopped successfully!")
        else:
            print("❌ Failed to stop server!")
            sys.exit(1)
        return
    
    # Check for start-only flag
    if len(sys.argv) > 1 and sys.argv[1] == '--start':
        print("🚀 Start-only mode")
        if find_flask_processes():
            print("⚠️  Flask server already running!")
            print("   Use --restart to restart or --stop to stop")
            sys.exit(1)
        
        if start_flask_server():
            print("🎉 Server started successfully!")
        else:
            print("❌ Failed to start server!")
            sys.exit(1)
        return
    
    # Default: restart (stop + start)
    print("🔄 Restart mode (stop + start)")
    
    # Stop existing server
    if not stop_flask_server():
        print("❌ Failed to stop existing server. Exiting.")
        sys.exit(1)
    
    print()
    
    # Start new server
    if start_flask_server():
        print("🎉 Server restart completed successfully!")
        print()
        print("🌐 You can now access the application at:")
        print("   http://localhost:5001")
    else:
        print("❌ Server restart failed!")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✅ Operation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)