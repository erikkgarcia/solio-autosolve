"""Browser management utilities."""

from playwright.sync_api import BrowserContext, Playwright, sync_playwright

from .config import CHROME_PROFILE_DIR


def create_browser_context(headless: bool = False) -> tuple[Playwright, BrowserContext]:
    """
    Create a Playwright browser context using real Chrome with persistent profile.

    Args:
        headless: Run browser without visible window (default: False).

    Returns:
        Tuple of (playwright, context) - caller must close both.
    """
    print(f"Using persistent Chrome profile at: {CHROME_PROFILE_DIR}")

    p = sync_playwright().start()

    context = p.chromium.launch_persistent_context(
        user_data_dir=str(CHROME_PROFILE_DIR),
        executable_path="/usr/bin/chromium",  # <-- use system Chromium on the Pi
        headless=headless,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--window-size=1920,1080",
        ],
    )

    return p, context
