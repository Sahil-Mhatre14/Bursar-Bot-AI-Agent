#!/usr/bin/env python3
"""
Test script to verify Gmail SMTP configuration
Run this to debug email authentication issues
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

EMAIL_FROM = os.getenv("BURSARBOT_EMAIL_FROM", "")
EMAIL_PASSWORD = os.getenv("BURSARBOT_EMAIL_PASSWORD", "")
OVERRIDE_TO = os.getenv("BURSARBOT_EMAIL_OVERRIDE_TO", "")

def test_smtp_connection():
    print("Testing Gmail SMTP connection...")

    if not EMAIL_FROM:
        print("❌ ERROR: BURSARBOT_EMAIL_FROM not set")
        return

    if not EMAIL_PASSWORD:
        print("❌ ERROR: BURSARBOT_EMAIL_PASSWORD not set")
        return

    if not OVERRIDE_TO:
        print("❌ ERROR: BURSARBOT_EMAIL_OVERRIDE_TO not set")
        return

    print(f"📧 From: {EMAIL_FROM}")
    print(f"📧 To: {OVERRIDE_TO}")
    print(f"🔑 Password length: {len(EMAIL_PASSWORD)} characters")

    # Create test message
    msg = MIMEMultipart()
    msg['From'] = EMAIL_FROM
    msg['To'] = OVERRIDE_TO
    msg['Subject'] = "SMTP Test - Bursar Bot"

    msg.attach(MIMEText("This is a test email from Bursar Bot SMTP configuration.", 'plain'))

    try:
        print("🔌 Connecting to Gmail SMTP server...")
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()

        # Clean password (remove spaces)
        clean_password = EMAIL_PASSWORD.replace(" ", "")
        print(f"🔐 Attempting login with cleaned password (length: {len(clean_password)})...")

        server.login(EMAIL_FROM, clean_password)
        print("✅ Authentication successful!")

        text = msg.as_string()
        server.sendmail(EMAIL_FROM, OVERRIDE_TO, text)
        server.quit()

        print("✅ Test email sent successfully!")
        print(f"📬 Check {OVERRIDE_TO} for the test email")

    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ AUTHENTICATION ERROR: {e}")
        print("\n🔧 TROUBLESHOOTING STEPS:")
        print("1. Make sure 2-Factor Authentication is ENABLED on your Gmail account")
        print("2. Generate a NEW App Password:")
        print("   - Go to https://myaccount.google.com/security")
        print("   - Click '2-Step Verification' → 'App passwords'")
        print("   - Select 'Mail' and 'Other (custom name)'")
        print("   - Copy the 16-character password (ignore spaces)")
        print("3. Update BURSARBOT_EMAIL_PASSWORD in .env with the new password")
        print("4. Make sure you're using your Gmail email address, not an alias")

    except smtplib.SMTPConnectError as e:
        print(f"❌ CONNECTION ERROR: {e}")
        print("Check your internet connection and Gmail SMTP server status")

    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")

if __name__ == "__main__":
    test_smtp_connection()