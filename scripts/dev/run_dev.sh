#!/bin/bash

# Development server startup script
# Handles environment setup and starts Flask in development mode

echo "🚀 Starting Tennis Club Reservation System..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run ./setup_env.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Set development environment variables
export FLASK_ENV=development
export FLASK_DEBUG=1

# Initialize database if it doesn't exist
if [ ! -f "tennis_club_dev.db" ]; then
    echo "🗄️  Initializing SQLite database..."
    python3 -c "
import sys
sys.path.append('.')
from app import create_app
from app.models import Court, Member, BlockReason
from app import db
from werkzeug.security import generate_password_hash

app = create_app('development')
with app.app_context():
    db.create_all()
    
    # Create courts
    for i in range(1, 7):
        if not Court.query.filter_by(number=i).first():
            court = Court(number=i, status='active')
            db.session.add(court)
    
    # Create admin user
    if not Member.query.filter_by(email='admin@tennisclub.de').first():
        admin = Member(
            firstname='Admin', lastname='User',
            email='admin@tennisclub.de',
            password_hash=generate_password_hash('admin123'),
            role='admin'
        )
        db.session.add(admin)
    
    # Create test member
    if not Member.query.filter_by(email='member@tennisclub.de').first():
        member = Member(
            firstname='Test', lastname='Member',
            email='member@tennisclub.de',
            password_hash=generate_password_hash('member123'),
            role='member'
        )
        db.session.add(member)
    
    # Create block reasons
    admin_user = Member.query.filter_by(role='admin').first()
    if admin_user:
        for reason_name in ['Wartung', 'Wetter', 'Turnier', 'Kurs', 'Reparatur']:
            if not BlockReason.query.filter_by(name=reason_name).first():
                reason = BlockReason(name=reason_name, is_active=True, created_by_id=admin_user.id)
                db.session.add(reason)
    
    db.session.commit()
    print('✅ Database initialized')
"
fi

# Start the Flask development server
echo "🌐 Starting development server at http://127.0.0.1:5001"
echo "📝 Recent updates:"
echo "   ✅ Reservation hours: 08:00-22:00 (14 slots)"
echo "   ✅ Default blocking: 08:00-22:00 (full day)"
echo "   ✅ SQLite database (no MySQL required)"
echo "   ✅ Test accounts created:"
echo "      - Admin: admin@tennisclub.de / admin123"
echo "      - Member: member@tennisclub.de / member123"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 wsgi.py