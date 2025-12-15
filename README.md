# Solio AutoSolve

Automated FPL (Fantasy Premier League) optimization using [Solio Analytics](https://fpl.solioanalytics.com/). This tool automatically logs in, runs optimization solves, parses the results, and sends you an email summary of recommended transfers.

## Features

- **Automated Login**: Uses a persistent Chrome profile to maintain Google OAuth sessions
- **Optimization Solve**: Clicks the "Optimise" button and waits for results
- **Results Parsing**: Extracts transfer recommendations, projected points, and gameweek plans
- **Email Notifications**: Sends formatted HTML emails with your optimization results
- **Scheduled Runs**: Can be configured to run automatically via Windows Task Scheduler
- **Headless Mode**: Runs without a visible browser window for background automation

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- Google Chrome browser installed
- A Solio Analytics account (with Google login)
- Gmail account with an [App Password](https://myaccount.google.com/apppasswords) for sending emails

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
   
   Edit `.env` with your email credentials:
   ```
   EMAIL_ADDRESS=your.email@gmail.com
   EMAIL_PASSWORD=your-16-char-app-password
   ```

5. **Initial login** (required once to set up Chrome profile):
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
```

## Scheduled Runs (Windows Task Scheduler)

Set up automatic daily runs:

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
│   ├── email_sender.py  # Email functionality
│   ├── login.py         # Login and authentication
│   ├── main.py          # Main orchestrator
│   ├── parser.py        # Results HTML parsing
│   └── solve.py         # Optimization solve logic
├── scripts/
│   ├── run_scheduled.ps1       # PowerShell runner for Task Scheduler
│   ├── run_scheduled.bat       # Batch file alternative
│   └── setup_scheduled_task.ps1 # Creates Windows scheduled task
├── chrome_profile/      # Persistent Chrome profile (gitignored)
├── output/              # Saved results HTML files (gitignored)
├── logs/                # Scheduler logs (gitignored)
├── .env                 # Email credentials (gitignored)
├── pyproject.toml       # Project configuration
└── README.md
```

## Customization for Your Own Use

If you want to use this project for yourself, you'll need to change:

### 1. Email Configuration

Edit `.env` with your own email credentials:

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

### 2. Paths (if not using default location)

Edit `scripts/run_scheduled.ps1` and `scripts/setup_scheduled_task.ps1` to update:
- `$ProjectDir` - Path to your project folder

### 3. Schedule Time

When setting up the scheduled task:
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

1. Check your `.env` file has correct credentials
2. For Gmail, ensure you're using an App Password, not your regular password
3. Check that "Less secure app access" isn't blocking you (shouldn't be needed with App Passwords)

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

4. **Email**: Sends both plain text and HTML formatted results to your email.

## License

MIT License - feel free to use and modify for your own FPL automation needs.

## Disclaimer

This project is not affiliated with Solio Analytics or the official Fantasy Premier League. Use at your own risk and be respectful of Solio's servers - don't run solves too frequently.
