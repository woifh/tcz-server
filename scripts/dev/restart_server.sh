#!/bin/bash
"""
Script to restart the local Flask development server.
Stops any existing Flask processes and starts a new one.
"""

echo "🔄 Restarting Flask Development Server..."
echo "=" * 50

# Function to check if server is running
check_server() {
    if pgrep -f "flask run" > /dev/null; then
        return 0  # Server is running
    else
        return 1  # Server is not running
    fi
}

# Function to stop existing server
stop_server() {
    echo "🛑 Stopping existing Flask server..."
    pkill -f "flask run" 2>/dev/null
    
    # Wait a moment for processes to terminate
    sleep 2
    
    # Force kill if still running
    if check_server; then
        echo "⚠️  Force killing Flask processes..."
        pkill -9 -f "flask run" 2>/dev/null
        sleep 1
    fi
    
    if check_server; then
        echo "❌ Failed to stop existing server"
        return 1
    else
        echo "✅ Existing server stopped"
        return 0
    fi
}

# Function to start server
start_server() {
    echo "🚀 Starting Flask server..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Load environment variables from .env
    if [ -f .env ]; then
        export $(cat .env | grep -v '^#' | xargs)
    fi
    
    # Set Flask environment variables
    export FLASK_APP=wsgi.py
    export FLASK_ENV=development
    
    # Start server in background
    python3 -m flask run --host=0.0.0.0 --port=5001 &
    
    # Get the process ID
    SERVER_PID=$!
    
    # Wait a moment for server to start
    sleep 3
    
    # Check if server started successfully
    if check_server; then
        echo "✅ Flask server started successfully!"
        echo "📍 Server running at: http://localhost:5001"
        echo "🆔 Process ID: $SERVER_PID"
        echo ""
        echo "💡 To stop the server later, run:"
        echo "   pkill -f 'flask run'"
        echo ""
        echo "📋 Server logs will appear below:"
        echo "=" * 50
        return 0
    else
        echo "❌ Failed to start Flask server"
        return 1
    fi
}

# Main execution
echo "🔍 Checking for existing Flask server..."

if check_server; then
    echo "📍 Found running Flask server"
    stop_server
    if [ $? -ne 0 ]; then
        echo "❌ Failed to stop existing server. Exiting."
        exit 1
    fi
else
    echo "✅ No existing Flask server found"
fi

echo ""
start_server

if [ $? -eq 0 ]; then
    echo "🎉 Server restart completed successfully!"
    echo ""
    echo "🌐 You can now access the application at:"
    echo "   http://localhost:5001"
    echo ""
    echo "⚠️  Note: This terminal will show server logs."
    echo "   Press Ctrl+C to stop the server when done."
else
    echo "❌ Server restart failed!"
    exit 1
fi