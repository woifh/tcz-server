# Local Testing Information

## ✅ Application is Running!

**Server URL**: http://127.0.0.1:5000

## Test Login Credentials

### Admin User
- **Email**: `admin@test.com`
- **Password**: `admin123`
- **Role**: Administrator
- **Permissions**: Full access to all features including member management, court blocking, and reservation overrides

### Member User
- **Email**: `member@test.com`
- **Password**: `member123`
- **Role**: Member
- **Permissions**: Can create reservations, manage favourites, view own bookings

## Database

- **Type**: SQLite
- **Location**: `instance/tennis_club.db`
- **Courts**: 6 courts (numbered 1-6) are pre-configured

## Alpine.js Status

✅ **Alpine.js v3.13.3 is loaded** and ready for migration
- Check browser console: `Alpine.version` should return `"3.13.3"`
- `[x-cloak]` CSS is present to prevent flash of unstyled content

## What to Test

### 1. Login Flow
- Go to http://127.0.0.1:5000
- Should redirect to login page
- Try logging in with admin or member credentials

### 2. Dashboard
- After login, you should see the court availability grid
- 6 courts (columns) × 15 time slots (rows, 06:00-21:00)
- All slots should be green (available) initially

### 3. Booking Flow
- Click on any green (available) slot
- Booking modal should open
- Fill in details and create a reservation
- Slot should turn red

### 4. Favourites
- Navigate to "Meine Favoriten" (Favourites)
- Try adding the other test user as a favourite
- Test the member search functionality

### 5. Reservations
- Navigate to "Meine Buchungen" (My Reservations)
- View your reservations
- Try cancelling a reservation

## Stopping the Server

The Flask development server is running in the background (Process ID: 4).

To stop it, you can either:
- Ask me to stop it
- Or run: `pkill -f "flask run"`

## Next Steps

Now that the app is running and you can test it:

1. **Test current functionality** to establish a baseline
2. **Verify Alpine.js is loaded** (check browser console)
3. **Begin migration** following `ALPINE_MIGRATION_GUIDE.md`

**Recommended migration order**:
1. Member Search (30 min) - Simplest component
2. Booking Modal (45 min) - Most used feature
3. Reservation Cancellation (30 min) - Better UX

## Troubleshooting

### Can't log in?
- Check credentials match exactly (case-sensitive)
- Check browser console for errors
- Verify database exists: `ls -la instance/`

### Alpine.js not working?
- Open browser console
- Type: `Alpine.version`
- Should see: `"3.13.3"`
- If not, hard refresh: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)

### Database issues?
- Delete and recreate: `rm instance/tennis_club.db && python3 create_test_user.py`

## Files Created

- `.env` - Environment configuration (SQLite database)
- `create_test_user.py` - Script to initialize database with test users
- `instance/tennis_club.db` - SQLite database file
- `venv/` - Python virtual environment

## Ready to Migrate!

Everything is set up and working. You can now:
- Test the current vanilla JS implementation
- Verify Alpine.js is loaded
- Start migrating components one by one

**Questions?** Just ask!
