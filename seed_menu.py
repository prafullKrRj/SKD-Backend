"""Seed the Firestore `menu` collection with sample dishes.

Run:  .venv/bin/python seed_menu.py
Uses the same firebase-admin credentials as the app (serviceAccount.json).
Idempotent: each dish is written under a deterministic doc id (its slug).
"""
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "swadkidukaan.settings")
django.setup()

from orders.firebase_client import get_db  # noqa: E402

MENU = [
    # ---- Momo ----
    {"id": "steam-momo-half", "name": "Steam Momo (Half · 5pc)", "price": 50, "category": "Momo",
     "description": "Soft steamed dumplings with spiced veg filling, served with chutney."},
    {"id": "steam-momo-full", "name": "Steam Momo (Full · 10pc)", "price": 80, "category": "Momo",
     "description": "Soft steamed dumplings with spiced veg filling, served with chutney."},
    {"id": "fried-momo-half", "name": "Fried Momo (Half · 5pc)", "price": 60, "category": "Momo",
     "description": "Golden fried dumplings, crisp outside, juicy veg filling inside."},
    {"id": "fried-momo-full", "name": "Fried Momo (Full · 10pc)", "price": 99, "category": "Momo",
     "description": "Golden fried dumplings, crisp outside, juicy veg filling inside."},
    {"id": "kurkure-momo-half", "name": "Kurkure Momo (Half · 5pc)", "price": 80, "category": "Momo",
     "description": "Crunchy crumb-coated momos, deep fried till crispy."},
    {"id": "kurkure-momo-full", "name": "Kurkure Momo (Full · 10pc)", "price": 140, "category": "Momo",
     "description": "Crunchy crumb-coated momos, deep fried till crispy."},

    # ---- Noodles ----
    {"id": "veg-noodles-half", "name": "Veg Noodles (Half)", "price": 50, "category": "Noodles",
     "description": "Wok-tossed noodles with fresh vegetables and soy."},
    {"id": "veg-noodles-full", "name": "Veg Noodles (Full)", "price": 80, "category": "Noodles",
     "description": "Wok-tossed noodles with fresh vegetables and soy."},
    {"id": "paneer-noodles-half", "name": "Paneer Noodles (Half)", "price": 60, "category": "Noodles",
     "description": "Stir-fried noodles loaded with paneer cubes and veggies."},
    {"id": "paneer-noodles-full", "name": "Paneer Noodles (Full)", "price": 99, "category": "Noodles",
     "description": "Stir-fried noodles loaded with paneer cubes and veggies."},
    {"id": "haka-noodles-half", "name": "Haka Noodles (Half)", "price": 60, "category": "Noodles",
     "description": "Indo-Chinese style noodles, spicy and tangy."},
    {"id": "haka-noodles-full", "name": "Haka Noodles (Full)", "price": 99, "category": "Noodles",
     "description": "Indo-Chinese style noodles, spicy and tangy."},

    # ---- Burger ----
    {"id": "veg-burger", "name": "Veg Burger", "price": 50, "category": "Burger",
     "description": "Crispy veg patty burger with fresh salad and sauces."},
    {"id": "veg-cheese-burger", "name": "Veg Cheese Burger", "price": 70, "category": "Burger",
     "description": "Veg patty burger loaded with melted cheese."},
    {"id": "paneer-burger", "name": "Paneer Burger", "price": 90, "category": "Burger",
     "description": "Grilled paneer patty burger with tangy sauces."},
    {"id": "kurkure-burger", "name": "Kurkure Burger", "price": 120, "category": "Burger",
     "description": "Extra crunchy kurkure patty burger, loaded and cheesy."},

    # ---- Chilli Potato ----
    {"id": "chilli-potato-half", "name": "Chilli Potato (Half)", "price": 50, "category": "Chilli Potato",
     "description": "Crispy potato fingers tossed in spicy chilli sauce."},
    {"id": "chilli-potato-full", "name": "Chilli Potato (Full)", "price": 80, "category": "Chilli Potato",
     "description": "Crispy potato fingers tossed in spicy chilli sauce."},
    {"id": "honey-chilli-potato-half", "name": "Honey Chilli Potato (Half)", "price": 60, "category": "Chilli Potato",
     "description": "Crispy potato tossed in sweet-spicy honey chilli glaze."},
    {"id": "honey-chilli-potato-full", "name": "Honey Chilli Potato (Full)", "price": 109, "category": "Chilli Potato",
     "description": "Crispy potato tossed in sweet-spicy honey chilli glaze."},
    {"id": "chilli-paneer-half", "name": "Chilli Paneer (Half)", "price": 100, "category": "Chilli Potato",
     "description": "Paneer cubes tossed in spicy Indo-Chinese chilli sauce."},
    {"id": "chilli-paneer-full", "name": "Chilli Paneer (Full)", "price": 180, "category": "Chilli Potato",
     "description": "Paneer cubes tossed in spicy Indo-Chinese chilli sauce."},

    # ---- Other Items ----
    {"id": "veg-spring-roll", "name": "Veg Spring Roll", "price": 40, "category": "Other Items",
     "description": "Crispy fried rolls stuffed with spiced vegetables."},
    {"id": "paneer-buterfully", "name": "Paneer Buterfully", "price": 80, "category": "Other Items",
     "description": "Crispy butterfly-cut paneer fritters, lightly spiced."},
    {"id": "muesli-icy-bite", "name": "Muesli ICY Bite", "price": 160, "category": "Other Items",
     "description": "Chilled muesli treat, crunchy and refreshing."},

    # ---- Fries ----
    {"id": "peri-peri-fries", "name": "Peri Peri Fries", "price": 60, "category": "Fries",
     "description": "Crispy fries tossed in tangy peri peri seasoning."},
    {"id": "masala-fries", "name": "Masala Fries", "price": 50, "category": "Fries",
     "description": "Crispy fries dusted with classic Indian masala."},

    # ---- Special ----
    {"id": "crispy-potato-bite-half", "name": "Crispy Potato Bite (Half)", "price": 50, "category": "Special",
     "description": "Crunchy spiced potato bites, fried golden."},
    {"id": "crispy-potato-bite-full", "name": "Crispy Potato Bite (Full)", "price": 90, "category": "Special",
     "description": "Crunchy spiced potato bites, fried golden."},
    {"id": "paneer-capsicum-bite-half", "name": "Paneer Capsicum Bite (Half)", "price": 90, "category": "Special",
     "description": "Paneer and capsicum bites, crispy and flavourful."},
    {"id": "paneer-capsicum-bite-full", "name": "Paneer Capsicum Bite (Full)", "price": 160, "category": "Special",
     "description": "Paneer and capsicum bites, crispy and flavourful."},

    # ---- Indo Chinese ----
    {"id": "veg-kawab-half", "name": "Veg Kawab (Half)", "price": 60, "category": "Indo Chinese",
     "description": "Spiced veg kebabs, pan seared and smoky."},
    {"id": "veg-kawab-full", "name": "Veg Kawab (Full)", "price": 99, "category": "Indo Chinese",
     "description": "Spiced veg kebabs, pan seared and smoky."},
    {"id": "veg-manchurian-half", "name": "Veg Manchurian (Half)", "price": 60, "category": "Indo Chinese",
     "description": "Fried veg balls tossed in classic Manchurian sauce."},
    {"id": "veg-manchurian-full", "name": "Veg Manchurian (Full)", "price": 99, "category": "Indo Chinese",
     "description": "Fried veg balls tossed in classic Manchurian sauce."},

    # ---- Combo ----
    {"id": "premium-combo", "name": "Premium Combo", "price": 199, "category": "Combo",
     "description": "Veg Noodles + Chilli Potato + Peri Peri Fries — a full meal deal."},
    {"id": "crunchy-combo", "name": "Crunchy Combo", "price": 139, "category": "Combo",
     "description": "Spring Roll + Half Fried Momo + Peri Peri Fries combo."},
]


def main():
    db = get_db()
    col = db.collection("menu")
    for dish in MENU:
        doc_id = dish["id"]
        payload = {k: v for k, v in dish.items() if k != "id"}
        payload["available"] = True
        col.document(doc_id).set(payload)
        print(f"  seeded menu/{doc_id}  {dish['name']}  ₹{dish['price']}")
    print(f"Done. {len(MENU)} dishes in 'menu' collection.")


if __name__ == "__main__":
    main()
