#!/usr/bin/env python3
"""
Alternative email setup using a simple SMTP server for testing
This bypasses Gmail authentication issues for development/testing
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# For testing - you can use services like:
# - Mailtrap (free tier): https://mailtrap.io
# - MailHog (local): https://github.com/mailhog/MailHog
# - Or any SMTP service

# Example configuration for different services:

# Option 1: Mailtrap (recommended for testing)
MAILTRAP_SMTP = {
    'server': 'smtp.mailtrap.io',
    'port': 587,
    'username': 'your-mailtrap-username',  # Get from Mailtrap dashboard
    'password': 'your-mailtrap-password'   # Get from Mailtrap dashboard
}

# Option 2: Local MailHog (if you want to run locally)
MAILHOG_SMTP = {
    'server': 'localhost',
    'port': 1025,
    'username': '',  # No auth needed
    'password': ''   # No auth needed
}

# Current config (update this based on your choice)
SMTP_CONFIG = MAILTRAP_SMTP  # Change to MAILHOG_SMTP if using local

OVERRIDE_TO = os.getenv("BURSARBOT_EMAIL_OVERRIDE_TO", "")

def test_alternative_smtp():
    print("Testing alternative SMTP setup...")
    print(f"📧 To: {OVERRIDE_TO}")
    print(f"🔌 Server: {SMTP_CONFIG['server']}:{SMTP_CONFIG['port']}")

    if not OVERRIDE_TO:
        print("❌ ERROR: BURSARBOT_EMAIL_OVERRIDE_TO not set")
        return

    # Create test message
    msg = MIMEMultipart()
    msg['From'] = 'bursarbot@test.com'  # Can be anything for testing services
    msg['To'] = OVERRIDE_TO
    msg['Subject'] = "SMTP Test - Alternative Setup"

    msg.attach(MIMEText("This is a test email using alternative SMTP setup.", 'plain'))

    try:
        print("🔌 Connecting to SMTP server...")
        server = smtplib.SMTP(SMTP_CONFIG['server'], SMTP_CONFIG['port'])
        server.starttls() if SMTP_CONFIG['port'] == 587 else None  # TLS for port 587

        if SMTP_CONFIG['username'] and SMTP_CONFIG['password']:
            server.login(SMTP_CONFIG['username'], SMTP_CONFIG['password'])
            print("✅ Authentication successful!")

        text = msg.as_string()
        server.sendmail(msg['From'], OVERRIDE_TO, text)
        server.quit()

        print("✅ Test email sent successfully!")
        print(f"📬 Check {OVERRIDE_TO} for the test email")

    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    test_alternative_smtp()