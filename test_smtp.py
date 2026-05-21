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

SENDER_EMAIL = os.getenv("SENDER_EMAIL", "")
EMAIL_PASSWORD = os.getenv("BURSARBOT_EMAIL_PASSWORD", "")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL", "")

def test_smtp_connection():
    print("Testing Gmail SMTP connection...")

    if not SENDER_EMAIL:
        print("❌ ERROR: SENDER_EMAIL not set")
        return

    if not EMAIL_PASSWORD:
        print("❌ ERROR: BURSARBOT_EMAIL_PASSWORD not set")
        return

    if not RECEIVER_EMAIL:
        print("❌ ERROR: RECEIVER_EMAIL not set")
        return

    print(f"📧 From: {SENDER_EMAIL}")
    print(f"📧 To: {RECEIVER_EMAIL}")
    print(f"🔑 Password length: {len(EMAIL_PASSWORD)} characters")

    # Create test message
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    msg['Subject'] = "SMTP Test - Bursar Bot"

    msg.attach(MIMEText("This is a test email from Bursar Bot SMTP configuration.", 'plain'))

    try:
        print("🔌 Connecting to Gmail SMTP server...")
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()

        # Clean password (remove spaces)
        clean_password = EMAIL_PASSWORD.replace(" ", "")
        print(f"🔐 Attempting login with cleaned password (length: {len(clean_password)})...")

        server.login(SENDER_EMAIL, clean_password)
        print("✅ Authentication successful!")

        text = msg.as_string()
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, text)
        server.quit()

        print("✅ Test email sent successfully!")
        print(f"📬 Check {RECEIVER_EMAIL} for the test email")

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