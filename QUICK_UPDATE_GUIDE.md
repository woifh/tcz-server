# Quick Update Guide for PythonAnywhere

## Method 1: Using the Update Script (Recommended)

1. **Open a Bash console on PythonAnywhere**
   - Go to: https://www.pythonanywhere.com/user/woifh/consoles/
   - Click "Bash" to open a new console

2. **Run the update script**
   ```bash
   cd ~/tcz
   bash update_pythonanywhere.sh
   ```

3. **Reload your web app**
   - Go to: https://www.pythonanywhere.com/user/woifh/webapps/
   - Click the green **"Reload"** button

4. **Test the new feature**
   - Visit: https://woifh.pythonanywhere.com
   - Go to "Favoriten" page
   - Click "Favorit hinzufügen"
   - Try searching for a member

---

## Method 2: Manual Update (If script doesn't work)

1. **Open Bash console on PythonAnywhere**

2. **Navigate to project and pull changes**
   ```bash
   cd ~/tcz
   git pull origin main
   ```

3. **Activate virtual environment**
   ```bash
   source ~/.virtualenvs/tennisclub/bin/activate
   ```

4. **Update dependencies (if needed)**
   ```bash
   pip install -r requirements.txt --upgrade
   ```

5. **Run database migrations**
   ```bash
   export FLASK_APP=wsgi.py
   flask db upgrade
   ```

6. **Reload web app**
   - Go to: https://www.pythonanywhere.com/user/woifh/webapps/
   - Click the green **"Reload"** button

---

## What's New in This Update

✅ **Member Search Feature**
- Search for members by name or email
- Real-time search with debouncing
- Keyboard navigation support
- Accessible design with ARIA labels
- German localization

✅ **UI Improvements**
- Toast notifications instead of double alerts
- Better user experience when removing favourites

---

## Troubleshooting

### If you see errors after deployment:

1. **Check the error log**
   - Go to: https://www.pythonanywhere.com/user/woifh/files/var/log/
   - Look at the error log for your web app

2. **Common issues:**
   - **Database migration failed**: Run `flask db upgrade` again
   - **Module not found**: Run `pip install -r requirements.txt`
   - **Changes not visible**: Make sure you clicked the Reload button

3. **Clear browser cache**
   - Press Ctrl+Shift+R (or Cmd+Shift+R on Mac) to hard refresh

### Still having issues?

- Check if the web app is running: https://www.pythonanywhere.com/user/woifh/webapps/
- Restart the web app by clicking "Reload"
- Check the server logs for detailed error messages

---

## Quick Commands Reference

```bash
# Navigate to project
cd ~/tcz

# Pull latest changes
git pull origin main

# Activate virtual environment
source ~/.virtualenvs/tennisclub/bin/activate

# Run migrations
export FLASK_APP=wsgi.py
flask db upgrade

# Check if app is running
ps aux | grep wsgi
```

---

## Need Help?

If you encounter any issues during deployment, check:
- PythonAnywhere error logs
- The main deployment guide: `PYTHONANYWHERE_DEPLOYMENT.md`
- PythonAnywhere help: https://help.pythonanywhere.com/
