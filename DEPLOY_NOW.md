# Deploy Latest Changes to PythonAnywhere

## Changes Pushed to GitHub ✅

The following changes have been committed and pushed to GitHub:
- Past booking validation (prevents bookings in the past)
- 15-minute cancellation window (prevents cancellations within 15 minutes of start)
- Future-only active reservations (only counts future reservations toward 2-reservation limit)

## Deploy to PythonAnywhere

### Option 1: Quick Deploy (Recommended)

1. **Open PythonAnywhere Bash Console**
   - Go to https://www.pythonanywhere.com/
   - Click on **Consoles** tab
   - Start a **Bash console** (or use an existing one)

2. **Run Deployment Commands**
   ```bash
   cd ~/tcz
   git pull origin main
   ```

3. **Reload Web App**
   - Go to the **Web** tab: https://www.pythonanywhere.com/user/S84AB/webapps/
   - Click the green **Reload** button for your webapp

### Option 2: Use Deployment Script

1. **Open PythonAnywhere Bash Console**

2. **Run the deployment script**
   ```bash
   cd ~/tcz
   bash deploy_update.sh
   ```

3. **Reload Web App**
   - Go to: https://www.pythonanywhere.com/user/S84AB/webapps/
   - Click the green **Reload** button

### Option 3: Manual Steps

If you prefer to do it manually:

```bash
# 1. Navigate to project
cd ~/tcz

# 2. Pull latest changes
git pull origin main

# 3. Activate virtual environment
source ~/.virtualenvs/tennisclub/bin/activate

# 4. Install any new dependencies (if needed)
pip install -r requirements.txt

# 5. Run migrations (if any)
export FLASK_APP=wsgi.py
flask db upgrade
```

Then reload the webapp from the Web tab.

## Verify Deployment

After reloading, test the following:

1. **Visit your site**: https://S84AB.pythonanywhere.com (or your custom domain)

2. **Test Past Booking Validation**:
   - Try to create a booking for yesterday
   - Should see error: "Buchungen in der Vergangenheit sind nicht möglich"

3. **Test 15-Minute Cancellation Window**:
   - Create a booking for 10 minutes from now
   - Try to cancel it
   - Should see error: "Stornierung nicht möglich. Buchungen können nur bis 15 Minuten vor Beginn storniert werden"

4. **Test Future-Only Active Reservations**:
   - Create 2 future bookings
   - Try to create a 3rd booking
   - Should see error: "Sie haben bereits 2 aktive Buchungen"
   - Past bookings should not count toward this limit

## Troubleshooting

### If Git Pull Fails

```bash
cd ~/tcz
git status
git stash  # If you have local changes
git pull origin main
```

### If Reload Doesn't Work

1. Check error logs:
   - Web tab → Click on "Error log" link
   - Look for Python errors

2. Verify virtual environment:
   - Web tab → Check "Virtualenv" section
   - Should be: `/home/S84AB/.virtualenvs/tennisclub`

3. Check WSGI configuration:
   - Web tab → Click on WSGI configuration file
   - Verify paths are correct

### If You See Import Errors

```bash
workon tennisclub
pip install -r requirements.txt
```

Then reload the webapp.

## What Was Changed

### app/services/validation_service.py
- Added check for past bookings in `validate_all_booking_constraints()`
- Only counts future reservations in `validate_member_reservation_limit()`

### app/services/reservation_service.py
- Added past booking check in `cancel_reservation()`
- Added 15-minute window check in `cancel_reservation()`
- Only returns future reservations in `get_member_active_reservations()`

## Need Help?

If you encounter any issues:
1. Check the error logs in PythonAnywhere
2. Verify the changes are in GitHub: https://github.com/woifh/tcz/commits/main
3. Make sure you reloaded the webapp after pulling changes

---

**Status**: ✅ Changes pushed to GitHub
**Next Step**: Deploy to PythonAnywhere using one of the options above
