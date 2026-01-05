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
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        # First, try the settings wheel button using XPath
        print("\nLooking for settings wheel button via XPath...")
        settings_wheel = page.locator('xpath=/html/body/div[1]/div/main/div[1]/div/div[4]/button')
        
        if settings_wheel.count() > 0 and settings_wheel.is_visible():
            print("Found settings wheel button, clicking...")
            settings_wheel.click()
            time.sleep(1)
            
            # Look for the dialog that opened
            dialog = page.locator('[role="dialog"]')
            if dialog.count() > 0:
                # First, click the "Settings" button to open the settings dialog
                settings_button = dialog.locator('button:has-text("Settings")').first
                if settings_button.count() > 0:
                    print("Found 'Settings' button in dialog, clicking...")
                    settings_button.click()
                    time.sleep(1.5)
                    
                    # Now look for the Optimisation tab (with wrench icon)
                    optimisation_tab = page.locator('button[role="tab"]:has-text("Optimisation")').first
                    if optimisation_tab.count() > 0:
                        print("Found 'Optimisation' tab, clicking...")
                        optimisation_tab.click()
                        time.sleep(1)
                        
                        # Now capture the optimisation settings content
                        optimisation_content = page.content()
                        optimisation_file = OUTPUT_DIR / f"optimisation_settings_{timestamp}.html"
                        optimisation_file.write_text(optimisation_content, encoding="utf-8")
                        print(f"Saved optimisation settings to: {optimisation_file}")
                        
                        # Look for all controls in the optimisation tab
                        print("\nExploring controls in Optimisation tab:")
                        
                        # Get the tab panel content
                        tab_panel = page.locator('[role="tabpanel"][aria-labelledby*="solver"]')
                        if tab_panel.count() > 0 and not tab_panel.get_attribute("hidden"):
                            controls = tab_panel.locator('input, select, button[role="switch"], [role="slider"], [role="checkbox"], [role="combobox"], textarea, label').all()
                            print(f"Found {len(controls)} controls in Optimisation tab:")
                            
                            for i, elem in enumerate(controls[:50]):  # Show first 50
                                try:
                                    tag = elem.evaluate("el => el.tagName.toLowerCase()")
                                    elem_type = elem.get_attribute("type") or elem.get_attribute("role") or tag
                                    elem_label = (
                                        elem.get_attribute("aria-label") 
                                        or elem.get_attribute("name")
                                        or elem.get_attribute("placeholder")
                                        or elem.text_content()[:60] if elem.text_content() else f"control_{i}"
                                    )
                                    elem_value = (
                                        elem.get_attribute("value") 
                                        or elem.get_attribute("aria-valuenow") 
                                        or elem.get_attribute("aria-checked")
                                        or elem.get_attribute("data-state")
                                        or "N/A"
                                    )
                                    print(f"  [{i}] {elem_label.strip()}: {elem_type} = {elem_value}")
                                except Exception as e:
                                    print(f"  [{i}] Error: {e}")
                        else:
                            print("Could not find visible Optimisation tab panel content")
                            # Just search for any visible settings-related controls
                            controls = page.locator('[role="dialog"] input, [role="dialog"] select, [role="dialog"] button[role="switch"], [role="dialog"] [role="slider"]').all()
                            print(f"Found {len(controls)} controls in dialog")
                            for i, elem in enumerate(controls[:20]):
                                try:
                                    elem_label = elem.text_content()[:40] if elem.text_content() else f"control_{i}"
                                    print(f"  [{i}] {elem_label.strip()}")
                                except:
                                    pass
                        
                        # Leave dialog open for inspection
                        print("\nOptimisation settings left open for manual inspection...")
                        return
                    else:
                        print("'Optimisation' tab not found after opening Settings dialog")
                else:
                    print("'Settings' button not found in dialog")
                    # Capture what we got
                    dialog_content = page.content()
                    dialog_file = OUTPUT_DIR / f"settings_wheel_dialog_{timestamp}.html"
                    dialog_file.write_text(dialog_content, encoding="utf-8")
                    print(f"Saved settings wheel dialog to: {dialog_file}")
            else:
                print("No dialog found after clicking settings wheel")
                page.keyboard.press("Escape")
        else:
            print("Settings wheel button not found or not visible")
        
        # Look for settings button/tab
        settings_button = page.locator('button[role="tab"]', has_text="Settings")
        
        if not settings_button.is_visible():
            print("Settings tab not found or not visible")
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
    
    p, context = create_browser_context(headless=True)
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
