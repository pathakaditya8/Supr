from sqlalchemy import select
from app.database import SessionLocal
from app.models import Product, ProductVariant, Vendor

def test_login_and_invalid_login(client):
    assert client.post("/api/auth/login",json={"email":"student@supr.bmu.edu.in","password":"Demo@12345"}).status_code==200
    assert client.post("/api/auth/login",json={"email":"student@supr.bmu.edu.in","password":"wrong-password"}).status_code==401

def test_real_vendor_profiles_are_pending_and_not_public(client,auth_headers):
    applications=client.get("/api/admin/applications?status=pending",headers=auth_headers["admin"]).json()
    expected={"Kolkata's Lazeez","Kathi Junction","Greenox","Domino's"}
    assert expected.issubset({a["business_name"] for a in applications})
    public=client.get("/api/vendors").json()
    assert not any(v["business_name"] in expected for v in public)   # pending vendors stay hidden
    assert all(v["listed"] for v in public)                            # only shops listed from public information

def test_menu_hidden_until_vendor_approved_then_visible_but_not_orderable(client,auth_headers):
    # FR-13: a vendor's menu stays hidden while the vendor is pending.
    db=SessionLocal(); product=db.scalar(select(Product).where(Product.name=="Momos")); vendor=db.get(Vendor,product.vendor_id); product_id=product.id; vendor_id=vendor.id
    assert vendor.status=="pending"; db.close()
    assert client.get(f"/api/products?q=Momos&vendor_id={vendor_id}").json()["items"]==[]
    assert client.get(f"/api/products/{product_id}").status_code==404
    # Once approved, the published menu is visible at zero stock but cannot be ordered.
    db=SessionLocal(); db.get(Vendor,vendor_id).status="approved"; db.commit(); db.close()
    listing=client.get(f"/api/products?q=Momos&vendor_id={vendor_id}").json()["items"]
    assert [p["id"] for p in listing]==[product_id] and listing[0]["available"] is False
    assert client.get(f"/api/products/{product_id}").status_code==200
    assert client.get(f"/api/products?q=Momos&vendor_id={vendor_id}&available_only=true").json()["items"]==[]
    student=client.post("/api/auth/login",json={"email":"student@supr.bmu.edu.in","password":"Demo@12345"}).json()["access_token"]
    assert all(p["id"]!=product_id for p in client.get("/api/student/recommendations",headers={"Authorization":f"Bearer {student}"}).json())
    card=next(v for v in client.get("/api/vendors").json() if v["id"]==vendor_id)
    assert card["catalogue_count"]>0 and card["listing_count"]==0
    blocked=client.post("/api/cart/items",headers=auth_headers["student"],json={"product_id":product_id,"quantity":1})
    assert blocked.status_code in (409,422)
    # An admin-paused listing disappears from the student catalogue again.
    paused=client.patch(f"/api/admin/listings/{product_id}",headers=auth_headers["admin"],json={"menu_status":"paused","review_note":"Test pause."})
    assert paused.status_code==200
    assert client.get(f"/api/products/{product_id}").status_code==404
    db=SessionLocal(); db.get(Product,product_id).menu_status="published"; db.commit(); db.close()

