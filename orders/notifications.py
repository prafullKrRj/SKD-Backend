"""WhatsApp dispatch stubs.

In DEBUG we never make outbound calls. In production these are the seams where
a real WhatsApp Business API integration would live; for now they log the
intended message so the flow is observable end-to-end.
"""
import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def send_otp_message(phone_number, otp):
    if settings.DEBUG:
        logger.info("[DEBUG] OTP for %s is %s (no outbound dispatch)", phone_number, otp)
        return
    # Production: mock outbound WhatsApp Business API message wrapper.
    logger.info("[WhatsApp][mock] Sending OTP to %s via phone_id=%s",
                phone_number, settings.WHATSAPP_PHONE_ID)


def send_order_confirmation(phone_number, order_id):
    # Mock outbound confirmation dispatch.
    logger.info("[WhatsApp][mock] Order %s confirmed to %s", order_id, phone_number)


def notify_admin_new_order(order_id, phone_number, total):
    """Push a notification to the admin app's `new_orders` FCM topic. Best-effort."""
    from firebase_admin import messaging

    try:
        messaging.send(messaging.Message(
            notification=messaging.Notification(
                title="New order received",
                body=f"{phone_number} · ₹{total} · #{order_id[:6]}",
            ),
            data={"orderId": order_id, "type": "new_order"},
            topic="new_orders",
        ))
    except Exception:
        logger.exception("FCM push failed for order %s", order_id)
