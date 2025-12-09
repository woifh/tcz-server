# Quick Update Guide for PythonAnywhere

## 🚀 Deploy Latest Changes

I've uploaded a deployment script to PythonAnywhere. Here's how to use it:

### Step 1: Open a Bash Console

1. Go to https://www.pythonanywhere.com/
2. Click on **Consoles** tab
3. Click **Bash** to start a new console

### Step 2: Run the Deployment Script

Copy and paste this command:

```bash
cd ~/tcz && bash deploy_update.sh
```

This script will:
- ✅ Pull latest code from GitHub
- ✅ Install/update dependencies
- ✅ Run database migrations
- ✅ Show you the status

### Step 3: Reload the Webapp

After the script completes, tell me to **"reload the webapp"** and I'll do it for you using MCP!

Or do it manually:
1. Go to https://www.pythonanywhere.com/user/woifh/webapps/
2. Click the big green **Reload** button

### Step 4: Test

Visit https://woifh.pythonanywhere.com and test:
- Dashboard with booking modal
- Favourites page with search
- Reservations list
- Creating and cancelling bookings

---

## Alternative: Manual Commands

If you prefer to run commands manually:

```bash
cd ~/tcz
git pull origin main
workon tennisclub
pip install -r requirements.txt
export FLASK_APP=wsgi.py
flask db upgrade
```

Then reload the webapp (tell me or do it manually).

---

## What Gets Updated

When you pull from GitHub, you'll get:
- ✅ Alpine.js migration (75% complete)
- ✅ Vanilla JS booking modal (stable)
- ✅ No confirmation dialogs
- ✅ Increased rate limits
- ✅ All bug fixes and improvements

---

## Need Help?

Just tell me:
- "reload the webapp" - I'll reload it via MCP
- "check error logs" - I'll check for errors
- "show me the files" - I'll list what's on PythonAnywhere

The deployment script is ready and waiting at `/home/woifh/tcz/deploy_update.sh`!
