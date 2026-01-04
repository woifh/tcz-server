#!/bin/bash
# Quick deployment script for PythonAnywhere
# Copy and paste this entire script into a PythonAnywhere Bash console

set -e  # Exit on error

echo "🚀 Deploying Tennis Club Reservation System to PythonAnywhere..."
echo ""

# Navigate to project directory
cd ~/tcz || { echo "❌ Error: Project directory not found"; exit 1; }
echo "✅ Changed to project directory: $(pwd)"

# Pull latest changes from GitHub
echo ""
echo "📥 Pulling latest changes from GitHub..."
git fetch origin
git pull origin main || { echo "❌ Error: Git pull failed"; exit 1; }
echo "✅ Git pull successful"

# Show what changed
echo ""
echo "📝 Recent changes:"
git log -3 --oneline
echo ""

# Activate virtual environment (if it exists)
if [ -d ~/.virtualenvs/tennisclub ]; then
    echo "🐍 Activating virtual environment..."
    source ~/.virtualenvs/tennisclub/bin/activate
    echo "✅ Virtual environment activated"
    
    # Install/update dependencies
    echo ""
    echo "📦 Checking dependencies..."
    pip install -q -r requirements.txt
    echo "✅ Dependencies up to date"
else
    echo "⚠️  Virtual environment not found at ~/.virtualenvs/tennisclub"
    echo "   Skipping dependency installation"
fi

# Run database migrations (if Flask is available)
if command -v flask &> /dev/null; then
    echo ""
    echo "🗄️  Running database migrations..."
    export FLASK_APP=wsgi.py
    flask db upgrade 2>&1 | grep -v "INFO" || echo "   No new migrations"
    echo "✅ Database migrations complete"
fi

# Update deployment timestamp
echo ""
echo "📝 Updating deployment info..."
python3 update_deployment_timestamp.py

echo ""
echo "✅ Code deployment complete!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔄 IMPORTANT: You must now reload your webapp!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Option 1: Use the Web Interface"
echo "  1. Go to: https://www.pythonanywhere.com/user/S84AB/webapps/"
echo "  2. Click the green 'Reload' button"
echo ""
echo "Option 2: Use the API (if you have the token)"
echo "  Run this command:"
echo "  curl -X POST https://www.pythonanywhere.com/api/v0/user/S84AB/webapps/S84AB.pythonanywhere.com/reload/ \\"
echo "    -H 'Authorization: Token YOUR_API_TOKEN'"
echo ""
echo "After reloading, test at: https://S84AB.pythonanywhere.com"
echo ""