def test_imported_menus_are_complete_and_start_out_of_stock(client,auth_headers):
    rows=client.get("/api/admin/listings",headers=auth_headers["admin"]).json()
    lazeez=[p for p in rows if p["vendor_name"]=="Kolkata's Lazeez"]
    kathi=[p for p in rows if p["vendor_name"]=="Kathi Junction"]
    dominos=[p for p in rows if p["vendor_name"]=="Domino's"]
    assert len(lazeez)==128 and len(kathi)==72 and len(dominos)==121
    assert all(p["menu_status"]=="published" and p["stock"]==0 and not p["available"] for p in lazeez+kathi+dominos)
    assert any(p["name"]=="Chicken Tikka" and {v["name"]:v["price"] for v in p["variants"]}=={"Half · 4 pcs":160,"Full · 8 pcs":300} for p in lazeez)
    assert any(p["name"]=="Butter Chicken" and [v["price"] for v in p["variants"]]==[110,170,280] for p in lazeez)
    assert any(p["name"]=="Dbl Paneer Roll" and p["price"]==100 for p in kathi)
    assert any(p["name"]=="Soft Drinks" and p["price"] is None for p in kathi)
    peppy=next(p for p in dominos if p["name"]=="Peppy Paneer")
    prices={v["name"]:v["price"] for v in peppy["variants"]}
    assert len(prices)==17 and prices["Regular · New Hand Tossed"]==269 and prices["Medium · New Hand Tossed"]==485 and prices["Large · New Hand Tossed"]==699
    assert peppy["dietary"]=="vegetarian" and peppy["price"]==269
    assert any(p["name"]=="Peppy Paneer (Cheese Burst)" for p in dominos)
    assert any(p["name"]=="Coca Cola 475ml" and p["price"]==66.66 and "5% GST" in p["description"] for p in dominos)

def test_momos_matrix_exact_prices_and_addons_unpriced(client,auth_headers):
    rows=client.get("/api/admin/listings",headers=auth_headers["admin"]).json()
    item=next(p for p in rows if p["name"]=="Momos")
    expected={"Steam · Veg Momos":70,"Steam · Paneer Momos":100,"Steam · Chicken Momos":100,"Fry · Veg Momos":80,"Kurkure · Chicken Momos":140,"Schezwan · Veg Momos":130,"Makhani · Paneer Momos":160,"Tandoori · Chicken Momos":160,"Afghani · Veg Momos":150,"Afghani · Chicken Momos":180,"Chilli Gravy · Paneer Momos":160}
    variants={v["name"]:v["price"] for v in item["variants"]}
    assert len(variants)==24
    assert all(variants[name]==price for name,price in expected.items())
    assert item["addons"]==[]
    roll=next(p for p in rows if p["vendor_name"]=="Kolkata's Lazeez" and p["name"]=="Egg Roll")
    addon_prices={a["name"]:a["price"] for a in roll["addons"]}
    assert addon_prices["Mayonise"]==10 and addon_prices["Dbl. Egg"]==30 and addon_prices["Wheat Base"]==0
    assert all(not a["available"] for a in roll["addons"])

def test_role_access_control(client,auth_headers):
    assert client.get("/api/admin/metrics",headers=auth_headers["student"]).status_code==403
    assert client.get("/api/vendor/products",headers=auth_headers["student"]).status_code==403

def test_variant_server_price_checkout_and_vendor_isolation(client,auth_headers):
    db=SessionLocal()
    product=db.scalar(select(Product).where(Product.name=="Momos"))
    vendor=db.get(Vendor,product.vendor_id)
    variant=db.scalar(select(ProductVariant).where(ProductVariant.product_id==product.id,ProductVariant.name=="Afghani · Chicken Momos"))
    vendor.status="approved"; product.available=True; product.menu_status="published"; product.stock=5; variant.available=True; db.commit(); db.close()
    ranged=client.get("/api/products?min_price=170&max_price=190").json()["items"]
    assert any(p["id"]==product.id for p in ranged)
    vegetarian=client.get("/api/products?dietary=vegetarian&q=Momos").json()["items"]
    assert any(p["id"]==product.id for p in vegetarian)
    response=client.post("/api/cart/items",headers=auth_headers["student"],json={"product_id":product.id,"quantity":1,"variant_id":variant.id})
    assert response.status_code==201 and response.json()["subtotal"]==180
    cart=client.get("/api/cart",headers=auth_headers["student"]).json()
    assert cart["items"][0]["unit_price"]==180
    order=client.post("/api/orders",headers=auth_headers["student"])
    assert order.status_code==201 and order.json()["subtotal"]==180
    orders=client.get("/api/orders",headers=auth_headers["vendor"]).json()
    assert not any(o["id"]==order.json()["id"] for o in orders)
    student_orders=client.get("/api/orders",headers=auth_headers["student"]).json()
    placed=next(o for o in student_orders if o["id"]==order.json()["id"])
    assert placed["items"][0]["variant_name"]=="Afghani · Chicken Momos"

