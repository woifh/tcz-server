# PythonAnywhere Deployment Guide

This guide walks you through deploying database changes and updates to your Tennis Club application on PythonAnywhere.

## Prerequisites

- PythonAnywhere account with web app already set up
- SSH access to PythonAnywhere (available on paid accounts)
- Git repository pushed to origin with latest changes

## Deployment Steps

### Step 1: Connect to PythonAnywhere

You can deploy using either:

**Option A: PythonAnywhere Bash Console** (Recommended for quick updates)
1. Log in to https://www.pythonanywhere.com
2. Go to "Consoles" tab
3. Start a new "Bash" console

**Option B: SSH** (If you have a paid account)
```bash
ssh your-username@ssh.pythonanywhere.com
```

### Step 2: Navigate to Your Project Directory

```bash
cd ~/tcz
# or wherever your project is located
```

### Step 3: Pull Latest Changes from Git

```bash
# Check current status
git status

# Pull latest changes
git pull origin main
```

### Step 4: Activate Virtual Environment

```bash
# Activate your virtual environment
source venv/bin/activate
# or if using .venv:
# source .venv/bin/activate
```

### Step 5: Install/Update Dependencies

```bash
# Update pip
pip install --upgrade pip

# Install any new dependencies
pip install -r requirements.txt
```

### Step 6: Run Database Migrations

```bash
# Check current migration status
flask db current

# Run migrations to update database schema
flask db upgrade

# Verify the migration was successful
flask db current
```

### Step 7: Reload Your Web App

**Important:** You must reload your web app for changes to take effect.

**Option A: Via Web Interface**
1. Go to the "Web" tab in PythonAnywhere
2. Click the green "Reload" button for your web app

**Option B: Via Command Line**
```bash
# Replace 'yourusername' with your actual PythonAnywhere username
touch /var/www/yourusername_pythonanywhere_com_wsgi.py
```

### Step 8: Verify Deployment

1. Visit your web app URL
2. Test the functionality that was changed
3. Check the error log if something doesn't work:
   - Go to "Web" tab
   - Click on "Error log" link
   - Look for recent errors

## Common Issues and Solutions

### Issue: Migration Fails

**Solution:**
```bash
# Check what migrations are available
flask db history

# Try to see if there's a specific error
flask db upgrade --sql  # Shows SQL that would be executed

# If migration is stuck, you may need to manually check the database
mysql -h yourusername.mysql.pythonanywhere-services.com -u yourusername -p yourusername$tennisclub
```

### Issue: Changes Don't Appear After Reload

**Solutions:**
1. Make sure you reloaded the web app (Step 7)
2. Clear your browser cache
3. Check if the changes were actually pulled from git:
   ```bash
   git log -1  # Should show your latest commit
   ```
4. Check error logs in PythonAnywhere Web tab

### Issue: Database Connection Error

**Solution:**
Check your `.env.production` file exists and has correct database credentials:
```bash
cat .env.production | grep DATABASE_URL
# Should show: mysql+pymysql://username:password@server/database
```

### Issue: Import Errors

**Solution:**
Make sure all dependencies are installed:
```bash
pip list  # Check installed packages
pip install -r requirements.txt  # Reinstall if needed
```

## Email Configuration on PythonAnywhere

If you're deploying email changes, ensure your production environment variables are set:

```bash
# Check email configuration
cat .env.production | grep MAIL_
```

Should show:
```
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=noreply@tennisclub.de
```

Test email sending:
```bash
flask test-email your-email@gmail.com
```

## Quick Deployment Checklist

Use this checklist for routine deployments:

- [ ] Commit and push all local changes to git
- [ ] SSH/Console into PythonAnywhere
- [ ] Navigate to project directory (`cd ~/tcz`)
- [ ] Pull latest changes (`git pull origin main`)
- [ ] Activate virtual environment (`source venv/bin/activate`)
- [ ] Update dependencies if needed (`pip install -r requirements.txt`)
- [ ] Run database migrations (`flask db upgrade`)
- [ ] Reload web app (green "Reload" button in Web tab)
- [ ] Test the deployment on live site
- [ ] Check error logs if issues occur

## Database Backup (Recommended Before Major Changes)

```bash
# Backup database before running migrations
mysqldump -h yourusername.mysql.pythonanywhere-services.com \
  -u yourusername -p \
  yourusername$tennisclub > backup_$(date +%Y%m%d).sql

# To restore if needed:
# mysql -h yourusername.mysql.pythonanywhere-services.com \
#   -u yourusername -p \
#   yourusername$tennisclub < backup_YYYYMMDD.sql
```

## Rolling Back a Migration

If a migration causes issues:

```bash
# Downgrade to previous migration
flask db downgrade

# Or downgrade to specific version
flask db downgrade <revision_id>

# Check history to find revision IDs
flask db history
```

## Getting Help

- **PythonAnywhere Forums:** https://www.pythonanywhere.com/forums/
- **PythonAnywhere Help:** Click "Send feedback" in PythonAnywhere interface
- **Project Issues:** Check the error log in PythonAnywhere Web tab

## Current Database Schema

Latest migration: `7347717de84b` - Initial migration with member audit log

To check current schema:
```bash
flask db current
```

## Environment Files on PythonAnywhere

You should have two environment files:
- `.env.production` - Used by PythonAnywhere (contains production credentials)
- `.env` - Your local development file (should NOT be deployed)

Make sure `.env.production` is properly configured with production credentials.
