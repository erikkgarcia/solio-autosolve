# Solio AutoSolve

Automated FPL (Fantasy Premier League) optimization using [Solio Analytics](https://fpl.solioanalytics.com/). This tool automatically logs in, runs optimization solves, parses the results, and sends you an email summary of recommended transfers.

## Features

- **Automated Login**: Uses a persistent Chrome profile to maintain Google OAuth sessions
- **Optimization Solve**: Clicks the "Optimise" button and waits for results
- **Results Parsing**: Extracts transfer recommendations, projected points, and gameweek plans
- **Email Notifications**: Sends formatted HTML emails via Gmail API (fast, reliable) or SMTP fallback
- **Scheduled Runs**: Can be configured to run automatically via Windows Task Scheduler
- **Headless Mode**: Runs without a visible browser window for background automation

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- Google Chrome browser installed
- A Solio Analytics account (with Google login)
- Gmail account (Gmail API recommended, or App Password for SMTP fallback)

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/solio-autosolve.git
   cd solio-autosolve
   ```

2. **Install dependencies**:
   ```bash
   uv sync
   ```

3. **Install Playwright browsers** (first time only):
   ```bash
   uv run playwright install chromium
   ```

4. **Create environment file**:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your email address:
   ```
   EMAIL_ADDRESS=your.email@gmail.com
   ```

5. **Set up Gmail API** (recommended for fast, reliable email delivery):
   
   a. Go to [Google Cloud Console](https://console.cloud.google.com/)
   
   b. Create a new project (e.g., "Solio AutoSolve")
   
   c. Enable the Gmail API:
      - Search for "Gmail API" → Click "Enable"
   
   d. Configure OAuth consent screen:
      - Go to "APIs & Services" → "OAuth consent screen"
      - Select "External" → Create
      - Fill in app name and your email
      - Add your email as a test user
   
   e. Create OAuth credentials:
      - Go to "APIs & Services" → "Credentials"
      - Click "Create Credentials" → "OAuth client ID"
      - Select "Desktop app" → Create
      - Download the JSON file
   
   f. Save the JSON file as:
      ```
      credentials/credentials.json
      ```
   
   g. Authorize the app:
      ```bash
      uv run solio-gmail-setup
      ```
      This opens a browser - sign in and authorize. Tokens are saved and auto-refresh.

   **Alternative: SMTP with App Password** (if you prefer not to use Gmail API)
   
   Add to `.env`:
   ```
   EMAIL_PASSWORD=your-16-char-app-password
   ```
   Create an App Password at: https://myaccount.google.com/apppasswords

6. **Initial login** (required once to set up Chrome profile):
   ```bash
   uv run solio-login
   ```
   
   This opens a browser window. Log in with your Google account, then close the browser.

## Usage

### Full Automation (Login + Solve + Email)

```bash
# With visible browser
uv run solio

# Headless mode (no browser window)
uv run solio --headless

# Skip email (just solve and display results)
uv run solio --no-email

# Email existing results without running a new solve
uv run solio --no-solve
```

### Individual Commands

```bash
# Login only (sets up Chrome profile)
uv run solio-login

# Run solve only
uv run solio-solve

# Parse and display latest results
uv run solio-parse

# Email latest results
uv run solio-email

# Set up/test Gmail API
uv run solio-gmail-setup
```

## Scheduled Runs

### Linux (systemd timers)

Set up automatic twice-daily runs on Linux/Raspberry Pi:

```bash
# Default times (10:00 AM and 6:00 PM)
./scripts/setup_scheduled.sh

# Custom times
./scripts/setup_scheduled.sh --morning 08:00 --evening 20:00

# Check timer status
systemctl --user list-timers

# View logs
journalctl --user -u solio-autosolve.service -n 50

# Run manually right now
systemctl --user start solio-autosolve.service

# Or just use the simple command
uv run solio

# Disable timers
systemctl --user stop solio-autosolve-morning.timer solio-autosolve-evening.timer
systemctl --user disable solio-autosolve-morning.timer solio-autosolve-evening.timer
```

**Note**: Timers will run even when you're not logged in (uses systemd lingering).

### Windows (Task Scheduler)

Set up automatic daily runs on Windows:

```powershell
# Daily at 10:00 AM
.\scripts\setup_scheduled_task.ps1 -Time "10:00"

# Twice daily (7 AM and 7 PM)
.\scripts\setup_scheduled_task.ps1 -Frequency "Twice"

# Test the scheduled task
schtasks /run /tn "Solio FPL AutoSolve"

# Remove the scheduled task
Unregister-ScheduledTask -TaskName "Solio FPL AutoSolve"
```

**Note**: The scheduled task only runs when your PC is on and you're logged in.

## Project Structure

```
solio-autosolve/
├── src/solio_autosolve/
│   ├── __init__.py
│   ├── browser.py       # Browser context management
│   ├── config.py        # Configuration and paths
│   ├── email_sender.py  # Email functionality (Gmail API + SMTP fallback)
│   ├── gmail_api.py     # Gmail API integration
│   ├── login.py         # Login and authentication
│   ├── main.py          # Main orchestrator
│   ├── parser.py        # Results HTML parsing
│   └── solve.py         # Optimization solve logic
├── scripts/
│   ├── run_scheduled.sh         # Bash runner for systemd/cron (Linux)
│   ├── setup_scheduled.sh       # Creates systemd timers (Linux)
│   ├── run_scheduled.ps1        # PowerShell runner for Task Scheduler (Windows)
│   ├── run_scheduled.bat        # Batch file alternative (Windows)
│   └── setup_scheduled_task.ps1 # Creates Windows scheduled task
├── credentials/         # Gmail API credentials (gitignored)
├── chrome_profile/      # Persistent Chrome profile (gitignored)
├── output/              # Saved results HTML files (gitignored)
├── logs/                # Scheduler logs (gitignored)
├── .env                 # Email address (gitignored)
├── pyproject.toml       # Project configuration
└── README.md
```

## Customization for Your Own Use

If you want to use this project for yourself, you'll need to change:

### 1. Email Configuration

**Option A: Gmail API (Recommended)**

Faster and more reliable. Follow the Gmail API setup in the Installation section above.

**Option B: SMTP with App Password**

Edit `.env` with your credentials:

```
EMAIL_ADDRESS=your.email@gmail.com
EMAIL_PASSWORD=your-app-password
```

For Gmail, create an App Password at: https://myaccount.google.com/apppasswords

For other providers, also set:
```
SMTP_SERVER=smtp.your-provider.com
SMTP_PORT=587
```

### 2. Paths

The scripts use relative paths, so no changes are needed. Just clone the repo anywhere and run from there.

### 3. Schedule Time

**Linux:**
```bash
./scripts/setup_scheduled.sh --morning 08:00 --evening 20:00
```

**Windows:**
```powershell
.\scripts\setup_scheduled_task.ps1 -Time "08:00"  # Your preferred time
```

### 4. Chrome Profile

Delete the `chrome_profile/` folder and run `uv run solio-login` to create a fresh profile with your own Google account.

## Troubleshooting

### "This browser or app may not be secure" during Google login

This happens because Google detects automation. The project uses real Chrome (not Chromium) with a persistent profile to avoid this. If it still occurs:
1. Delete `chrome_profile/` folder
2. Run `uv run solio-login` 
3. Complete the login manually in the browser window

### Unicode encoding errors in scheduled task

Fixed by using ASCII characters in output. If you see `?` characters for player names with accents (e.g., Muñoz), this is a Windows console limitation - the email will display correctly.

### Email not sending

**If using Gmail API:**
1. Run `uv run solio-gmail-setup` to check status
2. Ensure `credentials/credentials.json` exists
3. If `credentials/token.json` is missing, re-authorize by running the setup command

**If using SMTP:**
1. Check your `.env` file has correct `EMAIL_PASSWORD`
2. For Gmail, ensure you're using an App Password, not your regular password
3. SMTP emails may be delayed by Gmail - consider switching to Gmail API

### Solve timeout

The default timeout is 300 seconds (5 minutes). If solves consistently timeout:
- Check your internet connection
- The Solio servers might be under heavy load
- Try running at a different time

## How It Works

1. **Login**: Opens Chrome with a persistent profile. If not logged in, prompts for Google OAuth. The session is saved for future runs.

2. **Solve**: Navigates to Solio, clicks "Optimise", and polls for the "Preview Result" button to appear (indicates solve completion).

3. **Parse**: Extracts data from the results HTML using BeautifulSoup:
   - Total projected points
   - Transfer recommendations per gameweek
   - Expected points ranges and grades

4. **Email**: Sends both plain text and HTML formatted results via Gmail API (instant delivery) or SMTP fallback.

## License

MIT License - feel free to use and modify for your own FPL automation needs.

## Disclaimer

This project is not affiliated with Solio Analytics or the official Fantasy Premier League. Use at your own risk and be respectful of Solio's servers - don't run solves too frequently.
