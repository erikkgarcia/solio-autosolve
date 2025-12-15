"""Send optimization results via email."""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import TypedDict

from dotenv import load_dotenv

from .parser import SolveResults, format_results_text, parse_results_file

# Load environment variables from .env file
load_dotenv()


class EmailConfig(TypedDict):
    """Email configuration dictionary."""

    email_address: str
    email_password: str
    smtp_server: str
    smtp_port: int


def get_email_config() -> EmailConfig:
    """Get email configuration from environment variables.

    Required environment variables:
        EMAIL_ADDRESS: Your email address (sender and recipient)
        EMAIL_PASSWORD: Your email password or app password
        SMTP_SERVER: SMTP server address (default: smtp.gmail.com)
        SMTP_PORT: SMTP server port (default: 587)

    Returns:
        Dictionary with email configuration.

    Raises:
        ValueError: If required environment variables are missing.
    """
    email_address = os.environ.get("EMAIL_ADDRESS")
    email_password = os.environ.get("EMAIL_PASSWORD")

    if not email_address or not email_password:
        raise ValueError(
            "Missing required environment variables.\n"
            "Please set:\n"
            "  EMAIL_ADDRESS - your email address\n"
            "  EMAIL_PASSWORD - your email/app password\n"
            "\n"
            "For Gmail, create an App Password at:\n"
            "  https://myaccount.google.com/apppasswords"
        )

    return {
        "email_address": email_address,
        "email_password": email_password,
        "smtp_server": os.environ.get("SMTP_SERVER", "smtp.gmail.com"),
        "smtp_port": int(os.environ.get("SMTP_PORT", "587")),
    }


def send_results_email(
    results: SolveResults,
    recipient: str | None = None,
    subject: str | None = None,
) -> None:
    """Send optimization results via email.

    Args:
        results: Parsed solve results to send.
        recipient: Email recipient (defaults to sender address).
        subject: Email subject (defaults to generated subject).

    Raises:
        ValueError: If email configuration is missing.
        smtplib.SMTPException: If email sending fails.
    """
    config = get_email_config()

    sender = config["email_address"]
    recipient = recipient or sender

    # Generate subject if not provided
    if not subject:
        if results.gameweek_plans:
            first_gw = results.gameweek_plans[0].gameweek
            last_gw = results.gameweek_plans[-1].gameweek
            subject = (
                f"Solio FPL Results: {first_gw}-{last_gw} ({results.total_points} pts)"
            )
        else:
            subject = "Solio FPL Optimization Results"

    # Create email message
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient

    # Plain text version
    text_content = format_results_text(results)
    msg.attach(MIMEText(text_content, "plain"))

    # HTML version
    html_content = format_results_html(results)
    msg.attach(MIMEText(html_content, "html"))

    # Send email
    with smtplib.SMTP(config["smtp_server"], config["smtp_port"]) as server:
        server.starttls()
        server.login(sender, config["email_password"])
        server.sendmail(sender, recipient, msg.as_string())

    print(f"Email sent successfully to {recipient}")


def format_results_html(results: SolveResults) -> str:
    """Format results as HTML for email.

    Args:
        results: Parsed solve results.

    Returns:
        HTML formatted string.
    """
    html_parts = [
        """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; }
                h1 { color: #1a472a; border-bottom: 2px solid #1a472a; padding-bottom: 10px; }
                .summary { background: #f5f5f5; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
                .summary p { margin: 5px 0; }
                .gameweek { border: 1px solid #ddd; border-radius: 8px; margin-bottom: 15px; padding: 15px; }
                .gw-header { display: flex; justify-content: space-between; margin-bottom: 10px; }
                .gw-title { font-size: 18px; font-weight: bold; }
                .grade { color: #059669; font-weight: bold; }
                .transfer { margin: 5px 0; padding: 8px; background: #e8f5e9; border-radius: 4px; }
                .transfer-out { color: #c62828; }
                .transfer-in { color: #2e7d32; }
                .arrow { margin: 0 10px; color: #666; }
                .no-transfers { color: #666; font-style: italic; }
            </style>
        </head>
        <body>
            <h1>⚽ Solio FPL Optimization Results</h1>
        """,
        f"""
            <div class="summary">
                <p><strong>Total Projected Points:</strong> {results.total_points}</p>
                <p><strong>Total Transfers:</strong> {results.total_transfers}</p>
                <p><strong>Final Bank:</strong> £{results.final_bank}m</p>
            </div>
        """,
    ]

    for plan in results.gameweek_plans:
        transfers_html = ""
        if plan.transfers:
            for t in plan.transfers:
                transfers_html += f"""
                    <div class="transfer">
                        <span class="transfer-out">{t.out_player}</span>
                        <span class="arrow">→</span>
                        <span class="transfer-in">{t.in_player}</span>
                    </div>
                """
        else:
            transfers_html = '<p class="no-transfers">No transfers this week</p>'

        html_parts.append(f"""
            <div class="gameweek">
                <div class="gw-header">
                    <span class="gw-title">{plan.gameweek}</span>
                    <span class="grade">{plan.grade} ({plan.points_range})</span>
                </div>
                <p>Transfers: {plan.transfers_used} | Bank: £{plan.bank}m</p>
                {transfers_html}
            </div>
        """)

    html_parts.append("""
        </body>
        </html>
    """)

    return "".join(html_parts)


def main() -> None:
    """Send the most recent results via email."""
    from .config import OUTPUT_DIR

    # Find most recent results file
    result_files = list(OUTPUT_DIR.glob("results_*.html"))
    if not result_files:
        print("No results files found in output directory.")
        return

    latest_file = max(result_files, key=lambda f: f.stat().st_mtime)
    print(f"Parsing: {latest_file}")

    results = parse_results_file(latest_file)
    print(format_results_text(results))
    print()

    try:
        send_results_email(results)
    except ValueError as e:
        print(f"Configuration error: {e}")
    except smtplib.SMTPException as e:
        print(f"Email sending failed: {e}")


if __name__ == "__main__":
    main()
