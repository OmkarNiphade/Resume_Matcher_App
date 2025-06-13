from email_utils import send_email

if send_email("your_email@gmail.com", "Test Subject", "Test Body"):
    print("✅ Email sent successfully!")
else:
    print("❌ Failed to send email.")
