"""Custom client-signature guard.

Even if CORS is satisfied, a raw script/Postman request should not be able to
hit the ordering endpoints. The frontend web bundle computes an HMAC-SHA256
signature over a fresh unix timestamp using a shared secret and sends it as
``X-App-Signature`` alongside ``X-Client-Timestamp``. We recompute and compare
in constant time, and reject stale timestamps to blunt replay.

In DEBUG this can be bypassed (settings.REQUIRE_SIGNATURE=False) so Swagger and
local tooling stay usable.
"""
import hashlib
import hmac
import time

from django.conf import settings
from rest_framework.permissions import BasePermission


class HasValidClientSignature(BasePermission):
    message = "Invalid or missing client signature."

    def has_permission(self, request, view):
        if not getattr(settings, "REQUIRE_SIGNATURE", True):
            return True

        signature = request.headers.get("X-App-Signature", "")
        timestamp = request.headers.get("X-Client-Timestamp", "")
        if not signature or not timestamp:
            return False

        # Anti-replay: reject timestamps outside the freshness window.
        try:
            ts = int(timestamp)
        except (TypeError, ValueError):
            return False
        if abs(time.time() - ts) > settings.SIGNATURE_MAX_AGE:
            return False

        expected = hmac.new(
            settings.APP_SIGNATURE_SECRET.encode("utf-8"),
            timestamp.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(expected, signature)
