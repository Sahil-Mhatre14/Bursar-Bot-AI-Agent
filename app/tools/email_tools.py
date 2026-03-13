import os
from typing import Optional

from langchain_core.tools import tool
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
EMAIL_FROM = os.getenv("BURSARBOT_EMAIL_FROM", "")
OVERRIDE_TO = os.getenv("BURSARBOT_EMAIL_OVERRIDE_TO", "sahil.mhatre@sjsu.edu")


def _require_env():
    if not SENDGRID_API_KEY:
        raise RuntimeError("Missing SENDGRID_API_KEY in environment.")
    if not EMAIL_FROM:
        raise RuntimeError("Missing BURSARBOT_EMAIL_FROM in environment (must be verified in SendGrid).")


@tool
def send_email(to: str, subject: str, body: str) -> str:
    """
    Send an email via SendGrid.
    Demo safety: ALWAYS overrides recipient to BURSARBOT_EMAIL_OVERRIDE_TO (default: sahil.mhatre@sjsu.edu).

    Returns a short status string with HTTP code.
    """
    _require_env()

    actual_to = OVERRIDE_TO.strip()

    message = Mail(
        from_email=EMAIL_FROM,
        to_emails=actual_to,
        subject=subject,
        plain_text_content=body,
    )

    sg = SendGridAPIClient(SENDGRID_API_KEY)
    resp = sg.send(message)
    return f"sendgrid_status={resp.status_code}, to={actual_to}"