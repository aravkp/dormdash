import json
import os
from typing import Optional

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
FIREBASE_APP = None

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


def get_firebase_app():
    global FIREBASE_APP

    if FIREBASE_APP is not None:
        return FIREBASE_APP
    if firebase_admin is None or credentials is None:
        return None
    if not firebase_is_configured():
        return None

    if firebase_admin._apps:  # type: ignore[attr-defined]
        FIREBASE_APP = firebase_admin.get_app()
        return FIREBASE_APP

    service_account = json.loads(os.getenv(FIREBASE_SERVICE_ACCOUNT_JSON_ENV, "{}"))
    FIREBASE_APP = firebase_admin.initialize_app(
        credentials.Certificate(service_account)
    )
    return FIREBASE_APP


def upsert_notification_token(
    db: Session,
    payload: schemas.NotificationTokenCreate,
    role: str,
    courier_id: Optional[str] = None,
) -> models.NotificationDeviceToken:
    token_value = (payload.token or "").strip()
    normalized_courier_id = (courier_id or "").strip().lower() or None
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
        return existing

    db_obj = models.NotificationDeviceToken(
        token=token_value,
        role=role,
        courier_id=normalized_courier_id,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def remove_notification_token(db: Session, token: str) -> None:
    existing = (
        db.query(models.NotificationDeviceToken)
        .filter(models.NotificationDeviceToken.token == token)
        .first()
    )
    if existing:
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
    app = get_firebase_app()
    if app is None or messaging is None:
        return

    query = (
        db.query(models.NotificationDeviceToken)
        .filter(models.NotificationDeviceToken.role == role)
    )
    normalized_courier_id = (courier_id or "").strip().lower()
    if role == "courier" and normalized_courier_id:
        query = query.filter(models.NotificationDeviceToken.courier_id == normalized_courier_id)

    tokens = [row.token for row in query.all() if row.token]
    if not tokens:
        return

    stale_tokens = []
    for token in tokens:
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            token=token,
            webpush=messaging.WebpushConfig(
                fcm_options=messaging.WebpushFCMOptions(link=url)
            ),
        )
        try:
            messaging.send(message, app=app)
        except Exception as exc:  # pragma: no cover
            error_text = str(exc).lower()
            if "registration-token-not-registered" in error_text or "unregistered" in error_text:
                stale_tokens.append(token)

    for token in stale_tokens:
        remove_notification_token(db, token)
