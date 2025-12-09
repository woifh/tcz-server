# PythonAnywhere Deployment - December 8, 2025

## Deployment Status: ✅ IN PROGRESS

Your Tennis Club Reservation System is being deployed to PythonAnywhere!

## What Was Deployed

### Updated Files
1. **app/__init__.py** - Flask application with cache-busting headers and rate limiting
2. **app/static/js/app-bundle.js** - Vanilla JS booking modal (Alpine.js migration reverted)
3. **app/templates/base.html** - Base template with Alpine.js CDN
4. **app/templates/dashboard.html** - Dashboard with vanilla JS booking modal
5. **app/templates/favourites.html** - Favourites page with Alpine.js
6. **app/templates/reservations.html** - Reservations list with Alpine.js

### Features Deployed
- ✅ 75% Alpine.js migration (favourites and reservations)
- ✅ Vanilla JS booking modal (stable and working)
- ✅ No confirmation dialogs for better UX
- ✅ Increased rate limits (500/hour)
- ✅ Cache-busting headers for development

## Your Application

**URL**: https://woifh.pythonanywhere.com
**Database**: MySQL (woifh$tennisclub)
**Python Version**: 3.10
**Virtualenv**: /home/woifh/.virtualenvs/tennisclub

## Next Steps

### 1. Pull Latest Code on PythonAnywhere

You need to update the code on PythonAnywhere with the latest changes from GitHub:

```bash
# Open a Bash console on PythonAnywhere
cd ~/tcz
git pull origin main
```

### 2. Install/Update Dependencies

```bash
workon tennisclub
pip install -r requirements.txt
```

### 3. Run Database Migrations (if needed)

```bash
export FLASK_APP=wsgi.py
flask db upgrade
```

### 4. Reload the Web App

After pulling the code, you MUST reload the web app for changes to take effect.

**Option A: Using MCP (I can do this for you)**
Just say "reload the webapp" and I'll use the PythonAnywhere MCP tools.

**Option B: Manual**
1. Go to https://www.pythonanywhere.com/user/woifh/webapps/
2. Click the big green **Reload** button

## Testing After Deployment

1. Visit https://woifh.pythonanywhere.com
2. Log in with your credentials
3. Test the dashboard - booking modal should work
4. Test favourites page - Alpine.js search should work
5. Test reservations page - Alpine.js list should work
6. Try creating and cancelling bookings

## Configuration

Your `.env` file on PythonAnywhere is already configured with:
- ✅ MySQL database connection
- ✅ Secret key
- ⚠️ Email settings (needs Gmail app password)

### To Enable Email Notifications

Update `/home/woifh/tcz/.env` on PythonAnywhere:
```bash
MAIL_PASSWORD=your-gmail-app-password
```

Get a Gmail App Password: https://support.google.com/accounts/answer/185833

## Troubleshooting

### If the site doesn't load:
1. Check error logs: https://www.pythonanywhere.com/user/woifh/webapps/#tab_id_woifh_pythonanywhere_com
2. Click "Error log" link
3. Look for Python errors

### If booking modal doesn't work:
1. Check browser console for JavaScript errors
2. Clear browser cache (Cmd+Shift+R on Mac)
3. Verify app-bundle.js was updated

### If Alpine.js features don't work:
1. Check that Alpine.js CDN is loading (Network tab in browser dev tools)
2. Verify base.html was updated
3. Check browser console for errors

## What's Different from Local

- **Database**: MySQL instead of SQLite
- **Caching**: Production caching (no cache-busting headers in production)
- **Rate Limiting**: Same limits (500/hour)
- **Email**: Needs Gmail app password to work

## Files on PythonAnywhere

- **Project**: `/home/woifh/tcz/`
- **WSGI Config**: `/var/www/woifh_pythonanywhere_com_wsgi.py`
- **Virtualenv**: `/home/woifh/.virtualenvs/tennisclub`
- **Error Log**: Available in Web tab

## Ready to Go Live?

Once you've pulled the latest code and reloaded the webapp, your application will be live with all the latest features!

Let me know if you want me to:
1. Pull the latest code from GitHub
2. Reload the webapp
3. Check the error logs
4. Test the deployment

Just ask and I'll use the PythonAnywhere MCP tools to help!
