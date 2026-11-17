"""Add the laptop and phone shops from tech_vendors.py to a database (no reset).

Run from backend/: python -m app.import_tech_vendors
Safe to re-run: shops that already exist are skipped. Also called by app.seed.
"""
import secrets

from sqlalchemy import select

from .database import SessionLocal
from .models import Category, Product, User, Vendor, VendorApplication
from .security import hash_password
from .tech_vendors import LISTED_NOTE, TECH_CATEGORIES, TECH_VENDORS


def add_tech_vendors(db):
    categories = {c.name: c for c in db.scalars(select(Category))}
    for name in TECH_CATEGORIES:
        if name not in categories:
            categories[name] = Category(name=name); db.add(categories[name])
    db.flush()
    added = services = 0
    for shop in TECH_VENDORS:
        if db.scalar(select(Vendor).where(Vendor.business_name == shop["name"])):
            continue
        # Placeholder account with a random, unrecorded password: nobody can sign in as the shop.
        user = User(name=shop["name"], email=f"listing+{shop['slug']}@supr.invalid",
                    password_hash=hash_password(secrets.token_urlsafe(32)), role="vendor", enabled=False)
        db.add(user); db.flush()
        vendor = Vendor(user_id=user.id, business_name=shop["name"], phone=shop["phone"],
                        description=f"{shop['about']} {LISTED_NOTE}", status="listed", delivers_to_bmu=False,
                        agreement_valid=None, delivery_terms_note="", terms_confirmed=False)
        db.add(vendor); db.flush()
        db.add(VendorApplication(vendor_id=vendor.id, business_address=shop["address"], contact_person="Not confirmed",
                                 agreement_reference="", status="listed",
                                 decision_remarks="Listed from public information; the shop has not applied. Sources: " + "; ".join(shop["sources"])))
        for section, name, category, price, note in shop["services"]:
            db.add(Product(vendor_id=vendor.id, category_id=categories[category].id, name=name, description=note,
                           price=price, stock=0, available=False, image_url="", dietary="unspecified",
                           menu_section=section, menu_status="published"))
            services += 1
        added += 1
    return added, services


if __name__ == "__main__":
    db = SessionLocal()
    added, services = add_tech_vendors(db)
    db.commit(); db.close()
    print(f"Added {added} shop(s) with {services} service listing(s).")
