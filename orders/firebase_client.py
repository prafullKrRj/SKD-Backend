"""Lazy firebase-admin singleton.

Reads credentials from either FIREBASE_CREDENTIALS_JSON (raw JSON string) or
GOOGLE_APPLICATION_CREDENTIALS (path). Importing this module must never crash
the app when credentials are absent in local dev — callers get a clear runtime
error only when they actually try to use Firestore.
"""
import json
import logging

from django.conf import settings

logger = logging.getLogger(__name__)

_db = None
_init_error = None


def _initialize():
    global _db, _init_error
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore

        if not firebase_admin._apps:
            if settings.FIREBASE_CREDENTIALS_JSON:
                cred = credentials.Certificate(
                    json.loads(settings.FIREBASE_CREDENTIALS_JSON)
                )
            elif settings.GOOGLE_APPLICATION_CREDENTIALS:
                cred = credentials.Certificate(
                    settings.GOOGLE_APPLICATION_CREDENTIALS
                )
            else:
                raise RuntimeError(
                    "No Firebase credentials configured "
                    "(set FIREBASE_CREDENTIALS_JSON or GOOGLE_APPLICATION_CREDENTIALS)."
                )
            firebase_admin.initialize_app(cred)

        _db = firestore.client()
        _init_error = None
    except Exception as exc:  # noqa: BLE001 - surface lazily to callers
        _init_error = exc
        logger.warning("Firebase not initialized: %s", exc)


def get_db():
    """Return a Firestore client, initializing on first use.

    Raises the original initialization error if credentials are missing/invalid.
    """
    global _db
    if _db is None:
        _initialize()
    if _db is None:
        raise RuntimeError(f"Firestore unavailable: {_init_error}")
    return _db
