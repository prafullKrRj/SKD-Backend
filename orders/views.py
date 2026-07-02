"""Order flow endpoints: geofenced OTP dispatch + verification -> Firestore."""
import hmac
import logging
import secrets

from django.conf import settings
from django.core.cache import cache
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .geofence import within_delivery_radius
from .notifications import notify_admin_new_order, send_order_confirmation, send_otp_message
from .serializers import SendOtpSerializer, VerifyOtpSerializer

logger = logging.getLogger(__name__)

OTP_TTL_SECONDS = 300


def _generate_otp():
    # DEBUG: deterministic token so the flow is testable without dispatch.
    if settings.DEBUG:
        return "111111"
    return f"{secrets.randbelow(1_000_000):06d}"


class MenuView(APIView):
    """Public menu read, streamed live from Firestore `menu` collection."""

    permission_classes = [AllowAny]  # public read; no client signature required
    throttle_scope = "menu"

    @extend_schema(
        responses={200: OpenApiResponse(description="List of available dishes.")}
    )
    def get(self, request):
        try:
            from .firebase_client import get_db

            db = get_db()
            docs = db.collection("menu").where("available", "==", True).stream()
            items = []
            for doc in docs:
                data = doc.to_dict()
                data["id"] = doc.id
                items.append(data)
            items.sort(key=lambda d: (d.get("category", ""), d.get("name", "")))
            return Response({"items": items}, status=status.HTTP_200_OK)
        except Exception:  # noqa: BLE001
            logger.exception("menu fetch failed")
            return Response(
                {"error": "Menu temporarily unavailable."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )


class SendOtpView(APIView):
    throttle_scope = "send_otp"

    @extend_schema(
        request=SendOtpSerializer,
        responses={
            200: OpenApiResponse(description="OTP dispatched cleanly."),
            400: OpenApiResponse(description="Validation or geofence failure."),
            429: OpenApiResponse(description="Rate limit exceeded (3/min)."),
        },
        examples=[
            OpenApiExample(
                "In-radius order",
                value={
                    "phone_number": "+919876543210",
                    "cart_items": [{"name": "Chole Bhature", "price": 120, "qty": 2}],
                    "delivery_address": "12 MG Road, New Delhi",
                    "latitude": 28.6145,
                    "longitude": 77.2100,
                },
                request_only=True,
            )
        ],
    )
    def post(self, request):
        try:
            serializer = SendOtpSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            data = serializer.validated_data

            # 1. Geofence short-circuit.
            if not within_delivery_radius(data["latitude"], data["longitude"]):
                return Response(
                    {
                        "error": "Geofence Restriction: Your location is "
                        "outside our local delivery radius."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # 2. Generate + dispatch OTP.
            otp = _generate_otp()
            send_otp_message(data["phone_number"], otp)

            # 3. Stash the whole pending order under the phone number, TTL 5 min.
            cache.set(
                data["phone_number"],
                {
                    "token": otp,
                    "cart_items": data["cart_items"],
                    "delivery_address": data["delivery_address"],
                    "latitude": data["latitude"],
                    "longitude": data["longitude"],
                    "location_confirmed": data["location_confirmed"],
                },
                timeout=OTP_TTL_SECONDS,
            )

            return Response(
                {"message": "OTP dispatched cleanly"}, status=status.HTTP_200_OK
            )
        except Exception:  # noqa: BLE001 - never leak stack traces to clients
            logger.exception("send-otp failed")
            return Response(
                {"error": "Internal error dispatching OTP."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class VerifyOtpView(APIView):
    throttle_scope = "verify_otp"

    @extend_schema(
        request=VerifyOtpSerializer,
        responses={
            201: OpenApiResponse(description="Order successfully locked and verified."),
            400: OpenApiResponse(description="Expired/absent OTP or mismatch."),
            429: OpenApiResponse(description="Rate limit exceeded (5/min)."),
        },
    )
    def post(self, request):
        try:
            serializer = VerifyOtpSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            phone_number = serializer.validated_data["phone_number"]
            otp_entered = serializer.validated_data["otp_entered"]

            # 1. Pull the pending order; absent => expired or never sent.
            pending = cache.get(phone_number)
            if not pending:
                return Response(
                    {"error": "OTP expired or not found. Please request a new one."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # 2. Constant-time compare.
            if not hmac.compare_digest(str(pending["token"]), str(otp_entered)):
                return Response(
                    {"error": "Incorrect OTP."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # 3. Persist to Firestore FIRST — this is the source of truth.
            #    If it raises, we fall to the except block: no confirmation is
            #    sent and the cache is left intact so the user can retry.
            order_id = self._write_order(phone_number, pending)

            # 4. Order is durably saved. Clear the OTP so it can't be reused.
            cache.delete(phone_number)

            # 5. Confirmation is best-effort: the order already exists, so a
            #    WhatsApp hiccup must NOT fail the request or trigger a retry.
            try:
                send_order_confirmation(phone_number, order_id)
            except Exception:  # noqa: BLE001
                logger.exception("order %s saved but confirmation dispatch failed", order_id)

            # 6. Alert the admin app. Also best-effort — never fails the request.
            total = sum(i["price"] * i["qty"] for i in pending["cart_items"])
            notify_admin_new_order(order_id, phone_number, total)

            return Response(
                {
                    "status": "Order successfully locked and verified.",
                    "order_id": order_id,
                },
                status=status.HTTP_201_CREATED,
            )
        except Exception:  # noqa: BLE001
            logger.exception("verify-otp failed")
            return Response(
                {"error": "Internal error verifying order."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @staticmethod
    def _write_order(phone_number, pending):
        from firebase_admin import firestore

        from .firebase_client import get_db

        db = get_db()
        doc = {
            "status": "pending",  # pending -> out_for_delivery -> completed
            "phone_number": phone_number,
            "delivery_address": pending["delivery_address"],
            "coordinates": firestore.GeoPoint(
                pending["latitude"], pending["longitude"]
            ),
            "items": pending["cart_items"],
            "location_confirmed": pending.get("location_confirmed", False),
            "timestamp": firestore.SERVER_TIMESTAMP,
        }
        _, ref = db.collection("orders").add(doc)
        return ref.id
