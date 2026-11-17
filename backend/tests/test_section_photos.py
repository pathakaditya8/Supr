"""Illustrative section photos (Unsplash) fall back correctly and never replace a vendor's own photo."""
from sqlalchemy import event, select

from app.database import SessionLocal, engine
from app.models import MenuSectionPhoto, Product, Vendor

FAKE = dict(image_url="https://images.unsplash.com/photo-test?w=800", photographer="Test Photographer",
            photographer_url="https://unsplash.com/@tester", photo_page_url="https://unsplash.com/photos/test", search_query="garlic bread")


def setup_section():
    db = SessionLocal()
    vendor = db.scalar(select(Vendor).where(Vendor.business_name == "Domino's")); vendor.status = "approved"
    items = db.scalars(select(Product).where(Product.vendor_id == vendor.id, Product.menu_section == "Garlic Breads & Dips")).all()
    for p in items: p.image_url = ""; p.menu_status = "published"
    if not db.scalar(select(MenuSectionPhoto).where(MenuSectionPhoto.vendor_id == vendor.id, MenuSectionPhoto.menu_section == "Garlic Breads & Dips")):
        db.add(MenuSectionPhoto(vendor_id=vendor.id, menu_section="Garlic Breads & Dips", **FAKE))
    ids = (vendor.id, items[0].id, items[1].id); db.commit(); db.close()
    return ids


def test_item_without_photo_shows_credited_section_photo(client):
    _, pid, _ = setup_section()
    item = client.get(f"/api/products/{pid}").json()
    assert item["image_url"] == FAKE["image_url"] and item["image_illustrative"] is True
    assert item["own_image_url"] == ""
    credit = item["image_credit"]
    assert credit["name"] == "Test Photographer" and credit["source"] == "Unsplash"
    assert credit["url"].startswith("https://unsplash.com/@tester?utm_source=") and "utm_medium=referral" in credit["source_url"]


def test_vendor_photo_always_wins(client):
    _, _, pid = setup_section()
    db = SessionLocal(); db.get(Product, pid).image_url = "/api/public/product-images/" + "a" * 32 + ".png"; db.commit(); db.close()
    item = client.get(f"/api/products/{pid}").json()
    assert item["image_url"].startswith("/api/public/product-images/")
    assert item["image_illustrative"] is False and item["image_credit"] is None
    db = SessionLocal(); db.get(Product, pid).image_url = ""; db.commit(); db.close()


def test_section_photos_do_not_add_per_item_queries(client):
    vendor_id, _, _ = setup_section()
    statements = []
    def listener(conn, cursor, statement, *a): statements.append(statement)
    event.listen(engine, "before_cursor_execute", listener)
    try:
        page = client.get("/api/products", params={"vendor_id": vendor_id, "limit": 48}).json()
    finally:
        event.remove(engine, "before_cursor_execute", listener)
    assert len(page["items"]) >= 20
    photo_queries = [s for s in statements if "menu_section_photos" in s]
    assert len(photo_queries) == 1, photo_queries
    assert len(statements) < 20, f"{len(statements)} queries for one page"


def test_vegetarian_item_never_gets_the_non_vegetarian_photo(client):
    """Mixed sections hold one photo per diet; a veg item must not fall back to the meat photo."""
    db = SessionLocal()
    vendor = db.scalar(select(Vendor).where(Vendor.business_name == "Domino's")); vendor.status = "approved"
    veg = db.scalar(select(Product).where(Product.vendor_id == vendor.id, Product.menu_section == "Tacos & Parcels", Product.dietary == "vegetarian"))
    meat = db.scalar(select(Product).where(Product.vendor_id == vendor.id, Product.menu_section == "Tacos & Parcels", Product.dietary == "non_vegetarian"))
    for p in (veg, meat): p.image_url = ""; p.menu_status = "published"
    db.add(MenuSectionPhoto(vendor_id=vendor.id, menu_section="Tacos & Parcels", dietary="non_vegetarian", **{**FAKE, "image_url": "https://images.unsplash.com/meat"}))
    db.commit(); veg_id, meat_id = veg.id, meat.id; db.close()
    assert client.get(f"/api/products/{meat_id}").json()["image_url"] == "https://images.unsplash.com/meat"
    assert client.get(f"/api/products/{veg_id}").json()["image_url"] == ""  # no veg photo yet: placeholder, not meat
    db = SessionLocal()
    vendor_id = db.scalar(select(Vendor.id).where(Vendor.business_name == "Domino's"))
    db.add(MenuSectionPhoto(vendor_id=vendor_id, menu_section="Tacos & Parcels", dietary="vegetarian", **{**FAKE, "image_url": "https://images.unsplash.com/veg"}))
    db.commit(); db.close()
    assert client.get(f"/api/products/{veg_id}").json()["image_url"] == "https://images.unsplash.com/veg"
