"""Main orchestrator for Solio FPL automation.

This script performs the complete workflow:
1. Login to Solio (if not already logged in)
2. Run optimization solve
3. Parse results
4. Send email with results
"""

import argparse
import sys

from dotenv import load_dotenv

from .browser import create_browser_context
from .email_sender import send_results_email
from .login import ensure_logged_in
from .parser import format_results_text, parse_results_file
from .solve import run_solve_on_page

# Load environment variables from .env file
load_dotenv()


def main() -> int:
    """Run the complete Solio automation workflow.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    parser = argparse.ArgumentParser(
        description="Automate FPL optimization using Solio Analytics"
    )
    parser.add_argument(
        "--no-email",
        action="store_true",
        help="Skip sending email after solve",
    )
    parser.add_argument(
        "--no-solve",
        action="store_true",
        help="Skip solve (useful for testing email with existing results)",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Run browser with visible window (default is headless)",
    )
    parser.add_argument(
        "--horizon",
        type=int,
        metavar="weeks",
        help="Override horizon setting (1-10 gameweeks)",
    )
    parser.add_argument(
        "--ddp",
        type=float,
        metavar="probability",
        help="Override decision disruption probability (0.0-1.0)",
    )
    args = parser.parse_args()

    results_file = None

    if not args.no_solve:
        print("=" * 50)
        print("SOLIO FPL AUTOMATION")
        print("=" * 50)
        print()

        # Create browser context
        print("Starting browser...")
        # Default to headless unless --gui flag is used
        playwright, context = create_browser_context(headless=not args.gui)

        try:
            page = context.pages[0] if context.pages else context.new_page()

            # Step 1: Login if needed (this also navigates to Solio)
            if not ensure_logged_in(page, context):
                print("ERROR: Failed to log in")
                return 1

            # Step 3: Run solve
            print()
            print("Starting optimization solve...")
            
            # Prepare settings overrides from CLI args
            settings_overrides = {}
            if args.horizon is not None:
                settings_overrides['horizon_weeks'] = args.horizon
            if args.ddp is not None:
                settings_overrides['decision_disruption_probability'] = args.ddp
            
            solve_results = run_solve_on_page(page, settings_overrides=settings_overrides)

            if not solve_results or "output_file" not in solve_results:
                print("ERROR: Solve failed or no results captured")
                return 1

            results_file = solve_results["output_file"]

        finally:
            context.close()
            playwright.stop()
            print("Browser closed.")

    # Step 4: Parse and display results
    print()
    print("Parsing results...")

    if results_file:
        results = parse_results_file(results_file)
    else:
        # Find most recent results file
        from .config import OUTPUT_DIR

        result_files = list(OUTPUT_DIR.glob("results_*.html"))
        if not result_files:
            print("ERROR: No results files found")
            return 1

        latest_file = max(result_files, key=lambda f: f.stat().st_mtime)
        print(f"Using most recent results: {latest_file}")
        results = parse_results_file(latest_file)

    print()
    print(format_results_text(results))

    # Step 5: Send email
    if not args.no_email:
        print()
        print("Sending email...")
        try:
            send_results_email(results)
        except ValueError as e:
            print(f"Email configuration error: {e}")
            return 1
        except Exception as e:
            print(f"Email sending failed: {e}")
            return 1

    print()
    print("=" * 50)
    print("AUTOMATION COMPLETE")
    print("=" * 50)

    return 0


if __name__ == "__main__":
    sys.exit(main())
