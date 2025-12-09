#!/bin/bash
# PythonAnywhere Deployment Script for Tennis Club Reservation System

echo "=== PythonAnywhere Deployment Script ==="
echo ""
echo "This script will guide you through deploying to PythonAnywhere."
echo "Make sure you have:"
echo "  1. A PythonAnywhere account"
echo "  2. Your API token configured in .kiro/settings/mcp.json"
echo "  3. Git repository pushed to GitHub"
echo ""

# Get PythonAnywhere username
read -p "Enter your PythonAnywhere username: " PA_USERNAME

echo ""
echo "=== Step 1: Clone Repository on PythonAnywhere ==="
echo "Run these commands in a PythonAnywhere Bash console:"
echo ""
echo "git clone https://github.com/woifh/tcz.git"
echo "cd tcz"
echo ""

read -p "Press Enter when you've cloned the repository..."

echo ""
echo "=== Step 2: Create Virtual Environment ==="
echo "Run in PythonAnywhere console:"
echo ""
echo "mkvirtualenv --python=/usr/bin/python3.10 tennisclub"
echo "pip install -r requirements.txt"
echo ""

read -p "Press Enter when dependencies are installed..."

echo ""
echo "=== Step 3: Create MySQL Database ==="
echo "1. Go to PythonAnywhere → Databases tab"
echo "2. Create a new MySQL database"
echo "3. Note the database name, host, username, and password"
echo ""

read -p "Press Enter when database is created..."

echo ""
echo "=== Step 4: Configure Environment Variables ==="
echo "Create .env file in PythonAnywhere console:"
echo ""
echo "nano .env"
echo ""
echo "Add this content (replace with your values):"
echo ""
cat << 'EOF'
# Database Configuration
DATABASE_URL=mysql+pymysql://USERNAME:PASSWORD@USERNAME.mysql.pythonanywhere-services.com/USERNAME$tennisclub

# Flask Configuration
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
FLASK_ENV=production

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=noreply@tennisclub.de

# Application Settings
COURTS_COUNT=6
BOOKING_START_HOUR=6
BOOKING_END_HOUR=22
MAX_ACTIVE_RESERVATIONS=2
EOF
echo ""

read -p "Press Enter when .env file is created..."

echo ""
echo "=== Step 5: Initialize Database ==="
echo "Run in PythonAnywhere console:"
echo ""
echo "export FLASK_APP=wsgi.py"
echo "flask db upgrade"
echo "flask create-admin --name 'Admin' --email 'admin@tennisclub.de' --password 'YourPassword'"
echo "python3 init_db.py"
echo ""

read -p "Press Enter when database is initialized..."

echo ""
echo "=== Step 6: Configure Web App ==="
echo "1. Go to PythonAnywhere → Web tab"
echo "2. Click 'Add a new web app'"
echo "3. Choose 'Manual configuration'"
echo "4. Select 'Python 3.10'"
echo ""
echo "5. Edit WSGI file with this content:"
echo ""
cat << EOF
import sys
import os

project_home = '/home/$PA_USERNAME/tcz'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

from dotenv import load_dotenv
load_dotenv(os.path.join(project_home, '.env'))

from wsgi import application
EOF
echo ""
echo "6. Set Virtualenv to: /home/$PA_USERNAME/.virtualenvs/tennisclub"
echo ""
echo "7. Add Static files mapping:"
echo "   URL: /static/"
echo "   Directory: /home/$PA_USERNAME/tcz/app/static/"
echo ""

read -p "Press Enter when web app is configured..."

echo ""
echo "=== Step 7: Reload Web App ==="
echo "Click the green 'Reload' button in the Web tab"
echo ""
echo "Your app should be live at: https://$PA_USERNAME.pythonanywhere.com"
echo ""
echo "=== Deployment Complete! ==="
echo ""
echo "Next steps:"
echo "  1. Visit your app and test it"
echo "  2. Check error logs if something doesn't work"
echo "  3. Configure email settings properly"
echo ""
echo "For troubleshooting, see: PYTHONANYWHERE_DEPLOYMENT.md"
