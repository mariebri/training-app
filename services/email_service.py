import os
import smtplib
from email.message import EmailMessage
from typing import Optional


class EmailConfigError(ValueError):
    """Raised when mail configuration is missing or invalid."""


def _as_bool(value: Optional[str], default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _resolve_smtp_config() -> dict:
    provider = (os.getenv("MAIL_PROVIDER") or "smtp").strip().lower()

    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_use_tls = _as_bool(os.getenv("SMTP_USE_TLS"), default=True)
    smtp_use_ssl = _as_bool(os.getenv("SMTP_USE_SSL"), default=False)
    from_email = os.getenv("SMTP_FROM_EMAIL")
    from_name = os.getenv("SMTP_FROM_NAME", "Treningsplanlegger")

    if provider == "sendgrid":
        smtp_host = smtp_host or "smtp.sendgrid.net"
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_username = smtp_username or "apikey"
        smtp_password = smtp_password or os.getenv("SENDGRID_API_KEY")

    if provider == "postmark":
        smtp_host = smtp_host or "smtp.postmarkapp.com"
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        token = os.getenv("POSTMARK_SERVER_TOKEN")
        smtp_username = smtp_username or token
        smtp_password = smtp_password or token

    config = {
        "smtp_host": smtp_host,
        "smtp_port": smtp_port,
        "smtp_username": smtp_username,
        "smtp_password": smtp_password,
        "smtp_use_tls": smtp_use_tls,
        "smtp_use_ssl": smtp_use_ssl,
        "from_email": from_email,
        "from_name": from_name,
    }

    missing = [
        key
        for key in ["smtp_host", "smtp_port", "smtp_username", "smtp_password", "from_email"]
        if not config.get(key)
    ]
    if missing:
        raise EmailConfigError(
            "Mangler e-postkonfigurasjon: " + ", ".join(missing)
        )

    return config


def send_password_reset_email(to_email: str, temporary_password: str) -> None:
    config = _resolve_smtp_config()

    msg = EmailMessage()
    msg["Subject"] = "Nytt passord - Treningsplanlegger"
    msg["From"] = f"{config['from_name']} <{config['from_email']}>"
    msg["To"] = to_email
    msg.set_content(
        "Hei!\n\n"
        "Du har bedt om nytt passord i Treningsplanlegger.\n"
        f"Midlertidig passord: {temporary_password}\n\n"
        "Logg inn og bytt passord så snart som mulig.\n\n"
        "Hvis du ikke ba om nytt passord, kan du se bort fra denne e-posten.\n"
    )

    try:
        if config["smtp_use_ssl"]:
            with smtplib.SMTP_SSL(config["smtp_host"], config["smtp_port"], timeout=15) as server:
                server.login(config["smtp_username"], config["smtp_password"])
                server.send_message(msg)
        else:
            with smtplib.SMTP(config["smtp_host"], config["smtp_port"], timeout=15) as server:
                if config["smtp_use_tls"]:
                    server.starttls()
                server.login(config["smtp_username"], config["smtp_password"])
                server.send_message(msg)
    except Exception as exc:
        raise RuntimeError("Kunne ikke sende e-post. Sjekk SMTP-oppsettet.") from exc
