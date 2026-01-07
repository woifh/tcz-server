#!/bin/bash
# Setup script for Tennis Club Reservation System

echo "Tennis Club Reservation System - Setup"
echo "======================================="
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit .env file with your configuration!"
fi

# Install Node.js dependencies for Tailwind CSS
echo ""
echo "Installing Node.js dependencies..."
if command -v npm &> /dev/null; then
    npm install
    echo "Building Tailwind CSS..."
    npm run build:css
else
    echo "Warning: npm not found. Please install Node.js to build Tailwind CSS."
fi

echo ""
echo "======================================="
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your database and email settings"
echo "2. Activate virtual environment: source venv/bin/activate"
echo "3. Initialize database: flask db init && flask db migrate && flask db upgrade"
echo "4. Run development server: flask run"
