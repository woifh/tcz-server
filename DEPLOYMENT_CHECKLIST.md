# PythonAnywhere Deployment Checklist

Print this and check off each step as you complete it!

## Pre-Deployment
- [ ] Have PythonAnywhere account credentials ready
- [ ] Have Gmail account for email notifications
- [ ] Have Gmail App Password generated
- [ ] Know your desired admin email and password

## Database Setup
- [ ] Logged into PythonAnywhere
- [ ] Went to Databases tab
- [ ] Set MySQL password
- [ ] Created database: `yourusername$tennisclub`
- [ ] Wrote down database password: ___________________

## Code Setup
- [ ] Opened Bash console
- [ ] Cloned repository: `git clone https://github.com/woifh/tcz.git`
- [ ] Changed to directory: `cd tcz`
- [ ] Created virtualenv: `mkvirtualenv --python=/usr/bin/python3.10 tennisclub`
- [ ] Installed dependencies: `pip install -r requirements.txt`

## Configuration
- [ ] Generated SECRET_KEY
- [ ] Created .env file: `nano .env`
- [ ] Filled in DATABASE_URL with correct values
- [ ] Filled in SECRET_KEY
- [ ] Filled in MAIL_USERNAME (Gmail)
- [ ] Filled in MAIL_PASSWORD (App Password)
- [ ] Saved .env file (Ctrl+O, Enter, Ctrl+X)

## Database Initialization
- [ ] Set FLASK_APP: `export FLASK_APP=wsgi.py`
- [ ] Ran migrations: `flask db upgrade`
- [ ] Initialized courts: `python3 init_db.py`
- [ ] Created admin user: `flask create-admin --name "Admin" --email "admin@tennisclub.de" --password "YourPassword"`
- [ ] Wrote down admin credentials:
  - Email: ___________________
  - Password: ___________________

## Web App Configuration
- [ ] Went to Web tab
- [ ] Clicked "Add a new web app"
- [ ] Selected "Manual configuration"
- [ ] Selected "Python 3.10"
- [ ] Clicked on WSGI configuration file
- [ ] Deleted all content
- [ ] Pasted new WSGI configuration
- [ ] Replaced `yourusername` with actual username
- [ ] Saved WSGI file
- [ ] Set Virtualenv path: `/home/yourusername/.virtualenvs/tennisclub`
- [ ] Added static files mapping:
  - URL: `/static/`
  - Directory: `/home/yourusername/tcz/app/static/`

## Launch
- [ ] Clicked green "Reload" button
- [ ] Visited: `https://yourusername.pythonanywhere.com`
- [ ] Site loads without errors
- [ ] Can see login page
- [ ] Can log in with admin credentials
- [ ] Dashboard displays correctly
- [ ] Can create a test reservation
- [ ] Can cancel a test reservation

## Post-Deployment Testing
- [ ] Email notifications working (check spam folder)
- [ ] All pages load correctly
- [ ] No errors in error log
- [ ] Static files (CSS, JS) loading
- [ ] Mobile view works

## Security
- [ ] Changed PythonAnywhere account password
- [ ] Using strong SECRET_KEY
- [ ] Using Gmail App Password (not regular password)
- [ ] Admin password is strong
- [ ] .env file not committed to git

## Documentation
- [ ] Saved database password securely
- [ ] Saved admin credentials securely
- [ ] Bookmarked PythonAnywhere dashboard
- [ ] Bookmarked app URL

## Optional Enhancements
- [ ] Set up database backup schedule
- [ ] Configure custom domain (paid accounts)
- [ ] Set up monitoring/alerts
- [ ] Create additional admin accounts
- [ ] Import existing member data

---

## Quick Reference

**Your PythonAnywhere Username**: ___________________

**Your App URL**: https://_____________________.pythonanywhere.com

**Database Name**: _____________________$tennisclub

**Admin Email**: ___________________

**Virtualenv Path**: /home/_____________________/.virtualenvs/tennisclub

**Project Path**: /home/_____________________/tcz

---

## Emergency Commands

**View error log:**
```bash
tail -f /var/log/yourusername.pythonanywhere.com.error.log
```

**Restart virtualenv:**
```bash
workon tennisclub
```

**Update code:**
```bash
cd ~/tcz
git pull origin main
```

**Reload web app:**
Go to Web tab → Click green "Reload" button

---

**Date Deployed**: ___________________

**Deployed By**: ___________________

**Notes**: 
_____________________________________________
_____________________________________________
_____________________________________________
