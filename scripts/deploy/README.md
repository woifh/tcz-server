# Deployment Scripts

This directory contains scripts for deploying the Tennis Club Reservation System to production environments.

## Available Scripts

### `pythonanywhere.sh`

Main deployment script for updating an existing PythonAnywhere deployment.

**Usage:**
```bash
cd ~/tcz
./scripts/deploy/pythonanywhere.sh
```

**What it does:**
- Pulls latest code from GitHub
- Activates virtual environment
- Updates Python dependencies
- Runs database migrations
- Verifies configuration
- Provides reload instructions

**Prerequisites:**
- First-time setup must be completed (see `scripts/setup/pythonanywhere.sh`)
- `.env.production` file must exist with valid credentials
- Virtual environment must exist (`venv/`, `.venv/`, or `~/.virtualenvs/tennisclub`)

## Deployment Workflow

### Regular Updates (Code/Schema Changes)

1. **On your local machine:**
   ```bash
   git add .
   git commit -m "Description of changes"
   git push origin main
   ```

2. **On PythonAnywhere (Bash console):**
   ```bash
   cd ~/tcz
   ./scripts/deploy/pythonanywhere.sh
   ```

3. **Reload your web app:**
   - Go to Web tab in PythonAnywhere
   - Click green "Reload" button

### First-Time Setup

For initial deployment, use the setup script instead:
```bash
./scripts/setup/pythonanywhere.sh
```

See [docs/PYTHONANYWHERE_DEPLOYMENT.md](../../docs/PYTHONANYWHERE_DEPLOYMENT.md) for detailed setup instructions.

## Troubleshooting

### Script says "wsgi.py not found"
- Make sure you're running the script from the project root directory (`~/tcz`)

### "Virtual environment not found"
- Run first-time setup: `./scripts/setup/pythonanywhere.sh`
- Or create manually: `python3 -m venv venv`

### Migration fails
- Check database credentials in `.env.production`
- Try: `python scripts/database/fix_migration.py`
- See troubleshooting guide in docs/

### Changes don't appear after deployment
- Did you reload the web app? (Step 3 above is required!)
- Check error log in PythonAnywhere Web tab
- Verify git pull actually downloaded changes: `git log -1`

## Additional Resources

- **Full deployment guide:** [docs/PYTHONANYWHERE_DEPLOYMENT.md](../../docs/PYTHONANYWHERE_DEPLOYMENT.md)
- **Database tools:** [scripts/database/](../database/)
- **Setup scripts:** [scripts/setup/](../setup/)
