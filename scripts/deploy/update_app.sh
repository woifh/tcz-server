#!/bin/bash
# Update script for PythonAnywhere deployment
# Run this after pushing changes to GitHub

set -e

echo "=========================================="
echo "Updating Tennis Club Reservation System"
echo "=========================================="
echo ""

# Configuration
PROJECT_DIR="$HOME/tcz"
VENV_NAME="tennisclub"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Navigate to project directory
cd "$PROJECT_DIR"

# Pull latest changes
echo "Pulling latest changes from GitHub..."
git pull origin main
print_status "Code updated"

# Activate virtual environment
source "$HOME/.virtualenvs/$VENV_NAME/bin/activate"
print_status "Virtual environment activated"

# Update dependencies
echo ""
echo "Updating dependencies..."
pip install -r requirements.txt --upgrade
print_status "Dependencies updated"

# Run database migrations
echo ""
echo "Running database migrations..."
export FLASK_APP=wsgi.py
flask db upgrade
print_status "Database migrations completed"

# Deactivate virtual environment
deactivate

echo ""
print_warning "IMPORTANT: Go to the Web tab and click the Reload button!"
echo ""
echo "Your app: https://woifh.pythonanywhere.com"
echo ""
