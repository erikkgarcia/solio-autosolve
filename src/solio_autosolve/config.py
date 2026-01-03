from pathlib import Path

# URLs
SOLIO_URL = "https://fpl.solioanalytics.com/"

# Paths - relative to project root
# __file__ is at src/solio_autosolve/config.py
# .parent -> src/solio_autosolve/
# .parent.parent -> src/
# .parent.parent.parent -> project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
CHROME_PROFILE_DIR = PROJECT_ROOT / "chrome_profile"
OUTPUT_DIR = PROJECT_ROOT / "output"
CREDENTIALS_DIR = PROJECT_ROOT / "credentials"

# Ensure directories exist
CHROME_PROFILE_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
CREDENTIALS_DIR.mkdir(exist_ok=True)
