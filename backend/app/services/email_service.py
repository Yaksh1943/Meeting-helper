import smtplib
from email.mime.text import MIMEText
from app.utils.config import get_env


def send_email(to_email: str, subject: str, body: str):
    from_email = get_env("SMTP_USER")
    password = get_env("SMTP_PASS")
    smtp_host = get_env("SMTP_HOST", "smtp.gmail.com")
    smtp_port_raw = get_env("SMTP_PORT", "465")

    if not from_email or not password:
        print(f"Email skipped (no SMTP credentials configured): {subject} -> {to_email}")
        return False

    try:
        smtp_port = int(smtp_port_raw) if smtp_port_raw else 465
    except ValueError:
        smtp_port = 465

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email

    try:
        with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
            server.login(from_email, password)
            server.sendmail(from_email, [to_email], msg.as_string())
        return True
    except Exception as e:
        print(f"Email failed to {to_email}: {e}")
        return False