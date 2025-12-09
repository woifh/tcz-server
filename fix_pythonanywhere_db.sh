#!/bin/bash
# Fix PythonAnywhere Database Migration Issues
# This script stamps the database to the correct version and applies pending migrations

echo "🔧 Fixing PythonAnywhere Database..."

# Activate virtual environment
source ~/.virtualenvs/tennisclub/bin/activate

# Set Flask app
export FLASK_APP=wsgi.py

# Navigate to project directory
cd ~/tcz

echo "📍 Current migration status:"
flask db current

echo ""
echo "🏷️  Stamping database to migration 088504aa5508 (firstname/lastname columns)..."
flask db stamp 088504aa5508

echo ""
echo "⬆️  Applying pending migrations (including is_short_notice field)..."
flask db upgrade

echo ""
echo "📍 New migration status:"
flask db current

echo ""
echo "🔄 Reloading webapp..."
touch /var/www/woifh_pythonanywhere_com_wsgi.py

echo ""
echo "✅ Database fix complete!"
echo ""
echo "🌐 Test your application at: https://woifh.pythonanywhere.com"
echo ""
echo "If you still see errors, check the error logs:"
echo "  - PythonAnywhere error log: https://www.pythonanywhere.com/user/woifh/files/var/log/"
echo "  - Application logs in the webapp dashboard"
