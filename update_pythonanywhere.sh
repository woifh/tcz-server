#!/bin/bash
# Quick Update Script for PythonAnywhere
# Run this in a PythonAnywhere Bash console to update your deployed app

set -e  # Exit on error

echo "=========================================="
echo "Updating Tennis Club App on PythonAnywhere"
echo "=========================================="
echo ""

# Configuration
USERNAME="woifh"
PROJECT_NAME="tcz"
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

# Step 1: Navigate to project directory
echo "Step 1: Navigating to project directory..."
cd "$HOME/$PROJECT_NAME"
print_status "In project directory"

# Step 2: Pull latest changes from GitHub
echo ""
echo "Step 2: Pulling latest changes from GitHub..."
git pull origin main
print_status "Latest changes pulled"

# Step 3: Activate virtual environment
echo ""
echo "Step 3: Activating virtual environment..."
source "$HOME/.virtualenvs/$VENV_NAME/bin/activate"
print_status "Virtual environment activated"

# Step 4: Install/update dependencies
echo ""
echo "Step 4: Updating dependencies..."
pip install -r requirements.txt --upgrade
print_status "Dependencies updated"

# Step 5: Run database migrations
echo ""
echo "Step 5: Running database migrations..."
export FLASK_APP=wsgi.py
flask db upgrade
print_status "Database migrations completed"

# Step 6: Reload web app
echo ""
echo "Step 6: Reloading web app..."
echo ""
print_warning "You need to reload your web app manually:"
echo "1. Go to: https://www.pythonanywhere.com/user/$USERNAME/webapps/"
echo "2. Click the green 'Reload' button for your web app"
echo ""
echo "Or use the API (if you have an API token):"
echo "curl -X POST https://www.pythonanywhere.com/api/v0/user/$USERNAME/webapps/${USERNAME}.pythonanywhere.com/reload/ \\"
echo "  -H 'Authorization: Token YOUR_API_TOKEN'"
echo ""

echo "=========================================="
echo "Update Complete!"
echo "=========================================="
echo ""
print_status "All steps completed successfully!"
echo ""
echo "Your app should be updated at: https://$USERNAME.pythonanywhere.com"
echo ""
echo "If you see any issues:"
echo "- Check the error log: https://www.pythonanywhere.com/user/$USERNAME/files/var/log/"
echo "- Make sure you clicked the Reload button"
echo ""
