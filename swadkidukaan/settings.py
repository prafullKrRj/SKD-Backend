"""
Django settings for Swad Ki Dukaan — a stateless proxy/validation API.

No persistent SQL database is used. Firestore (via firebase-admin) is the only
permanent data engine. Transient OTP state lives in an in-memory LocMemCache.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env for local development (no-op in prod where env vars are injected).
load_dotenv(BASE_DIR / ".env")


def env_bool(name, default="False"):
    return os.environ.get(name, default).strip().lower() in ("1", "true", "yes", "on")


def env_list(name, default=""):
    raw = os.environ.get(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-insecure-change-me-in-prod")
DEBUG = env_bool("DEBUG", "True")

# Open/wildcarded for local test execution; strictly bound via env in prod.
if DEBUG:
    ALLOWED_HOSTS = ["*"]
else:
    ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1")

INSTALLED_APPS = [
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "drf_spectacular",
    "orders",
]

# Note: no sessions/auth/contenttypes/admin — this API is stateless and DB-free.
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.common.CommonMiddleware",
]

# Cloudflare real-IP resolution only matters behind the proxy in production.
# In local dev there is no proxy, so skip it (nothing to throttle against).
if not DEBUG:
    MIDDLEWARE.insert(3, "orders.middleware.CloudflareRealIPMiddleware")

ROOT_URLCONF = "swadkidukaan.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": []},
    },
]

WSGI_APPLICATION = "swadkidukaan.wsgi.application"

# ---------------------------------------------------------------------------
# Database — intentionally empty. Zero persistent SQL storage.
# ---------------------------------------------------------------------------
DATABASES = {}

# ---------------------------------------------------------------------------
# Cache — in-memory OTP store with a strict TTL.
# ---------------------------------------------------------------------------
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "skd-otp-cache",
        "TIMEOUT": 300,  # 5-minute default TTL for OTP records
    }
}

# ---------------------------------------------------------------------------
# Static files (WhiteNoise)
# ---------------------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# CORS — browser client lock
# ---------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = env_list(
    "CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
)
CORS_ALLOW_HEADERS = [
    "accept",
    "authorization",
    "content-type",
    "origin",
    "user-agent",
    "x-app-signature",
    "x-client-timestamp",
]

# ---------------------------------------------------------------------------
# Client signature guard (see orders/permissions.py)
# ---------------------------------------------------------------------------
APP_SIGNATURE_SECRET = os.environ.get("APP_SIGNATURE_SECRET", "change-me-shared-secret")
REQUIRE_SIGNATURE = env_bool("REQUIRE_SIGNATURE", "False" if DEBUG else "True")
SIGNATURE_MAX_AGE = int(os.environ.get("SIGNATURE_MAX_AGE", "300"))

# ---------------------------------------------------------------------------
# Geofence
# ---------------------------------------------------------------------------
RESTAURANT_LAT = float(os.environ.get("RESTAURANT_LAT", "29.04039"))
RESTAURANT_LNG = float(os.environ.get("RESTAURANT_LNG", "77.67525"))
DELIVERY_RADIUS_KM = float(os.environ.get("DELIVERY_RADIUS_KM", "10.0"))

# ---------------------------------------------------------------------------
# Firebase
# ---------------------------------------------------------------------------
FIREBASE_CREDENTIALS_JSON = os.environ.get("FIREBASE_CREDENTIALS_JSON", "")
GOOGLE_APPLICATION_CREDENTIALS = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")

# ---------------------------------------------------------------------------
# WhatsApp (prod mock)
# ---------------------------------------------------------------------------
WHATSAPP_API_TOKEN = os.environ.get("WHATSAPP_API_TOKEN", "")
WHATSAPP_PHONE_ID = os.environ.get("WHATSAPP_PHONE_ID", "")

# ---------------------------------------------------------------------------
# DRF + throttling + schema
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": [
        "orders.permissions.HasValidClientSignature",
    ],
    # Throttling is OFF in local dev (DEBUG) so testing is never blocked.
    # In production it is GENEROUS: high enough that a confused genuine user
    # fumbling the OTP or re-requesting a code is never locked out, but low
    # enough to stop bots hammering thousands of requests.
    "DEFAULT_THROTTLE_CLASSES": (
        []
        if DEBUG
        else [
            "rest_framework.throttling.ScopedRateThrottle",
            "rest_framework.throttling.AnonRateThrottle",
        ]
    ),
    "DEFAULT_THROTTLE_RATES": {
        # Blanket per-IP ceiling across every endpoint (bot/abuse floor).
        "anon": os.environ.get("THROTTLE_ANON", "300/min"),
        # Re-send OTP: generous — a confused user can request several codes.
        "send_otp": os.environ.get("THROTTLE_SEND_OTP", "10/min"),
        # Verify OTP: generous — fat-fingering the 6 digits won't lock you out.
        "verify_otp": os.environ.get("THROTTLE_VERIFY_OTP", "20/min"),
        # Menu browsing: effectively unlimited for real users.
        "menu": os.environ.get("THROTTLE_MENU", "120/min"),
    },
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "UNAUTHENTICATED_USER": None,
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Swad Ki Dukaan API",
    "DESCRIPTION": "Stateless ordering proxy: geofenced OTP flow writing to Firestore.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}

# Security niceties behind a proxy (Railway/Cloudflare).
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
if not DEBUG:
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", "False")
