#!/bin/bash
# Initial setup script for PythonAnywhere
# Run this ONCE when first setting up the project on PythonAnywhere

set -e  # Exit on any error

echo "=== Tennis Club PythonAnywhere Initial Setup ==="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

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

# Check if virtual environment already exists
if [ -d "venv" ] || [ -d ".venv" ]; then
    print_warning "Virtual environment already exists. Skipping creation."
    if [ -d "venv" ]; then
        VENV_DIR="venv"
    else
        VENV_DIR=".venv"
    fi
else
    print_step "Creating virtual environment..."
    python3 -m venv venv
    VENV_DIR="venv"
fi

print_step "Activating virtual environment..."
source $VENV_DIR/bin/activate

print_step "Upgrading pip..."
pip install --upgrade pip

print_step "Installing dependencies..."
pip install -r requirements.txt

print_step "Checking if .env.production exists..."
if [ ! -f ".env.production" ]; then
    print_warning ".env.production not found!"
    echo ""
    echo "You need to create .env.production with your production settings."
    echo "Use .env.production.example as a template:"
    echo ""
    echo "  cp .env.production.example .env.production"
    echo "  nano .env.production  # Edit with your settings"
    echo ""
else
    print_step ".env.production found!"
fi

print_step "Checking database migration status..."
if flask db current 2>/dev/null; then
    echo "Database is already initialized."
else
    print_warning "Database not initialized. Run migrations after setting up .env.production"
    echo ""
    echo "After creating .env.production, run:"
    echo "  flask db upgrade"
    echo ""
fi

echo ""
print_step "Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Create/verify .env.production with your production credentials"
echo "  2. Run database migrations: flask db upgrade"
echo "  3. Configure your web app in PythonAnywhere Web tab"
echo "  4. Set the WSGI configuration file path to: /home/YOUR_USERNAME/tcz/wsgi.py"
echo "  5. Set virtualenv path to: /home/YOUR_USERNAME/tcz/venv"
echo "  6. Reload your web app"
echo ""
