"""Dish photos: grouped by type and diet, credited, and never the wrong diet."""
from sqlalchemy import select
from app.database import SessionLocal
from app.dish_photos import dish_key
from app.models import DishPhoto, Product, Vendor


def test_dish_keys_group_by_type_and_keep_diet():
    assert dish_key("Paneer Tikka Roll", "Roll (Veg)", "Fast Food", "vegetarian")[0] == "kathi-roll|vegetarian"
    assert dish_key("Chicken Seekh Roll", "Roll (Non Veg)", "Fast Food", "non_vegetarian")[0] == "kathi-roll|non_vegetarian"
    assert dish_key("Chicken Fiesta", "Non-Veg Pizza", "Fast Food", "non_vegetarian")[0] == "pizza|non_vegetarian"
    assert dish_key("Peppy Paneer", "Veg Pizza", "Fast Food", "vegetarian")[0] == "pizza|vegetarian"
    assert dish_key("Chicken Fried Rice", "Rice", "Meals and Main Course", "non_vegetarian")[0] == "fried-rice|non_vegetarian"
    assert dish_key("Laptop screen replacement", "Laptop repairs", "Laptop Repair", "unspecified")[0] == "laptop-repair|any"
    # a vegetarian item can never be given a non-vegetarian photo key
    assert dish_key("Veg Biryani", "Biryani", "Meals and Main Course", "vegetarian")[0] == "biryani|vegetarian"


def test_item_gets_credited_dish_photo_and_own_photo_wins(client):
    db = SessionLocal()
    vendor = db.scalar(select(Vendor).where(Vendor.business_name == "Kathi Junction")); vendor.status = "approved"
    item = db.scalar(select(Product).where(Product.vendor_id == vendor.id, Product.name == "Aloo Roll"))
    item.menu_status = "published"; item.image_url = ""
    if not db.scalar(select(DishPhoto).where(DishPhoto.key == "kathi-roll|vegetarian")):
        db.add(DishPhoto(key="kathi-roll|vegetarian", query="paneer kathi roll", image_url="https://images.unsplash.com/photo-roll",
                         photographer="Test Photographer", photographer_url="https://unsplash.com/@tester", photo_page_url="https://unsplash.com/photos/roll"))
    pid = item.id; db.commit(); db.close()
    got = client.get(f"/api/products/{pid}").json()
    assert got["image_url"] == "https://images.unsplash.com/photo-roll" and got["image_illustrative"] is True
    assert got["image_credit"]["name"] == "Test Photographer" and got["image_credit"]["source"] == "Unsplash"
    db = SessionLocal(); db.get(Product, pid).image_url = "/api/public/product-images/" + "b" * 32 + ".png"; db.commit(); db.close()
    own = client.get(f"/api/products/{pid}").json()
    assert own["image_illustrative"] is False and own["image_credit"] is None
    db = SessionLocal(); db.get(Product, pid).image_url = ""; db.commit(); db.close()
