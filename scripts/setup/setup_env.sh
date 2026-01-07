#!/bin/bash

# Setup script for Tennis Club Reservation System
# Handles Python 3.13 compatibility issues

echo "🏗️  Setting up Tennis Club Reservation System..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
python3 -m pip install --upgrade pip

# Install Python 3.13 compatible versions
echo "📚 Installing Python 3.13 compatible dependencies..."
python3 -m pip install -r requirements.txt

echo "✅ Setup complete!"
echo ""
echo "To start the application:"
echo "  source venv/bin/activate"
echo "  export FLASK_ENV=development"
echo "  python wsgi.py"
echo ""
echo "Application will be available at: http://127.0.0.1:5000"