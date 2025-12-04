#!/bin/bash
# PythonAnywhere Deployment Script for Tennis Club Reservation System
# Run this script in a PythonAnywhere Bash console

set -e  # Exit on error

echo "=========================================="
echo "Tennis Club Reservation System Deployment"
echo "=========================================="
echo ""

# Configuration
USERNAME="woifh"
PROJECT_NAME="tcz"
VENV_NAME="tennisclub"
REPO_URL="https://github.com/woifh/tcz.git"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Check if we're on PythonAnywhere
if [[ ! "$HOSTNAME" =~ "pythonanywhere.com" ]]; then
    print_warning "This script is designed for PythonAnywhere. Proceeding anyway..."
fi

# Step 1: Clone repository
echo ""
echo "Step 1: Cloning repository..."
if [ -d "$HOME/$PROJECT_NAME" ]; then
    print_warning "Directory $PROJECT_NAME already exists. Pulling latest changes..."
    cd "$HOME/$PROJECT_NAME"
    git pull origin main
else
    cd "$HOME"
    git clone "$REPO_URL"
    print_status "Repository cloned successfully"
fi

cd "$HOME/$PROJECT_NAME"

# Step 2: Create virtual environment
echo ""
echo "Step 2: Setting up virtual environment..."
if [ -d "$HOME/.virtualenvs/$VENV_NAME" ]; then
    print_warning "Virtual environment already exists. Skipping creation..."
else
    mkvirtualenv --python=/usr/bin/python3.10 "$VENV_NAME"
    print_status "Virtual environment created"
fi

# Activate virtual environment
source "$HOME/.virtualenvs/$VENV_NAME/bin/activate"
print_status "Virtual environment activated"

# Step 3: Install dependencies
echo ""
echo "Step 3: Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
print_status "Dependencies installed"

# Step 4: Collect database information
echo ""
echo "Step 4: Database Configuration"
echo "================================"
print_warning "You need to create a MySQL database first!"
echo ""
echo "Go to: https://www.pythonanywhere.com/user/$USERNAME/databases/"
echo "Create a database named: ${USERNAME}\$tennisclub"
echo ""
read -p "Have you created the database? (yes/no): " db_created

if [[ "$db_created" != "yes" ]]; then
    print_error "Please create the database first, then run this script again."
    exit 1
fi

# Get database password
echo ""
read -sp "Enter your MySQL password: " db_password
echo ""

# Step 5: Generate SECRET_KEY
echo ""
echo "Step 5: Generating SECRET_KEY..."
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
print_status "SECRET_KEY generated"

# Step 6: Get email configuration
echo ""
echo "Step 6: Email Configuration"
echo "============================"
echo "For Gmail, you need an App Password (not your regular password)"
echo "Guide: https://support.google.com/accounts/answer/185833"
echo ""
read -p "Email address (e.g., your-email@gmail.com): " email_address
read -sp "Email password (App Password): " email_password
echo ""

# Step 7: Create .env file
echo ""
echo "Step 7: Creating .env file..."
cat > "$HOME/$PROJECT_NAME/.env" << EOF
# Database Configuration
DATABASE_URL=mysql+pymysql://${USERNAME}:${db_password}@${USERNAME}.mysql.pythonanywhere-services.com/${USERNAME}\$tennisclub

# Flask Configuration
SECRET_KEY=${SECRET_KEY}
FLASK_ENV=production

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=${email_address}
MAIL_PASSWORD=${email_password}
MAIL_DEFAULT_SENDER=noreply@tennisclub.de

# Application Settings
COURTS_COUNT=6
BOOKING_START_HOUR=6
BOOKING_END_HOUR=22
MAX_ACTIVE_RESERVATIONS=2
EOF

print_status ".env file created"

# Step 8: Initialize database
echo ""
echo "Step 8: Initializing database..."
export FLASK_APP=wsgi.py

# Run migrations
flask db upgrade
print_status "Database migrations completed"

# Initialize courts
python3 init_db.py
print_status "Courts initialized"

# Step 9: Create admin user
echo ""
echo "Step 9: Creating admin user..."
read -p "Admin name (default: Admin): " admin_name
admin_name=${admin_name:-Admin}

read -p "Admin email (default: admin@tennisclub.de): " admin_email
admin_email=${admin_email:-admin@tennisclub.de}

read -sp "Admin password: " admin_password
echo ""

flask create-admin --name "$admin_name" --email "$admin_email" --password "$admin_password"
print_status "Admin user created"

# Step 10: Create WSGI configuration file
echo ""
echo "Step 10: Creating WSGI configuration..."
WSGI_FILE="$HOME/wsgi_config.py"
cat > "$WSGI_FILE" << EOF
import sys
import os

# Add your project directory to the sys.path
project_home = '/home/${USERNAME}/${PROJECT_NAME}'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(os.path.join(project_home, '.env'))

# Import Flask app
from wsgi import application
EOF

print_status "WSGI configuration file created at: $WSGI_FILE"

# Final instructions
echo ""
echo "=========================================="
echo "Deployment Script Completed!"
echo "=========================================="
echo ""
print_status "All automated steps completed successfully!"
echo ""
echo "NEXT STEPS (Manual - Web Interface):"
echo "====================================="
echo ""
echo "1. Go to the Web tab: https://www.pythonanywhere.com/user/$USERNAME/webapps/"
echo ""
echo "2. Click 'Add a new web app'"
echo "   - Choose 'Manual configuration'"
echo "   - Select 'Python 3.10'"
echo ""
echo "3. Configure WSGI file:"
echo "   - Click on the WSGI configuration file link"
echo "   - Delete all content"
echo "   - Copy content from: $WSGI_FILE"
echo "   - Or run: cat $WSGI_FILE"
echo ""
echo "4. Set Virtual Environment:"
echo "   - In the 'Virtualenv' section, enter:"
echo "   - /home/$USERNAME/.virtualenvs/$VENV_NAME"
echo ""
echo "5. Configure Static Files:"
echo "   - In 'Static files' section, add:"
echo "   - URL: /static/"
echo "   - Directory: /home/$USERNAME/$PROJECT_NAME/app/static/"
echo ""
echo "6. Reload your web app (big green button)"
echo ""
echo "7. Visit: https://$USERNAME.pythonanywhere.com"
echo ""
echo "Admin Credentials:"
echo "  Email: $admin_email"
echo "  Password: [the one you just entered]"
echo ""
print_warning "IMPORTANT: Change your PythonAnywhere password after deployment!"
echo ""
echo "For detailed troubleshooting, see: PYTHONANYWHERE_DEPLOYMENT.md"
echo ""
