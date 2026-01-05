"""Exploration script for discovering Solio settings interface."""

import time
from datetime import datetime

from playwright.sync_api import Page

from .browser import create_browser_context
from .config import OUTPUT_DIR
from .login import ensure_logged_in


def explore_settings_interface(page: Page) -> None:
    """
    Explore the settings interface to see what options are available.
    This helps us understand what settings we can configure.
    """
    print("\nExploring settings interface...")
    
    try:
        # Look for settings button/tab
        settings_button = page.locator('button[role="tab"]', has_text="Settings")
        
        if not settings_button.is_visible():
            print("Settings tab not found or not visible")
            # Try alternative selector - settings icon button
            settings_icon = page.locator('button[aria-haspopup="dialog"]').locator('svg.lucide-settings')
            if settings_icon.count() > 0:
                print("Found settings icon button")
                settings_icon.first.click()
                time.sleep(1)
                
                # Capture what's in the dialog
                dialog_content = page.content()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                settings_file = OUTPUT_DIR / f"settings_dialog_{timestamp}.html"
                settings_file.write_text(dialog_content, encoding="utf-8")
                print(f"Saved settings dialog to: {settings_file}")
            return
        
        print("Found Settings tab")
        settings_button.click()
        time.sleep(2)  # Wait for settings to load
        
        # Capture the settings content
        settings_content = page.content()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        settings_file = OUTPUT_DIR / f"settings_page_{timestamp}.html"
        settings_file.write_text(settings_content, encoding="utf-8")
        print(f"Saved settings page to: {settings_file}")
        
        # Try to identify available settings
        # Look for input fields, sliders, dropdowns, etc.
        inputs = page.locator('input, select, button[role="switch"]').all()
        print(f"Found {len(inputs)} potential setting controls")
        
        for i, input_elem in enumerate(inputs[:10]):  # Show first 10
            try:
                elem_type = input_elem.get_attribute("type") or "unknown"
                elem_name = input_elem.get_attribute("name") or input_elem.get_attribute("aria-label") or f"control_{i}"
                print(f"  - {elem_name}: {elem_type}")
            except Exception:
                pass
        
        # Now explore the horizon setting (10 GWs button)
        print("\nExploring horizon setting...")
        horizon_button = page.locator('button:has-text("GWs")').first
        if horizon_button.is_visible():
            print("Found horizon button, clicking to open dialog...")
            horizon_button.click()
            time.sleep(1)  # Wait for dialog to open
            
            # Capture the horizon dialog
            horizon_content = page.content()
            horizon_file = OUTPUT_DIR / f"horizon_dialog_{timestamp}.html"
            horizon_file.write_text(horizon_content, encoding="utf-8")
            print(f"Saved horizon dialog to: {horizon_file}")
            
            # Look for slider or input controls in the dialog
            dialog = page.locator('[role="dialog"]')
            if dialog.count() > 0:
                dialog_inputs = dialog.locator('input, [role="slider"]').all()
                print(f"Found {len(dialog_inputs)} controls in horizon dialog:")
                for i, elem in enumerate(dialog_inputs[:5]):
                    try:
                        elem_type = elem.get_attribute("type") or elem.get_attribute("role") or "unknown"
                        elem_label = elem.get_attribute("aria-label") or elem.get_attribute("aria-valuetext") or f"control_{i}"
                        elem_value = elem.get_attribute("value") or elem.get_attribute("aria-valuenow") or "N/A"
                        print(f"  - {elem_label}: {elem_type} (value: {elem_value})")
                    except Exception as e:
                        print(f"  - Error reading control {i}: {e}")
            
            # Close the dialog (press Escape or click outside)
            page.keyboard.press("Escape")
            time.sleep(0.5)
        else:
            print("Horizon button not found")
    
    except Exception as e:
        print(f"Error exploring settings: {e}")


def main() -> None:
    """Run the settings exploration script."""
    print("Starting Solio settings exploration...")
    
    p, context = create_browser_context(headless=False)
    page = context.new_page()
    
    try:
        if not ensure_logged_in(page, context):
            print("Failed to log in")
            return
        
        # Wait for page to fully load
        page.wait_for_load_state("networkidle", timeout=30000)
        time.sleep(2)
        
        # Run exploration
        explore_settings_interface(page)
        
        print("\nExploration complete! Check the output/ directory for captured HTML.")
        print("Press Ctrl+C to exit...")
        
        # Keep browser open for manual inspection
        try:
            page.wait_for_timeout(300000)  # Wait 5 minutes
        except KeyboardInterrupt:
            print("\nExiting...")
    
    except Exception as e:
        print(f"Error during exploration: {e}")
    finally:
        context.close()
        p.stop()


if __name__ == "__main__":
    main()
