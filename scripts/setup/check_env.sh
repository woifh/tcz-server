#!/bin/bash
echo "Checking environment configuration on PythonAnywhere"
echo "===================================================="
echo ""

if [ -f ".env.production" ]; then
    echo "✓ .env.production exists"
    echo ""
    echo "DATABASE_URL setting:"
    grep "^DATABASE_URL=" .env.production || echo "  WARNING: DATABASE_URL not set!"
    echo ""
    echo "MAIL settings:"
    grep "^MAIL_" .env.production || echo "  WARNING: No MAIL settings found!"
else
    echo "✗ .env.production does NOT exist"
    echo ""
    echo "You need to create it:"
    echo "  cp .env.production.example .env.production"
    echo "  nano .env.production"
    echo ""
    echo "Then fill in your production credentials."
fi
