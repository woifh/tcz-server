#!/bin/bash
# Deployment script for PythonAnywhere
# Run this script ON PYTHONANYWHERE in your project directory

set -e  # Exit on any error

echo "=== Tennis Club PythonAnywhere Deployment ==="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_step() {
    echo -e "${GREEN}[STEP]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "wsgi.py" ]; then
    print_error "wsgi.py not found. Please run this script from your project root directory."
    exit 1
fi

print_step "Checking current branch..."
git branch --show-current

print_step "Pulling latest changes from git..."
git pull origin main

print_step "Activating virtual environment..."
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
else
    print_error "Virtual environment not found. Please create one first."
    exit 1
fi

print_step "Upgrading pip..."
pip install --upgrade pip

print_step "Installing/updating dependencies..."
pip install -r requirements.txt

print_step "Checking current database migration..."
flask db current

print_step "Running database migrations..."
flask db upgrade

print_step "Verifying migration was successful..."
flask db current

echo ""
print_warning "IMPORTANT: Don't forget to reload your web app!"
echo ""
echo "To reload your web app:"
echo "  1. Go to the 'Web' tab in PythonAnywhere"
echo "  2. Click the green 'Reload' button"
echo ""
echo "Or run this command:"
echo "  touch /var/www/\${USER}_pythonanywhere_com_wsgi.py"
echo ""

print_step "Deployment complete!"
echo ""
echo "Next steps:"
echo "  1. Reload your web app (see above)"
echo "  2. Visit your site and test the changes"
echo "  3. Check error logs if something doesn't work"
echo ""
