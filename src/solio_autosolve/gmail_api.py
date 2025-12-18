"""Gmail API integration for sending emails.

This module uses the Gmail API with OAuth2 for reliable email delivery.
Tokens are stored locally and auto-refresh, so authentication is only
needed once.
"""

import base64
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from google.auth.external_account_authorized_user import (
    Credentials as ExternalCredentials,
)
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .config import CREDENTIALS_DIR

# Gmail API scopes - only need send permission
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

# Credential file paths
CREDENTIALS_FILE = CREDENTIALS_DIR / "credentials.json"
TOKEN_FILE = CREDENTIALS_DIR / "token.json"


def get_gmail_credentials() -> Credentials | ExternalCredentials:
    """Get or refresh Gmail API credentials.

    On first run, opens a browser for OAuth2 authorization.
    After that, tokens are saved and auto-refresh.

    Returns:
        Valid Gmail API credentials.

    Raises:
        FileNotFoundError: If credentials.json is not found.
    """
    creds: Credentials | ExternalCredentials | None = None

    # Check for existing token
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    # If no valid credentials, get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Refresh expired token
            creds.refresh(Request())
        else:
            # Need new authorization
            if not CREDENTIALS_FILE.exists():
                raise FileNotFoundError(
                    f"Gmail API credentials not found at: {CREDENTIALS_FILE}\n\n"
                    "To set up Gmail API:\n"
                    "1. Go to https://console.cloud.google.com/\n"
                    "2. Create a new project (or select existing)\n"
                    "3. Enable the Gmail API\n"
                    "4. Go to Credentials -> Create Credentials -> OAuth client ID\n"
                    "5. Select 'Desktop app' as application type\n"
                    "6. Download the JSON and save as:\n"
                    f"   {CREDENTIALS_FILE}"
                )

            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save token for future runs
        TOKEN_FILE.write_text(creds.to_json())
        print(f"Gmail API token saved to: {TOKEN_FILE}")

    return creds


def send_email_gmail_api(
    to: str,
    subject: str,
    text_content: str,
    html_content: str | None = None,
) -> None:
    """Send an email using the Gmail API.

    Args:
        to: Recipient email address.
        subject: Email subject.
        text_content: Plain text email body.
        html_content: Optional HTML email body.

    Raises:
        HttpError: If the Gmail API request fails.
        FileNotFoundError: If credentials are not set up.
    """
    creds = get_gmail_credentials()
    service = build("gmail", "v1", credentials=creds)

    # Create message
    if html_content:
        msg = MIMEMultipart("alternative")
        msg.attach(MIMEText(text_content, "plain"))
        msg.attach(MIMEText(html_content, "html"))
    else:
        msg = MIMEText(text_content, "plain")

    msg["To"] = to
    msg["Subject"] = subject

    # Encode message
    encoded_message = base64.urlsafe_b64encode(msg.as_bytes()).decode()

    # Send via Gmail API
    try:
        message = (
            service.users()
            .messages()
            .send(userId="me", body={"raw": encoded_message})
            .execute()
        )
        print(f"Email sent successfully via Gmail API (Message ID: {message['id']})")
    except HttpError as error:
        print(f"Gmail API error: {error}")
        raise


def is_gmail_api_configured() -> bool:
    """Check if Gmail API credentials are configured.

    Returns:
        True if credentials.json exists, False otherwise.
    """
    return CREDENTIALS_FILE.exists()


def is_gmail_api_authorized() -> bool:
    """Check if Gmail API has been authorized (token exists).

    Returns:
        True if token.json exists and is valid, False otherwise.
    """
    if not TOKEN_FILE.exists():
        return False

    try:
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        if creds.valid:
            return True
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            TOKEN_FILE.write_text(creds.to_json())
            return True
    except Exception:
        return False

    return False


def authorize_gmail_api() -> None:
    """Interactively authorize Gmail API access.

    This opens a browser window for OAuth2 authorization.
    Call this once to set up Gmail API access.
    """
    print("Authorizing Gmail API access...")
    print("A browser window will open for you to authorize access.")
    print()

    try:
        get_gmail_credentials()  # Called for side effect (authorization)
        print()
        print("Gmail API authorized successfully!")
        print(f"Token saved to: {TOKEN_FILE}")
    except FileNotFoundError as e:
        print(e)


def main() -> None:
    """Test Gmail API setup and send a test email."""
    from dotenv import load_dotenv

    load_dotenv()

    print("Gmail API Setup Check")
    print("=" * 40)

    if not is_gmail_api_configured():
        print(f"❌ credentials.json not found at: {CREDENTIALS_FILE}")
        print()
        print("To set up Gmail API:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a new project (or select existing)")
        print("3. Enable the Gmail API")
        print("4. Go to Credentials -> Create Credentials -> OAuth client ID")
        print("5. Select 'Desktop app' as application type")
        print("6. Download the JSON and save as:")
        print(f"   {CREDENTIALS_FILE}")
        return

    print("✅ credentials.json found")

    if not is_gmail_api_authorized():
        print("⚠️  Not yet authorized - will open browser for authorization")
        authorize_gmail_api()
    else:
        print("✅ Gmail API authorized (token exists)")

    # Send test email
    email_address = os.environ.get("EMAIL_ADDRESS")
    if email_address:
        print()
        print(f"Sending test email to {email_address}...")
        try:
            send_email_gmail_api(
                to=email_address,
                subject="Solio AutoSolve - Gmail API Test",
                text_content="This is a test email from Solio AutoSolve using the Gmail API.",
                html_content="<h1>Gmail API Test</h1><p>This is a test email from <strong>Solio AutoSolve</strong> using the Gmail API.</p>",
            )
        except Exception as e:
            print(f"Failed to send test email: {e}")
    else:
        print()
        print("Set EMAIL_ADDRESS in .env to send a test email")


if __name__ == "__main__":
    main()
