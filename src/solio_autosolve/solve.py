"""Optimization functionality for Solio FPL."""

import time
from typing import Any

from playwright.sync_api import Page

from .browser import create_browser_context
from .config import OUTPUT_DIR
from .login import ensure_logged_in
from .settings import load_solver_settings


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


def apply_solver_settings(page: Page, settings: dict[str, Any]) -> bool:
    """
    Apply solver settings from configuration before running optimization.
    
    Args:
        page: Playwright page
        settings: Settings dictionary from solver_settings.yaml
    
    Returns:
        True if settings were applied successfully, False otherwise
    """
    print("\nApplying solver settings...")
    
    try:
        # Apply horizon setting (number of gameweeks to plan ahead)
        horizon_weeks = settings.get('horizon_weeks', 10)
        print(f"Setting horizon to {horizon_weeks} gameweeks...")
        
        # Click the horizon button to open the dialog
        horizon_button = page.locator('button:has-text("GWs")')
        if horizon_button.count() > 0:
            horizon_button.click()
            time.sleep(0.5)
            
            # Find the slider in the dialog
            # There might be 2 sliders: risk preference and horizon
            # Horizon slider has aria-valuemin="1" and aria-valuemax around 10
            slider = page.locator('[role="dialog"] [role="slider"][aria-valuemin="1"]').first
            
            if slider.count() > 0:
                # Get slider bounds
                min_val = int(slider.get_attribute("aria-valuemin") or "1")
                max_val = int(slider.get_attribute("aria-valuemax") or "10")
                current_val = int(slider.get_attribute("aria-valuenow") or "10")
                
                # Clamp horizon_weeks to valid range
                target_val = max(min_val, min(horizon_weeks, max_val))
                
                if current_val != target_val:
                    print(f"  Current: {current_val} GWs, Target: {target_val} GWs")
                    
                    # Focus on the slider
                    slider.focus()
                    time.sleep(0.2)
                    
                    # Use keyboard to set the value
                    # Press Home to go to minimum, then use arrow keys
                    page.keyboard.press("Home")
                    time.sleep(0.2)
                    
                    # Each arrow key press increments by 1
                    steps = target_val - min_val
                    for _ in range(steps):
                        page.keyboard.press("ArrowRight")
                        time.sleep(0.05)
                    
                    time.sleep(0.3)
                    
                    # Verify the change
                    new_val = int(slider.get_attribute("aria-valuenow") or str(current_val))
                    print(f"  Set horizon to {new_val} GWs")
                    
                    # Close dialog
                    page.keyboard.press("Escape")
                    time.sleep(0.5)
                    
                    return new_val == target_val
                else:
                    print(f"  Horizon already at {target_val} GWs")
                    page.keyboard.press("Escape")
                    time.sleep(0.5)
                    return True
            else:
                print("  Horizon slider not found in dialog")
                page.keyboard.press("Escape")
                return False
        else:
            print("  Horizon button not found")
            return False
        
    except Exception as e:
        print(f"Error applying settings: {e}")
        import traceback
        traceback.print_exc()
        return False
        
        # For now, just log what settings we would apply
        if "settings" in settings:
            for key, value in settings["settings"].items():
                print(f"  {key}: {value}")
        
        return True
    
    except Exception as e:
        print(f"Error applying settings: {e}")
        return False


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


def run_solve_on_page(page: Page, timeout_seconds: int = 300, apply_settings: bool = True) -> dict | None:
    """
    Run the optimization solve on an existing page.

    Args:
        page: Playwright page that is already logged in to Solio.
        timeout_seconds: Maximum time to wait for solve completion.
        apply_settings: Whether to apply settings from solver_settings.yaml

    Returns:
        Results dictionary with output_file path, or None if failed.
    """
    # Wait for page to fully load
    page.wait_for_load_state("networkidle", timeout=30000)
    time.sleep(2)

    # Apply settings if requested
    if apply_settings:
        settings = load_solver_settings()
        apply_solver_settings(page, settings)
        # Use timeout from settings
        timeout_seconds = settings.get("timeout", timeout_seconds)

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

    p, context = create_browser_context(headless=True)
    page = context.new_page()

    try:
        # First, ensure we're logged in
        if not ensure_logged_in(page, context):
            print("Failed to log in")
            return None

        # Wait for page to fully load
        page.wait_for_load_state("networkidle", timeout=30000)
        time.sleep(2)

        # Apply settings
        settings = load_solver_settings()
        apply_solver_settings(page, settings)
        timeout = settings.get("timeout", 300)

        # Click the Optimise button
        if not click_optimise_button(page):
            print("Failed to click Optimise button")
            return None

        # Wait for solve to complete
        if not wait_for_solve_completion(page, timeout_seconds=timeout):
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
