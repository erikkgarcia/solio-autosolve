#!/usr/bin/env python
"""Debug why settings aren't being applied."""

from playwright.sync_api import sync_playwright
from solio_autosolve.config import CHROME_PROFILE_DIR, OUTPUT_DIR
from solio_autosolve.login import ensure_logged_in
import time

print('Debugging settings application...')

with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        user_data_dir=str(CHROME_PROFILE_DIR),
        headless=True,
        args=['--disable-blink-features=AutomationControlled']
    )
    page = context.pages[0] if context.pages else context.new_page()
    
    # Login
    print('Logging in...')
    ensure_logged_in(page, context)
    
    # Wait for page to fully load (same as in solve.py)
    page.wait_for_load_state("networkidle", timeout=30000)
    time.sleep(2)
    
    # Save page HTML to see what's there
    html = page.content()
    output_file = OUTPUT_DIR / "page_before_settings.html"
    output_file.write_text(html, encoding='utf-8')
    print(f'Saved page HTML to: {output_file}')
    
    # Check if horizon button exists
    horizon_button = page.locator('button:has-text("GWs")')
    count = horizon_button.count()
    print(f'\nHorizon button count: {count}')
    
    if count > 0:
        print('Found horizon button(s):')
        for i in range(count):
            btn = horizon_button.nth(i)
            text = btn.text_content()
            print(f'  [{i}]: {text}')
    else:
        print('No horizon button found!')
        print('Searching for any button with "GW" in text...')
        gw_buttons = page.locator('button:has-text("GW")').all()
        print(f'Found {len(gw_buttons)} buttons with "GW":')
        for i, btn in enumerate(gw_buttons[:5]):
            print(f'  [{i}]: {btn.text_content()[:50]}')
    
    context.close()

print('\nDebug complete!')
