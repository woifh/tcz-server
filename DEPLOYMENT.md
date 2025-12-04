# PythonAnywhere Deployment Guide

This guide provides step-by-step instructions for deploying the Tennis Club Reservation System on PythonAnywhere.

## Prerequisites

- PythonAnywhere account (free or paid)
- MySQL database (included with paid accounts, or use free SQLite for testing)
- SMTP email credentials (Gmail, SendGrid, etc.)

## Step 1: Upload Code

1. Log in to PythonAnywhere
2. Open a Bash console
3. Clone or upload your repository:
   ```bash
   git clone <your-repository-url>
   cd tennis-club-reservation
   ```

## Step 2: Create Virtual Environment

```bash
mkvirtualenv --python=/usr/bin/python3.10 tennis-club
pip install -r requirements.txt
```

## Step 3: Configure Environment Variables

Create a `.env` file in the project root:

```bash
nano .env
```

Add the following variables:

```env
# Flask Configuration
SECRET_KEY=your-secret-key-here-change-this
FLASK_ENV=production

# Database Configuration
DATABASE_URL=mysql+pymysql://username:password@username.mysql.pythonanywhere-services.com/dbname

# Email Configuration (Gmail example)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=noreply@tennisclub.de
```

**Note:** For Gmail, you need to create an App Password:
1. Go to Google Account settings
2. Security → 2-Step Verification → App passwords
3. Generate a new app password for "Mail"

## Step 4: Set Up MySQL Database

### For Paid Accounts:

1. Go to the "Databases" tab in PythonAnywhere
2. Create a new MySQL database
3. Note the database name, username, and password
4. Update the `DATABASE_URL` in your `.env` file

### For Free Accounts (SQLite):

Update `.env` to use SQLite:
```env
DATABASE_URL=sqlite:///instance/tennis_club.db
```

## Step 5: Initialize Database

```bash
workon tennis-club
cd tennis-club-reservation

# Run database migrations
flask db upgrade

# Initialize courts (creates 6 courts)
flask init-courts

# Create admin user
flask create-admin
# Follow prompts to enter admin name, email, and password
```

## Step 6: Configure WSGI

1. Go to the "Web" tab in PythonAnywhere
2. Click "Add a new web app"
3. Choose "Manual configuration" and Python 3.10
4. Set the following:

### Source code directory:
```
/home/yourusername/tennis-club-reservation
```

### Working directory:
```
/home/yourusername/tennis-club-reservation
```

### WSGI configuration file:

Click on the WSGI configuration file link and replace its contents with:

```python
import sys
import os

# Add your project directory to the sys.path
project_home = '/home/yourusername/tennis-club-reservation'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Load environment variables
from dotenv import load_dotenv
load_dotenv(os.path.join(project_home, '.env'))

# Import the Flask app
from wsgi import application
```

## Step 7: Configure Static Files

In the "Web" tab, add static file mappings:

| URL | Directory |
|-----|-----------|
| `/static/` | `/home/yourusername/tennis-club-reservation/app/static/` |

## Step 8: Configure Virtualenv

In the "Web" tab, set the virtualenv path:

```
/home/yourusername/.virtualenvs/tennis-club
```

## Step 9: Reload Web App

Click the green "Reload" button in the "Web" tab.

## Step 10: Test the Application

1. Visit your PythonAnywhere URL: `https://yourusername.pythonanywhere.com`
2. Log in with the admin credentials you created
3. Test email functionality:
   ```bash
   flask test-email --to your-email@example.com
   ```

## Troubleshooting

### Error Logs

View error logs in the "Web" tab:
- Error log: Shows Python errors
- Server log: Shows HTTP requests
- Access log: Shows all requests

### Common Issues

**Database Connection Errors:**
- Verify `DATABASE_URL` is correct
- Check MySQL credentials
- Ensure database exists

**Email Not Sending:**
- Verify SMTP credentials
- Check firewall settings
- For Gmail, ensure App Password is used (not regular password)
- Check error logs for specific email errors

**Import Errors:**
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check virtualenv is activated
- Verify Python version (3.10+)

**Static Files Not Loading:**
- Check static file mappings in Web tab
- Ensure paths are absolute
- Click "Reload" after changes

### Database Migrations

To apply new migrations:

```bash
workon tennis-club
cd tennis-club-reservation
flask db upgrade
```

### Updating Code

```bash
workon tennis-club
cd tennis-club-reservation
git pull origin main
pip install -r requirements.txt  # If dependencies changed
flask db upgrade  # If database schema changed
```

Then reload the web app in the Web tab.

## Security Checklist

- [ ] Change `SECRET_KEY` to a strong random value
- [ ] Use environment variables for all sensitive data
- [ ] Enable HTTPS (automatic on PythonAnywhere)
- [ ] Use strong passwords for admin accounts
- [ ] Regularly backup the database
- [ ] Keep dependencies updated
- [ ] Monitor error logs regularly

## Backup Strategy

### Database Backup

```bash
# For MySQL
mysqldump -u username -p database_name > backup_$(date +%Y%m%d).sql

# For SQLite
cp instance/tennis_club.db backups/tennis_club_$(date +%Y%m%d).db
```

### Automated Backups

Set up a scheduled task in PythonAnywhere:
1. Go to "Tasks" tab
2. Create a new scheduled task
3. Set frequency (daily recommended)
4. Add backup command

## Monitoring

### Health Checks

Create a simple health check endpoint to monitor:
- Database connectivity
- Email service status
- Application uptime

### Performance

- Monitor response times in access logs
- Check database query performance
- Optimize slow queries if needed

## Support

For issues specific to:
- **PythonAnywhere:** Check their help pages or forums
- **Application:** Check error logs and this documentation
- **Email:** Verify SMTP provider documentation

## Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key | Random string |
| `FLASK_ENV` | Environment | `production` |
| `DATABASE_URL` | Database connection | `mysql+pymysql://...` |
| `MAIL_SERVER` | SMTP server | `smtp.gmail.com` |
| `MAIL_PORT` | SMTP port | `587` |
| `MAIL_USE_TLS` | Use TLS | `true` |
| `MAIL_USERNAME` | Email username | `user@gmail.com` |
| `MAIL_PASSWORD` | Email password | App password |
| `MAIL_DEFAULT_SENDER` | Default sender | `noreply@club.de` |

## Next Steps

After deployment:
1. Create member accounts
2. Test booking workflow
3. Configure court blocking
4. Train administrators
5. Announce to club members
