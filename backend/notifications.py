import json
import logging
import os
from typing import Optional
from urllib import error, request

from sqlalchemy.orm import Session

try:
    import firebase_admin
    from firebase_admin import credentials, messaging
except ImportError:  # pragma: no cover
    firebase_admin = None  # type: ignore
    credentials = None  # type: ignore
    messaging = None  # type: ignore

try:
    from . import models, schemas
except ImportError:
    import models  # type: ignore
    import schemas  # type: ignore


FIREBASE_SERVICE_ACCOUNT_JSON_ENV = "FIREBASE_SERVICE_ACCOUNT_JSON"
FIREBASE_WEB_PUSH_CERTIFICATE_KEY_ENV = "FIREBASE_WEB_PUSH_CERTIFICATE_KEY"
RESEND_API_KEY_ENV = "RESEND_API_KEY"
FROM_EMAIL_ENV = "FROM_EMAIL"
ADMIN_NOTIFY_EMAIL_ENV = "ADMIN_NOTIFY_EMAIL"
COURIER_NOTIFY_EMAIL_ENV = "COURIER_NOTIFY_EMAIL"
COURIER_NOTIFY_EMAILS_ENV = "COURIER_NOTIFY_EMAILS_JSON"
FIREBASE_APP = None
logger = logging.getLogger("dormdash.notifications")

FIREBASE_CONFIG = {
    "apiKey": "AIzaSyCmHbirJJE7d8_wvMhvEUDknBfSdTqwPK0",
    "authDomain": "dormdash-38623.firebaseapp.com",
    "projectId": "dormdash-38623",
    "storageBucket": "dormdash-38623.firebasestorage.app",
    "messagingSenderId": "927323489495",
    "appId": "1:927323489495:web:0f9a2163ab45b25f509c92",
}


def get_firebase_config() -> dict:
    return FIREBASE_CONFIG


def get_firebase_web_push_key() -> Optional[str]:
    return os.getenv(FIREBASE_WEB_PUSH_CERTIFICATE_KEY_ENV)


def firebase_is_configured() -> bool:
    return bool(os.getenv(FIREBASE_SERVICE_ACCOUNT_JSON_ENV)) and bool(
        os.getenv(FIREBASE_WEB_PUSH_CERTIFICATE_KEY_ENV)
    )


def email_is_configured() -> bool:
    return bool(os.getenv(RESEND_API_KEY_ENV)) and bool(os.getenv(FROM_EMAIL_ENV))


def get_admin_notification_email() -> Optional[str]:
    return (os.getenv(ADMIN_NOTIFY_EMAIL_ENV) or "").strip() or None


def get_courier_notification_email(courier_id: Optional[str]) -> Optional[str]:
    normalized_courier_id = (courier_id or "").strip().lower()
    mapping_raw = os.getenv(COURIER_NOTIFY_EMAILS_ENV, "").strip()
    if mapping_raw:
        try:
            mapping = json.loads(mapping_raw)
            if isinstance(mapping, dict):
                match = mapping.get(normalized_courier_id)
                if isinstance(match, str) and match.strip():
                    return match.strip()
        except Exception:
            logger.exception("Failed to parse courier email mapping JSON")
    fallback = (os.getenv(COURIER_NOTIFY_EMAIL_ENV) or "").strip()
    return fallback or None


def send_email(recipient: str, subject: str, text: str) -> None:
    if not email_is_configured():
        logger.info("Skipping email send because Resend is not configured")
        return

    api_key = os.getenv(RESEND_API_KEY_ENV, "").strip()
    from_email = os.getenv(FROM_EMAIL_ENV, "").strip()
    payload = json.dumps(
        {
            "from": from_email,
            "to": [recipient],
            "subject": subject,
            "text": text,
        }
    ).encode("utf-8")
    req = request.Request(
        "https://api.resend.com/emails",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "dormdash/1.0",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=20) as response:
            body = response.read().decode("utf-8", errors="replace")
            logger.info(
                "Email send succeeded recipient=%s status=%s response=%s",
                recipient,
                getattr(response, "status", "unknown"),
                body,
            )
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        logger.error(
            "Email send failed recipient=%s status=%s response=%s",
            recipient,
            exc.code,
            body,
        )
    except Exception:
        logger.exception("Email send failed recipient=%s", recipient)


def send_admin_email(subject: str, text: str) -> None:
    recipient = get_admin_notification_email()
    if not recipient:
        logger.info("Skipping admin email because ADMIN_NOTIFY_EMAIL is not set")
        return
    send_email(recipient, subject, text)


