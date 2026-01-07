#!/bin/bash
# Consolidated PythonAnywhere Deployment Script
# Tennis Club Reservation System
#
# Usage:
#   Run this script IN YOUR PROJECT DIRECTORY on PythonAnywhere
#   ./scripts/deploy/pythonanywhere.sh
#
# This script handles regular deployments (updates) only.
# For first-time setup, see: scripts/setup/pythonanywhere.sh

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_step() {
    echo -e "${BLUE}==>${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_header() {
    echo ""
    echo "=========================================="
    echo "$1"
    echo "=========================================="
    echo ""
}

# Trap errors and provide helpful message
trap 'print_error "Deployment failed at line $LINENO. Check the error message above."; exit 1' ERR

# Start deployment
print_header "Tennis Club - PythonAnywhere Deployment"

# Step 1: Verify we're in the right directory
print_step "Verifying project directory..."
if [ ! -f "wsgi.py" ]; then
    print_error "wsgi.py not found. Please run this script from your project root directory (~/tcz)"
    exit 1
fi
print_success "Project directory verified: $(pwd)"

# Step 2: Check current branch
print_step "Checking git branch..."
CURRENT_BRANCH=$(git branch --show-current)
print_success "Current branch: $CURRENT_BRANCH"

# Step 3: Pull latest changes
print_step "Pulling latest changes from GitHub..."
git fetch origin
git pull origin main
print_success "Git pull successful"

# Show recent commits
echo ""
echo "Recent changes:"
git log -3 --oneline --decorate
echo ""

# Step 4: Activate virtual environment
print_step "Activating virtual environment..."
if [ -d "venv" ]; then
    source venv/bin/activate
    print_success "Virtual environment activated: venv/"
elif [ -d ".venv" ]; then
    source .venv/bin/activate
    print_success "Virtual environment activated: .venv/"
elif [ -d "$HOME/.virtualenvs/tennisclub" ]; then
    source "$HOME/.virtualenvs/tennisclub/bin/activate"
    print_success "Virtual environment activated: ~/.virtualenvs/tennisclub"
else
    print_error "Virtual environment not found!"
    echo "  Looking for: venv/, .venv/, or ~/.virtualenvs/tennisclub"
    echo "  Run the setup script first: ./scripts/setup/pythonanywhere.sh"
    exit 1
fi

# Step 5: Verify .env.production exists
print_step "Checking production configuration..."
if [ ! -f ".env.production" ]; then
    print_warning ".env.production not found!"
    echo "  Copy .env.production.example to .env.production and configure it"
    echo "  See docs/PYTHONANYWHERE_DEPLOYMENT.md for details"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    print_success ".env.production found"
fi

# Step 6: Update dependencies
print_step "Updating dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
print_success "Dependencies updated"

# Step 7: Check current migration status
print_step "Checking database migration status..."
export FLASK_APP=wsgi.py
echo "Current migration:"
flask db current || print_warning "Could not determine current migration"
echo ""

# Step 8: Run database migrations
print_step "Running database migrations..."
if flask db upgrade; then
    print_success "Database migrations completed"
    echo "New migration:"
    flask db current
else
    print_error "Migration failed!"
    echo ""
    echo "Common fixes:"
    echo "  1. Check .env.production has correct DATABASE_URL"
    echo "  2. Run: python scripts/database/fix_migration.py"
    echo "  3. See: docs/PYTHONANYWHERE_DEPLOYMENT.md (Troubleshooting)"
    exit 1
fi

# Step 9: Optional email test
echo ""
print_step "Email configuration check..."
if grep -q "^MAIL_USERNAME=.\+@.\+\...\+" .env.production 2>/dev/null && \
   grep -q "^MAIL_PASSWORD=.\+" .env.production 2>/dev/null; then
    print_success "Email credentials configured"
    echo ""
    echo "To test email sending, run:"
    echo "  flask test-email your-email@example.com"
else
    print_warning "Email credentials may not be configured"
    echo "  See docs/PYTHONANYWHERE_DEPLOYMENT.md for email setup"
fi

# Step 10: Reload instructions
echo ""
print_header "Deployment Complete!"

print_success "All steps completed successfully!"
echo ""
print_warning "IMPORTANT: You must reload your web app for changes to take effect!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "How to Reload Your Web App:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Option 1: Web Interface (Recommended)"
echo "  1. Go to: https://www.pythonanywhere.com/user/\$USER/webapps/"
echo "  2. Click the green 'Reload' button"
echo ""
echo "Option 2: Command Line"
echo "  touch /var/www/\${USER}_pythonanywhere_com_wsgi.py"
echo ""
echo "After reloading:"
echo "  • Visit your site and test the changes"
echo "  • Check error logs if issues occur (Web tab → Error log)"
echo ""
echo "For troubleshooting, see: docs/PYTHONANYWHERE_DEPLOYMENT.md"
echo ""
