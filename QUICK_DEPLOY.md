# Quick Deployment Guide

## Automated Setup (5 minutes)

### 1. Log in to PythonAnywhere
- Go to: https://www.pythonanywhere.com/login/
- Username: `woifh`
- Password: `Sh4CiLC+%B-Mh.Z`

### 2. Create MySQL Database
- Go to **Databases** tab
- Create new database: `woifh$tennisclub`
- Set a password and **save it** (you'll need it in step 4)

### 3. Open Bash Console
- Go to **Consoles** tab
- Click "Bash" to start a new console

### 4. Run Deployment Script
```bash
# Download and run the script
wget https://raw.githubusercontent.com/woifh/tcz/main/deploy_pythonanywhere.sh
chmod +x deploy_pythonanywhere.sh
./deploy_pythonanywhere.sh
```

The script will ask you for:
- MySQL password (from step 2)
- Email address (for sending notifications)
- Email password (use Gmail App Password)
- Admin name, email, and password

## Manual Configuration (5 minutes)

### 5. Create Web App
- Go to **Web** tab
- Click **"Add a new web app"**
- Choose **"Manual configuration"**
- Select **"Python 3.10"**

### 6. Configure WSGI File
- Click on the WSGI configuration file link
- **Delete all content**
- Copy and paste this:

```python
import sys
import os

# Add your project directory to the sys.path
project_home = '/home/woifh/tcz'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(os.path.join(project_home, '.env'))

# Import Flask app
from wsgi import application
```

- Click **Save**

### 7. Set Virtual Environment
- In the **Virtualenv** section, enter:
```
/home/woifh/.virtualenvs/tennisclub
```

### 8. Configure Static Files
- In **Static files** section, click **"Enter URL"**
- Add:
  - **URL**: `/static/`
  - **Directory**: `/home/woifh/tcz/app/static/`

### 9. Reload Web App
- Click the big green **"Reload woifh.pythonanywhere.com"** button

### 10. Test Your App
- Visit: https://woifh.pythonanywhere.com
- Log in with your admin credentials

## Troubleshooting

### Check Error Logs
If something doesn't work:
1. Go to **Web** tab
2. Click **"Error log"** link
3. Look for Python errors at the bottom

### Common Issues

**"No module named 'flask_limiter'"**
```bash
workon tennisclub
pip install Flask-Limiter
```

**"Can't connect to MySQL"**
- Check DATABASE_URL in `/home/woifh/tcz/.env`
- Verify database name is `woifh$tennisclub`

**Static files not loading**
- Verify path: `/home/woifh/tcz/app/static/`
- Click Reload button again

**Email not sending**
- Use Gmail App Password, not regular password
- Enable "Less secure app access" if needed

## After Deployment

### Create Test Members
Log in as admin and create some test members through the web interface.

### Change Your Password
**IMPORTANT**: Change your PythonAnywhere password:
- Go to **Account** tab
- Click **"Change password"**

### Update Application
When you make changes:
```bash
cd ~/tcz
git pull origin main
workon tennisclub
pip install -r requirements.txt
# Then reload web app from Web tab
```

## Support

- Full guide: `PYTHONANYWHERE_DEPLOYMENT.md`
- PythonAnywhere Help: https://help.pythonanywhere.com/
- Your app: https://woifh.pythonanywhere.com

## Summary

✅ Total time: ~10-15 minutes
✅ Automated: Database setup, dependencies, initialization
✅ Manual: Web app configuration (WSGI, virtualenv, static files)
✅ Result: Live app at woifh.pythonanywhere.com
