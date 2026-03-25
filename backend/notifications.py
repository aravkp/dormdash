import json
import os
from typing import Optional

from sqlalchemy.orm import Session

try:
    from pywebpush import WebPushException, webpush
except ImportError:  # pragma: no cover - dependency may not be installed locally yet
    WebPushException = Exception  # type: ignore
    webpush = None  # type: ignore

try:
    from . import models, schemas
except ImportError:
    import models  # type: ignore
    import schemas  # type: ignore


VAPID_PUBLIC_KEY_ENV = "VAPID_PUBLIC_KEY"
VAPID_PRIVATE_KEY_ENV = "VAPID_PRIVATE_KEY"
VAPID_SUBJECT_ENV = "VAPID_SUBJECT"


def get_vapid_public_key() -> Optional[str]:
    return os.getenv(VAPID_PUBLIC_KEY_ENV)


def vapid_is_configured() -> bool:
    return all(
        os.getenv(key)
        for key in (VAPID_PUBLIC_KEY_ENV, VAPID_PRIVATE_KEY_ENV, VAPID_SUBJECT_ENV)
    )


def upsert_subscription(
    db: Session,
    subscription: schemas.PushSubscriptionCreate,
    role: str,
) -> models.PushSubscription:
    existing = (
        db.query(models.PushSubscription)
        .filter(models.PushSubscription.endpoint == subscription.endpoint)
        .first()
    )
    if existing:
        existing.p256dh = subscription.keys.p256dh
        existing.auth = subscription.keys.auth
        existing.role = role
        db.add(existing)
        db.commit()
        db.refresh(existing)
        return existing

    db_obj = models.PushSubscription(
        endpoint=subscription.endpoint,
        p256dh=subscription.keys.p256dh,
        auth=subscription.keys.auth,
        role=role,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def remove_subscription_by_endpoint(db: Session, endpoint: str) -> None:
    existing = (
        db.query(models.PushSubscription)
        .filter(models.PushSubscription.endpoint == endpoint)
        .first()
    )
    if existing:
        db.delete(existing)
        db.commit()


def send_role_notification(
    db: Session,
    role: str,
    title: str,
    body: str,
    url: str,
) -> None:
    if not vapid_is_configured() or webpush is None:
        return

    subscriptions = (
        db.query(models.PushSubscription)
        .filter(models.PushSubscription.role == role)
        .all()
    )
    if not subscriptions:
        return

    payload = json.dumps(
        {
            "title": title,
            "body": body,
            "url": url,
        }
    )

    vapid_private_key = os.getenv(VAPID_PRIVATE_KEY_ENV)
    vapid_claims = {"sub": os.getenv(VAPID_SUBJECT_ENV)}

    stale_endpoints = []
    for sub in subscriptions:
        try:
            webpush(
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": {
                        "p256dh": sub.p256dh,
                        "auth": sub.auth,
                    },
                },
                data=payload,
                vapid_private_key=vapid_private_key,
                vapid_claims=vapid_claims,
            )
        except WebPushException as exc:  # pragma: no cover - network side effect
            status_code = getattr(getattr(exc, "response", None), "status_code", None)
            if status_code in {404, 410}:
                stale_endpoints.append(sub.endpoint)

    for endpoint in stale_endpoints:
        remove_subscription_by_endpoint(db, endpoint)


def courier_role(courier_id: str) -> str:
    return f"courier:{(courier_id or '').strip().lower()}"
