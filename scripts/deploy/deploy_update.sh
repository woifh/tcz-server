#!/bin/bash
# Deployment script for PythonAnywhere
# Run this in a PythonAnywhere Bash console

echo "🚀 Deploying Tennis Club Reservation System..."
echo ""

# Navigate to project directory
cd ~/tcz || exit 1
echo "✓ Changed to project directory"

# Pull latest changes from GitHub
echo ""
echo "📥 Pulling latest changes from GitHub..."
git pull origin main
if [ $? -eq 0 ]; then
    echo "✓ Git pull successful"
else
    echo "✗ Git pull failed"
    exit 1
fi

# Activate virtual environment
echo ""
echo "🐍 Activating virtual environment..."
source ~/.virtualenvs/tennisclub/bin/activate
echo "✓ Virtual environment activated"

# Install/update dependencies
echo ""
echo "📦 Installing dependencies..."
pip install -r requirements.txt
if [ $? -eq 0 ]; then
    echo "✓ Dependencies installed"
else
    echo "✗ Dependency installation failed"
    exit 1
fi

# Run database migrations
echo ""
echo "🗄️  Running database migrations..."
export FLASK_APP=wsgi.py
flask db upgrade
if [ $? -eq 0 ]; then
    echo "✓ Database migrations complete"
else
    echo "⚠️  Database migrations failed (may be okay if no new migrations)"
fi

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Next steps:"
echo "1. Reload your webapp at: https://www.pythonanywhere.com/user/woifh/webapps/"
echo "2. Or tell Kiro to 'reload the webapp'"
echo "3. Test your app at: https://woifh.pythonanywhere.com"
echo ""
