"""Optimization functionality for Solio FPL."""

import time
from datetime import datetime

from playwright.sync_api import Page

from .browser import create_browser_context
from .config import OUTPUT_DIR
from .login import ensure_logged_in


def click_optimise_button(page: Page) -> bool:
    """Click the Optimise button to start the solve. Returns True if successful."""
    print("Looking for Optimise button...")

    optimise_button = page.get_by_role("button", name="Optimise")

    if not optimise_button.is_visible():
        print("Optimise button not found or not visible")
        return False

    print("Clicking Optimise button...")
    optimise_button.click()
    return True


def wait_for_solve_completion(page: Page, timeout_seconds: int = 300) -> bool:
    """
    Wait for the optimization solve to complete.
    Returns True if solve completed, False if timed out.
    """
    print(f"Waiting for solve to complete (timeout: {timeout_seconds}s)...")

    start_time = time.time()

    while time.time() - start_time < timeout_seconds:
        # Check if "Preview Result" appears (indicates solve is complete)
        preview_result = page.locator('text="Preview Result"')
        if preview_result.is_visible():
            print("Preview Result found! Solve complete.")
            return True

        elapsed = int(time.time() - start_time)
        print(f"  Waiting for results... ({elapsed}s elapsed)")
        time.sleep(5)  # Check every 5 seconds

    print("Solve timed out!")
    return False


def run_solve_on_page(page: Page, timeout_seconds: int = 300) -> dict | None:
    """
    Run the optimization solve on an existing page.

    Args:
        page: Playwright page that is already logged in to Solio.
        timeout_seconds: Maximum time to wait for solve completion.

    Returns:
        Results dictionary with output_file path, or None if failed.
    """
    # Wait for page to fully load
    page.wait_for_load_state("networkidle", timeout=30000)
    time.sleep(2)

    # Click the Optimise button
    if not click_optimise_button(page):
        print("Failed to click Optimise button")
        return None

    # Wait for solve to complete
    if not wait_for_solve_completion(page, timeout_seconds=timeout_seconds):
        print("Solve did not complete in time")
        # Still try to fetch whatever results are available

    # Fetch and return results
    results = fetch_results(page)
    return results


def fetch_results(page: Page) -> dict:
    """
    Fetch the optimization results from the page.
    Returns a dictionary with the results.
    """
    print("Fetching results...")

    results = {
        "timestamp": datetime.now().isoformat(),
        "transfers": [],
        "html": "",
    }

    # Wait for page to be stable
    page.wait_for_load_state("networkidle", timeout=10000)
    time.sleep(2)

    # Capture the full HTML for reference
    results["html"] = page.content()

    # Try to extract transfer information
    # This will depend on how results are displayed - adjust selectors as needed
    try:
        # Look for transfer-related elements
        # Common patterns: player names with "OUT" and "IN" indicators
        transfer_elements = page.locator("[data-transfer]").all()
        if transfer_elements:
            for elem in transfer_elements:
                results["transfers"].append(elem.text_content())

        # Alternative: try to find player names in results
        player_elements = page.locator('.player-name, [class*="player"]').all()
        if player_elements:
            results["players"] = [
                elem.text_content() for elem in player_elements[:20]
            ]  # Limit to 20

    except Exception as e:
        print(f"Error extracting detailed results: {e}")

    # Save HTML to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = OUTPUT_DIR / f"results_{timestamp}.html"
    output_file.write_text(results["html"], encoding="utf-8")
    print(f"Saved results HTML to: {output_file}")

    results["output_file"] = output_file
    return results


def run_solve() -> dict | None:
    """
    Run the full optimization solve process.
    Returns the results dictionary or None if failed.
    """
    print("Starting Solio AutoSolve - Optimization...")

    p, context = create_browser_context()
    page = context.new_page()

    try:
        # First, ensure we're logged in
        if not ensure_logged_in(page, context):
            print("Failed to log in")
            return None

        # Wait for page to fully load
        page.wait_for_load_state("networkidle", timeout=30000)
        time.sleep(2)

        # Click the Optimise button
        if not click_optimise_button(page):
            print("Failed to click Optimise button")
            return None

        # Wait for solve to complete
        if not wait_for_solve_completion(page, timeout_seconds=300):
            print("Solve did not complete in time")
            # Still try to fetch whatever results are available

        # Fetch and return results
        results = fetch_results(page)

        print("Solve completed successfully!")
        return results

    except Exception as e:
        print(f"Error during solve: {e}")
        return None
    finally:
        context.close()
        p.stop()


def main():
    """Run the solve and print results."""
    results = run_solve()

    if results:
        print("\n=== SOLVE RESULTS ===")
        print(f"Timestamp: {results['timestamp']}")
        if results.get("transfers"):
            print(f"Transfers: {results['transfers']}")
        if results.get("players"):
            print(f"Players found: {results['players'][:10]}")  # Print first 10
        print("HTML saved to output folder")
    else:
        print("Solve failed - no results")


if __name__ == "__main__":
    main()