def send_courier_email(courier_id: Optional[str], subject: str, text: str) -> None:
    recipient = get_courier_notification_email(courier_id)
    if not recipient:
        logger.info(
            "Skipping courier email because no recipient is configured for courier_id=%s",
            (courier_id or "").strip().lower() or None,
        )
        return
    send_email(recipient, subject, text)


def get_firebase_app():
    global FIREBASE_APP

    if FIREBASE_APP is not None:
        return FIREBASE_APP
    if firebase_admin is None or credentials is None:
        logger.warning("Firebase admin SDK is not installed; notifications disabled")
        return None
    if not firebase_is_configured():
        logger.warning("Firebase env vars are missing; notifications disabled")
        return None

    if firebase_admin._apps:  # type: ignore[attr-defined]
        FIREBASE_APP = firebase_admin.get_app()
        logger.info("Reusing existing Firebase app")
        return FIREBASE_APP

    try:
        service_account = json.loads(os.getenv(FIREBASE_SERVICE_ACCOUNT_JSON_ENV, "{}"))
        FIREBASE_APP = firebase_admin.initialize_app(
            credentials.Certificate(service_account)
        )
        logger.info(
            "Initialized Firebase app for project_id=%s",
            service_account.get("project_id", "unknown"),
        )
        return FIREBASE_APP
    except Exception:
        logger.exception("Failed to initialize Firebase app")
        return None


def upsert_notification_token(
    db: Session,
    payload: schemas.NotificationTokenCreate,
    role: str,
    courier_id: Optional[str] = None,
) -> models.NotificationDeviceToken:
    token_value = (payload.token or "").strip()
    normalized_courier_id = (courier_id or "").strip().lower() or None
    logger.info(
        "Registering notification token role=%s courier_id=%s token_suffix=%s",
        role,
        normalized_courier_id,
        token_value[-12:] if token_value else "missing",
    )
    existing = (
        db.query(models.NotificationDeviceToken)
        .filter(models.NotificationDeviceToken.token == token_value)
        .first()
    )
    if existing:
        existing.role = role
        existing.courier_id = normalized_courier_id
        db.add(existing)
        db.commit()
        db.refresh(existing)
        logger.info("Updated existing notification token id=%s", existing.id)
        return existing

    db_obj = models.NotificationDeviceToken(
        token=token_value,
        role=role,
        courier_id=normalized_courier_id,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    logger.info("Created notification token id=%s", db_obj.id)
    return db_obj


def remove_notification_token(db: Session, token: str) -> None:
    existing = (
        db.query(models.NotificationDeviceToken)
        .filter(models.NotificationDeviceToken.token == token)
        .first()
    )
    if existing:
        logger.info(
            "Removing stale notification token id=%s token_suffix=%s",
            existing.id,
            (token or "")[-12:],
        )
        db.delete(existing)
        db.commit()


def send_notification(
    db: Session,
    role: str,
    title: str,
    body: str,
    url: str,
    courier_id: Optional[str] = None,
) -> None:
    logger.info(
        "Preparing notification role=%s courier_id=%s title=%s url=%s",
        role,
        (courier_id or "").strip().lower() or None,
        title,
        url,
    )
    app = get_firebase_app()
    if app is None or messaging is None:
        logger.warning("Skipping notification send because Firebase is unavailable")
        return

    query = (
        db.query(models.NotificationDeviceToken)
        .filter(models.NotificationDeviceToken.role == role)
    )
    normalized_courier_id = (courier_id or "").strip().lower()
    if role == "courier" and normalized_courier_id:
        query = query.filter(models.NotificationDeviceToken.courier_id == normalized_courier_id)

    tokens = [row.token for row in query.all() if row.token]
    logger.info(
        "Found %s notification token(s) for role=%s courier_id=%s",
        len(tokens),
        role,
        normalized_courier_id or None,
    )
    if not tokens:
        return

    stale_tokens = []
    for token in tokens:
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            token=token,
            webpush=messaging.WebpushConfig(
                headers={"Urgency": "high"},
                notification=messaging.WebpushNotification(
                    title=title,
                    body=body,
                    icon="/icon-512.png",
                    badge="/icon-512.png",
                ),
                fcm_options=messaging.WebpushFCMOptions(link=url),
            ),
        )
        try:
            message_id = messaging.send(message, app=app)
            logger.info(
                "Notification send succeeded role=%s token_suffix=%s message_id=%s",
                role,
                token[-12:],
                message_id,
            )
        except Exception as exc:  # pragma: no cover
            logger.exception(
                "Notification send failed role=%s token_suffix=%s error=%s",
                role,
                token[-12:],
                str(exc),
            )
            error_text = str(exc).lower()
            if "registration-token-not-registered" in error_text or "unregistered" in error_text:
                stale_tokens.append(token)

    for token in stale_tokens:
        remove_notification_token(db, token)
