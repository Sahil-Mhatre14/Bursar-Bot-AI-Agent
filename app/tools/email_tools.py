import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from langchain_core.tools import tool
from app.tools.email_templates import build_email


EMAIL_FROM = os.getenv("BURSARBOT_EMAIL_FROM", "")
EMAIL_PASSWORD = os.getenv("BURSARBOT_EMAIL_PASSWORD", "")  # For Gmail App Password
OVERRIDE_TO = os.getenv("BURSARBOT_EMAIL_OVERRIDE_TO", "sahil.mhatre@sjsu.edu")


def _require_env():
    if not EMAIL_FROM:
        raise RuntimeError("Missing BURSARBOT_EMAIL_FROM in environment.")
    if not EMAIL_PASSWORD:
        raise RuntimeError("Missing BURSARBOT_EMAIL_PASSWORD in environment (use Gmail App Password for Gmail).")


@tool
def send_email(to: str, subject: str, body: str) -> str:
    """
    Send an email via native Python SMTP.
    Demo safety: ALWAYS overrides recipient to BURSARBOT_EMAIL_OVERRIDE_TO (default: sahil.mhatre@sjsu.edu).

    Returns a short status string.
    """
    _require_env()

    actual_to = OVERRIDE_TO.strip()

    # Create message
    msg = MIMEMultipart()
    msg['From'] = EMAIL_FROM
    msg['To'] = actual_to
    msg['Subject'] = subject

    # Add body
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Connect to Gmail SMTP server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()  # Enable TLS

        # Remove spaces from App Password if present and ensure it's exactly 16 chars
        clean_password = EMAIL_PASSWORD.replace(" ", "").strip()
        if len(clean_password) != 16:
            return f"smtp_status=error, error=App Password must be exactly 16 characters (got {len(clean_password)}), to={actual_to}"

        server.login(EMAIL_FROM, clean_password)
        text = msg.as_string()
        server.sendmail(EMAIL_FROM, actual_to, text)
        server.quit()
        return f"smtp_status=success, to={actual_to}"
    except smtplib.SMTPAuthenticationError as e:
        return f"smtp_status=auth_error, error=Gmail authentication failed - check App Password setup at https://myaccount.google.com/apppasswords, to={actual_to}"
    except smtplib.SMTPConnectError as e:
        return f"smtp_status=connect_error, error=Failed to connect to Gmail SMTP server, to={actual_to}"
    except Exception as e:
        return f"smtp_status=error, error={str(e)}, to={actual_to}"


@tool
def send_outreach_email(
    bucket: str,
    student_name: str,
    student_id: str,
    email: str,
    balance: str,
    address: str = "",
    city: str = "",
    state: str = "",
    postal: str = "",
) -> str:
    """
    Send an official SJSU Bursar collection notice email using the correct
    template for the student's aging bucket.

    Args:
        bucket:       Aging bucket — one of "61-90", "91-120", "121-150".
        student_name: Full name of the student (first + last).
        student_id:   Student EMPLID.
        email:        Student's email address.
        balance:      Outstanding balance as a string, e.g. "321.84".
        address:      Street address (optional).
        city:         City (optional).
        state:        State abbreviation (optional).
        postal:       Postal/ZIP code (optional).

    Returns:
        Status string indicating success or failure.
    """
    try:
        subject, body = build_email(
            bucket=bucket,
            student_name=student_name,
            student_id=student_id,
            address=address or "—",
            city=city or "—",
            state=state or "—",
            postal=postal or "—",
            balance=balance,
        )
    except ValueError as e:
        return f"template_error={str(e)}"

    return send_email.invoke({"to": email, "subject": subject, "body": body})