import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# ✅ Define these AFTER loading dotenv
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

def send_email(to, subject, body):
    msg = EmailMessage()
    msg["From"] = EMAIL_USER
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_USER, EMAIL_PASS)
            smtp.send_message(msg)
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False
