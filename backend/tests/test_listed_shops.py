"""Laptop and phone shops listed from public information: visible, contactable, never orderable."""
from sqlalchemy import select

from app.database import SessionLocal
from app.models import User, Vendor
from app.tech_vendors import TECH_VENDORS


def test_tech_categories_exist(client):
    names = {c["name"] for c in client.get("/api/categories").json()}
    assert {"Laptop Repair", "Laptops and Accessories", "Phone Repair", "Phones and Accessories"} <= names


def test_listed_shops_are_public_and_clearly_labelled(client):
    shops = {v["business_name"]: v for v in client.get("/api/vendors").json() if v["listed"]}
    assert set(shops) == {s["name"] for s in TECH_VENDORS}
    for v in shops.values():
        assert "has not joined Supr yet" in v["description"]
        assert v["listing_count"] == 0                     # nothing orderable
    detail = client.get(f"/api/vendors/{shops['Make My Lappy']['id']}").json()
    assert detail["listed"] is True and detail["phone"] == "+91 98885 45174" and "Sadar Bazar" in detail["address"]


def test_only_published_prices_are_shown(client):
    items = client.get("/api/products", params={"q": "Refurbished laptop"}).json()["items"]
    assert [(i["price"], i["vendor_listed"], i["available"]) for i in items] == [(17000.0, True, False)]
    visit = client.get("/api/products", params={"q": "Doorstep visit"}).json()["items"][0]
    assert visit["price"] == 500.0 and "adjusted into your bill" in visit["description"]
    screen = client.get("/api/products", params={"q": "Laptop screen replacement"}).json()["items"][0]
    assert screen["price"] is None                         # no invented prices


def test_listed_shop_cannot_take_orders(client, auth_headers):
    item = client.get("/api/products", params={"q": "Refurbished laptop"}).json()["items"][0]
    r = client.post("/api/cart/items", headers=auth_headers["student"], json={"product_id": item["id"], "quantity": 1})
    assert r.status_code == 409 and "has not joined Supr yet" in r.json()["detail"]


def test_nobody_can_sign_in_as_a_listed_shop(client):
    db = SessionLocal()
    users = db.scalars(select(User).join(Vendor, Vendor.user_id == User.id).where(Vendor.status == "listed")).all()
    assert len(users) == len(TECH_VENDORS)
    assert all(not u.enabled and u.email.endswith("@supr.invalid") for u in users)
    emails = [u.email for u in users]; db.close()
    for email in emails:
        assert client.post("/api/auth/login", json={"email": email, "password": "Demo@12345"}).status_code == 401


def test_food_and_tech_items_can_be_listed_separately(client):
    from app.main import FOOD_CATEGORIES, TECH_CATEGORIES
    food = client.get("/api/products", params={"kind": "food", "limit": 100}).json()
    tech = client.get("/api/products", params={"kind": "tech", "limit": 100}).json()
    assert tech["total"] == 34 and all(i["category"] in TECH_CATEGORIES for i in tech["items"])
    assert all(i["category"] in FOOD_CATEGORIES for i in food["items"])
    assert client.get("/api/products", params={"kind": "food", "q": "laptop"}).json()["total"] == 0


def test_vendor_summary_for_the_landing_page(client):
    rows = {v["business_name"]: v for v in client.get("/api/vendors").json()}
    lappy = rows["Make My Lappy"]
    assert lappy["kind"] == "tech" and lappy["min_price"] == 500.0      # free diagnosis (₹0) is not a "from" price
    assert "Laptop Repair" in lappy["top_categories"]
    assert rows["AJ Mobile Repairing Hub"]["min_price"] is None         # no published prices
    assert "Chaudhary Mobile Centre" not in rows                         # removed on request


def test_shop_images_are_served_with_vendors(client):
    rows = {v["business_name"]: v for v in client.get("/api/vendors").json()}
    assert rows["Make My Lappy"]["image_url"] == "/vendors/make-my-lappy-logo.png"
    assert rows["Vislor Electronics"]["image_url"] == ""                 # no official image: name tile
    assert client.get(f"/api/vendors/{rows['Make My Lappy']['id']}").json()["image_url"] == "/vendors/make-my-lappy-logo.png"