def test_missing_variant_and_unknown_addon_rejected(client,auth_headers):
    db=SessionLocal(); product=db.scalar(select(Product).where(Product.name=="Momos")); variant=db.scalar(select(ProductVariant).where(ProductVariant.product_id==product.id)); product.available=True; product.menu_status="published"; product.stock=3; vendor=db.get(Vendor,product.vendor_id); vendor.status="approved"; db.commit(); db.close()
    no_variant=client.post("/api/cart/items",headers=auth_headers["student"],json={"product_id":product.id,"quantity":1})
    assert no_variant.status_code==422
    unknown_addon=client.post("/api/cart/items",headers=auth_headers["student"],json={"product_id":product.id,"quantity":1,"variant_id":variant.id,"addon_ids":[999999]})
    assert unknown_addon.status_code==422

def _approve_dominos_and_login(client):
    db=SessionLocal(); vendor=db.scalar(select(Vendor).where(Vendor.business_name=="Domino's")); vendor.status="approved"
    paused=db.scalar(select(Product).where(Product.vendor_id==vendor.id,Product.name=="Margherita")); paused.menu_status="paused"; paused.stock=0
    vendor_id,paused_id=vendor.id,paused.id; db.commit(); db.close()
    token=client.post("/api/auth/login",json={"email":"dominos@supr.demo","password":"Demo@12345"}).json()["access_token"]
    return {"Authorization":f"Bearer {token}"},vendor_id,paused_id

def test_vendor_bulk_availability_toggles_only_own_live_items(client,auth_headers):
    headers,vendor_id,paused_id=_approve_dominos_and_login(client)
    on=client.post("/api/vendor/products/availability",headers=headers,json={"available":True})
    assert on.status_code==200 and on.json()["updated"]==120 and on.json()["skipped_unpriced"]==0
    db=SessionLocal()
    rows=db.scalars(select(Product).where(Product.vendor_id==vendor_id)).all()
    live=[p for p in rows if p.id!=paused_id]
    assert all(p.stock>0 and p.available and p.menu_status=="published" for p in live)
    assert all(v.available for p in live for v in p.variants)
    paused=db.get(Product,paused_id); assert paused.menu_status=="paused" and paused.stock==0
    other=db.scalars(select(Product).join(Vendor).where(Vendor.business_name=="Kathi Junction")).all()
    assert all(p.stock==0 for p in other)
    db.close()
    farmhouse=next(p for p in client.get(f"/api/products?q=Farmhouse&vendor_id={vendor_id}").json()["items"] if p["name"]=="Farmhouse")
    assert farmhouse["available"]
    off=client.post("/api/vendor/products/availability",headers=headers,json={"available":False})
    assert off.status_code==200 and off.json()["updated"]==120
    db=SessionLocal()
    assert all(p.stock==0 and not any(v.available for v in p.variants) for p in db.scalars(select(Product).where(Product.vendor_id==vendor_id)))
    db.close()
    assert client.post("/api/vendor/products/availability",headers=auth_headers["student"],json={"available":True}).status_code==403

def test_vendor_uploads_food_photo_and_attaches_it(client):
    headers,vendor_id,_=_approve_dominos_and_login(client)
    png=b"\x89PNG\r\n\x1a\n"+b"\x00"*64
    up=client.post("/api/vendor/product-images",headers=headers,files={"file":("pizza.png",png,"image/png")})
    assert up.status_code==201
    url=up.json()["image_url"]
    assert client.get(url).status_code==200
    db=SessionLocal(); pid=db.scalar(select(Product.id).where(Product.vendor_id==vendor_id,Product.name=="Farmhouse")); db.close()
    saved=client.patch(f"/api/vendor/products/{pid}",headers=headers,json={"image_url":url})
    assert saved.status_code==200 and saved.json()["image_url"]==url
    bad=client.post("/api/vendor/product-images",headers=headers,files={"file":("pizza.png",b"not an image","image/png")})
    assert bad.status_code==415
