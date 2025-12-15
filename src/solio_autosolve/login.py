"""Login functionality for Solio FPL."""

import time

from playwright.sync_api import BrowserContext, Page

from .browser import create_browser_context
from .config import OUTPUT_DIR, SOLIO_URL


def is_logged_in(page: Page) -> bool:
    """Check if we're already logged in by seeing if the login dialog is NOT present."""
    try:
        # Give the page more time to load and process auth state
        page.wait_for_load_state("networkidle", timeout=15000)
        time.sleep(2)  # Extra wait for JS to process auth

        # If the login dialog is visible, we're not logged in
        dialog = page.locator('[data-slot="dialog-content"]')
        if dialog.is_visible():
            # Double-check - sometimes dialog appears briefly
            time.sleep(1)
            if dialog.is_visible():
                return False
        return True
    except Exception:
        return False


def login_to_solio(page: Page, context: BrowserContext) -> bool:
    """
    Handle the login flow when not already logged in.
    Returns True if login was successful.
    """
    # Wait for the login dialog to appear
    print("Waiting for login dialog...")
    page.wait_for_selector('[data-slot="dialog-content"]', timeout=10000)

    # Step 1: Accept the terms checkbox
    print("Accepting terms...")
    terms_checkbox = page.locator('button[role="checkbox"]#terms')
    terms_checkbox.click()

    # Step 2: Wait for the Google login button to become enabled
    print("Waiting for Google login button to be enabled...")
    google_button = page.get_by_role("button", name="Log in with Google")

    # Poll until the button is enabled
    max_wait = 5  # seconds
    start_time = time.time()
    while time.time() - start_time < max_wait:
        if google_button.is_enabled():
            break
        time.sleep(0.1)
    else:
        print("Google button did not become enabled in time")
        return False

    # Step 3: Click the Google login button and handle the popup or redirect
    print("Clicking Google login button...")
    google_button.click()

    # Wait for either a popup or a redirect to Google
    time.sleep(2)

    # Check if we got redirected (URL changed from Solio)
    if "google" in page.url.lower() or "accounts.google" in page.url.lower():
        print("Redirected to Google login page...")
        print("Please complete Google login in the browser...")
        try:
            page.wait_for_url("**/fpl.solioanalytics.com/**", timeout=180000)
            print("Redirected back to Solio!")
        except Exception as e:
            print(f"Waiting for redirect: {e}")
    else:
        # Check if there's a popup
        pages = context.pages
        if len(pages) > 1:
            popup_page = pages[-1]
            print("Google OAuth popup detected!")
            print("Please complete the Google login in the popup window...")
            try:
                # Wait for the popup to close by polling
                max_wait = 180  # 3 minutes
                start = time.time()
                while time.time() - start < max_wait:
                    if popup_page.is_closed():
                        break
                    time.sleep(0.5)
                print("Google popup closed!")
            except Exception as e:
                print(f"Popup handling: {e}")
        else:
            print("Waiting for authentication to complete...")

    # Give the main page time to process the auth callback
    time.sleep(3)

    # Wait for the dialog to close after successful login
    try:
        page.wait_for_selector(
            '[data-slot="dialog-content"]', state="hidden", timeout=30000
        )
        print("Login successful! Dialog closed.")
        return True
    except Exception as e:
        # Check if we're actually logged in despite the dialog check
        page.reload()
        time.sleep(2)
        if not page.locator('[data-slot="dialog-content"]').is_visible():
            print("Login successful after reload!")
            return True
        print(f"Login may have failed or timed out: {e}")
        return False


def ensure_logged_in(page: Page, context: BrowserContext) -> bool:
    """Navigate to Solio and ensure we're logged in. Returns True if successful."""
    print(f"Navigating to {SOLIO_URL}...")
    page.goto(SOLIO_URL)

    if is_logged_in(page):
        print("Already logged in from saved session!")
        return True
    else:
        print("Need to log in...")
        login_success = login_to_solio(page, context)
        if login_success:
            print("Logged in successfully!")
            print("Session saved in Chrome profile - future runs will be automatic.")
            return True
        else:
            print("Login failed or was cancelled.")
            return False


def main():
    """Run login and capture the page HTML after logging in."""
    print("Starting Solio AutoSolve - Login...")

    p, context = create_browser_context()
    page = context.new_page()

    try:
        if ensure_logged_in(page, context):
            # Wait for page to fully load
            print("Waiting for page to fully load...")
            page.wait_for_load_state("networkidle", timeout=30000)
            time.sleep(2)

            # Capture and save the HTML
            html_content = page.content()
            output_file = OUTPUT_DIR / "logged_in_page.html"
            output_file.write_text(html_content, encoding="utf-8")
            print(f"Saved page HTML to: {output_file}")

            # Keep browser open briefly
            print("Browser will stay open for 10 seconds...")
            time.sleep(10)
        else:
            print("Could not log in.")
            time.sleep(5)

    except Exception as e:
        print(f"Error during automation: {e}")
        time.sleep(5)
    finally:
        context.close()
        p.stop()


if __name__ == "__main__":
    main()
