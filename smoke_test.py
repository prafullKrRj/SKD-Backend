"""Full end-to-end smoke test (requires real Admin service-account creds).

Run:  .venv/bin/python smoke_test.py
Exercises: Firestore menu read, send-otp (geofence + cache), verify-otp
(Firestore order write + cache wipe). Cleans up the test order it creates.
"""
import json
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "swadkidukaan.settings")
django.setup()

from django.core.cache import cache  # noqa: E402
from django.test import Client  # noqa: E402

from orders.firebase_client import get_db  # noqa: E402

c = Client()
PHONE = "+919876543210"


def post(path, payload):
    r = c.post(path, data=json.dumps(payload), content_type="application/json")
    return r.status_code, r.json()


def main():
    db = get_db()
    ok = True

    # 1. Menu read from Firestore
    r = c.get("/api/orders/menu/")
    print(f"[menu]   {r.status_code}  items={len(r.json().get('items', []))}")
    ok &= r.status_code == 200 and len(r.json().get("items", [])) > 0

    # 2. Geofence reject (Mumbai coords vs Delhi restaurant)
    code, body = post("/api/orders/send-otp/", {
        "phone_number": PHONE,
        "cart_items": [{"name": "Samosa", "price": 40, "qty": 1}],
        "delivery_address": "far away", "latitude": 19.076, "longitude": 72.877,
    })
    print(f"[geo]    {code}  {body.get('error', '')[:40]}")
    ok &= code == 400

    # 3. send-otp in radius
    code, body = post("/api/orders/send-otp/", {
        "phone_number": PHONE,
        "cart_items": [{"name": "Chole Bhature", "price": 180, "qty": 2}],
        "delivery_address": "Main Bazaar, Kiratpur",
        "latitude": 29.0404, "longitude": 77.6752,
        "location_confirmed": True,
    })
    print(f"[send]   {code}  {body}")
    ok &= code == 200
    cached = cache.get(PHONE)
    print(f"[cache]  token={cached and cached['token']}")

    # 4. verify wrong
    code, body = post("/api/orders/verify-otp/", {"phone_number": PHONE, "otp_entered": "000000"})
    print(f"[wrong]  {code}  {body.get('error')}")
    ok &= code == 400

    # 5. verify correct -> Firestore write
    code, body = post("/api/orders/verify-otp/", {"phone_number": PHONE, "otp_entered": "111111"})
    print(f"[verify] {code}  {body}")
    ok &= code == 201
    ok &= cache.get(PHONE) is None  # cache wiped

    # 6. confirm order landed in Firestore, then clean up
    orders = list(db.collection("orders").where("phone_number", "==", PHONE).stream())
    print(f"[order]  {len(orders)} order doc(s) for {PHONE}")
    ok &= len(orders) >= 1
    for o in orders:
        d = o.to_dict()
        print(f"         id={o.id} status={d.get('status')} items={len(d.get('items', []))} loc_confirmed={d.get('location_confirmed')}")
        ok &= d.get("location_confirmed") is True
        o.reference.delete()  # cleanup test order
    print("[clean]  test orders removed")

    print("\n" + ("ALL GREEN ✅" if ok else "FAILURES ❌"))


if __name__ == "__main__":
    main()
