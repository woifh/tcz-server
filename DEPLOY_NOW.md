# Deploy to PythonAnywhere - Quick Start Guide

Follow these steps to deploy your Tennis Club Reservation System to PythonAnywhere.

## 🚀 Quick Deployment (15 minutes)

### Step 1: Log in to PythonAnywhere
1. Go to: https://www.pythonanywhere.com/login/
2. Log in with your account (or create a free account)

### Step 2: Create MySQL Database (5 min)
1. Go to the **Databases** tab
2. Set a MySQL password if you haven't already
3. Create a new database:
   - Database name: `yourusername$tennisclub` (replace `yourusername` with your actual username)
   - **Write down your password!** You'll need it later.

### Step 3: Clone Your Repository (2 min)
1. Go to the **Consoles** tab
2. Click **"Bash"** to start a new console
3. Run these commands:
```bash
git clone https://github.com/woifh/tcz.git
cd tcz
```

### Step 4: Create Virtual Environment (2 min)
```bash
mkvirtualenv --python=/usr/bin/python3.10 tennisclub
pip install -r requirements.txt
```

### Step 5: Create .env File (3 min)
```bash
nano .env
```

Copy and paste this (replace the values with your actual information):
```bash
# Database Configuration
DATABASE_URL=mysql+pymysql://yourusername:yourpassword@yourusername.mysql.pythonanywhere-services.com/yourusername$tennisclub

# Flask Configuration
SECRET_KEY=your-super-secret-key-change-this
FLASK_ENV=production

# Email Configuration (Gmail example)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-gmail-app-password
MAIL_DEFAULT_SENDER=noreply@tennisclub.de

# Application Settings
COURTS_COUNT=6
BOOKING_START_HOUR=6
BOOKING_END_HOUR=22
MAX_ACTIVE_RESERVATIONS=2
```

**Important:**
- Generate a SECRET_KEY: `python3 -c "import secrets; print(secrets.token_hex(32))"`
- For Gmail, use an [App Password](https://support.google.com/accounts/answer/185833)
- Save: Press `Ctrl+O`, then `Enter`, then `Ctrl+X`

### Step 6: Initialize Database (2 min)
```bash
export FLASK_APP=wsgi.py
flask db upgrade
python3 init_db.py
```

Create admin user:
```bash
flask create-admin --name "Admin" --email "admin@tennisclub.de" --password "YourStrongPassword"
```

### Step 7: Configure Web App (3 min)

#### 7a. Create Web App
1. Go to the **Web** tab
2. Click **"Add a new web app"**
3. Choose **"Manual configuration"**
4. Select **"Python 3.10"**

#### 7b. Configure WSGI File
1. Click on the **WSGI configuration file** link
2. **Delete all content** and replace with:

```python
import sys
import os

# Add your project directory to the sys.path
project_home = '/home/yourusername/tcz'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(os.path.join(project_home, '.env'))

# Import Flask app
from wsgi import application
```

**Replace `yourusername` with your actual PythonAnywhere username!**

3. Click **Save**

#### 7c. Set Virtual Environment
In the **Virtualenv** section, enter:
```
/home/yourusername/.virtualenvs/tennisclub
```

#### 7d. Configure Static Files
In the **Static files** section, add:
- **URL**: `/static/`
- **Directory**: `/home/yourusername/tcz/app/static/`

### Step 8: Reload and Test (1 min)
1. Click the big green **"Reload"** button
2. Visit: `https://yourusername.pythonanywhere.com`
3. Log in with your admin credentials

## ✅ Success Checklist

- [ ] Database created and password saved
- [ ] Repository cloned
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] .env file created with correct values
- [ ] Database initialized
- [ ] Admin user created
- [ ] Web app configured
- [ ] WSGI file updated
- [ ] Virtual environment path set
- [ ] Static files configured
- [ ] Web app reloaded
- [ ] Site is accessible

## 🔧 Troubleshooting

### Check Error Logs
1. Go to **Web** tab
2. Click **"Error log"** link
3. Look at the bottom for recent errors

### Common Issues

**"No module named 'flask_limiter'"**
```bash
workon tennisclub
pip install Flask-Limiter
```

**"Can't connect to MySQL"**
- Check DATABASE_URL in `.env` file
- Verify database name: `yourusername$tennisclub`
- Check username and password

**"ImportError: No module named 'dotenv'"**
```bash
workon tennisclub
pip install python-dotenv
```

**Static files not loading**
- Verify path: `/home/yourusername/tcz/app/static/`
- Click Reload button again

**Email not sending**
- Use Gmail App Password (not regular password)
- Check MAIL_* settings in .env

### View Full Error Log
```bash
tail -f /var/log/yourusername.pythonanywhere.com.error.log
```

## 🔄 Updating Your App

When you push changes to GitHub:
```bash
cd ~/tcz
git pull origin main
workon tennisclub
pip install -r requirements.txt  # If dependencies changed
flask db upgrade  # If database schema changed
```

Then reload the web app from the Web tab.

## 📧 Email Configuration

### Gmail Setup
1. Go to Google Account settings
2. Security → 2-Step Verification
3. App passwords → Generate new password
4. Use this password in your .env file

### Test Email
```bash
workon tennisclub
cd ~/tcz
flask test-email --to your-email@example.com
```

## 🔐 Security

After deployment:
- [ ] Change SECRET_KEY to a strong random value
- [ ] Use strong admin password
- [ ] Keep .env file secure (never commit to git)
- [ ] Regularly backup database
- [ ] Monitor error logs

## 📊 Monitoring

### Database Backup
```bash
mysqldump -u yourusername -h yourusername.mysql.pythonanywhere-services.com -p yourusername$tennisclub > backup.sql
```

### Check App Status
- Error log: Python errors
- Server log: HTTP requests
- Access log: All requests

## 🆘 Need Help?

- **PythonAnywhere Help**: https://help.pythonanywhere.com/
- **PythonAnywhere Forums**: https://www.pythonanywhere.com/forums/
- **Full Documentation**: See `PYTHONANYWHERE_DEPLOYMENT.md`

## 🎉 Next Steps

After successful deployment:
1. Test all functionality (login, booking, cancellation)
2. Create test member accounts
3. Test email notifications
4. Share the URL with your club members!

---

**Your app will be live at**: `https://yourusername.pythonanywhere.com`

Good luck! 🚀
