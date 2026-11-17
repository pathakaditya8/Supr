"""Order tracking: campus deliveries pass through 'out_for_delivery'; pickups go straight from ready to completed."""
import json, time
from sqlalchemy import select
from app.database import SessionLocal
from app.models import Product, Vendor

PASSWORD = "Track@123456"  # throwaway test-database account


def vendor_item(name, delivers):
    db = SessionLocal()
    v = db.scalar(select(Vendor).where(Vendor.business_name == name))
    v.status = "approved"; v.delivers_to_bmu = delivers; v.delivery_points_json = json.dumps(["Hostel Gate"] if delivers else [])
    p = db.scalar(select(Product).where(Product.vendor_id == v.id, Product.price.is_not(None), ~Product.variants.any()).limit(1))
    p.menu_status = "published"; p.available = True; p.stock = 50
    pid = p.id; db.commit(); db.close()
    return pid


def student(client, admin):
    email = f"track-{time.time_ns()}@supr.test"
    assert client.post("/api/admin/students", headers=admin, json={"name": "Tracker", "email": email, "phone": "9000000000", "password": PASSWORD}).status_code == 201
    return {"Authorization": "Bearer " + client.post("/api/auth/login", json={"email": email, "password": PASSWORD}).json()["access_token"]}


def order(client, headers, pid, location=""):
    client.delete("/api/cart", headers=headers)
    assert client.post("/api/cart/items", headers=headers, json={"product_id": pid, "quantity": 1}).status_code == 201
    r = client.post("/api/orders", headers=headers, json={"delivery_location": location})
    assert r.status_code == 201, r.text
    return r.json()["id"]


def move(client, vendor, oid, *statuses):
    for s in statuses:
        r = client.patch(f"/api/orders/{oid}/status", headers=vendor, json={"status": s})
        assert r.status_code == 200, (s, r.text)


def test_campus_delivery_goes_out_for_delivery_then_completes(client, auth_headers):
    pid = vendor_item("Kathi Junction", True)
    s = student(client, auth_headers["admin"])
    oid = order(client, s, pid, "Hostel Gate")
    vendor = auth_headers["vendor"]  # Kathi Junction
    move(client, vendor, oid, "accepted", "preparing", "ready", "out_for_delivery")
    mine = next(o for o in client.get("/api/orders", headers=s).json() if o["id"] == oid)
    assert mine["status"] == "out_for_delivery" and mine["campus_delivery"] is True
    assert client.post(f"/api/orders/{oid}/arrival", headers=vendor, json={"stage": "hostel_gate"}).status_code == 200
    assert next(o for o in client.get("/api/orders", headers=s).json() if o["id"] == oid)["delivery_stage"] == "hostel_gate"
    move(client, vendor, oid, "completed")
    notes = [n["message"] for n in client.get("/api/notifications", headers=s).json()["items"]]
    assert any(f"Order #{oid}: your order is on the way to campus." == m for m in notes)
    assert not any("out_for_delivery" in m for m in notes)  # students never see raw status codes
    metrics = client.get("/api/student/metrics", headers=s).json()
    assert metrics["completed_orders"] == 1 and metrics["pending_orders"] == 0


def test_pickup_order_cannot_be_marked_out_for_delivery(client, auth_headers):
    pid = vendor_item("Kathi Junction", False)
    s = student(client, auth_headers["admin"])
    oid = order(client, s, pid)
    vendor = auth_headers["vendor"]
    move(client, vendor, oid, "accepted", "preparing", "ready")
    assert client.patch(f"/api/orders/{oid}/status", headers=vendor, json={"status": "out_for_delivery"}).status_code == 409
    move(client, vendor, oid, "completed")


def test_on_the_way_order_counts_as_active(client, auth_headers):
    pid = vendor_item("Kathi Junction", True)
    s = student(client, auth_headers["admin"])
    oid = order(client, s, pid, "Hostel Gate")
    move(client, auth_headers["vendor"], oid, "accepted", "preparing", "ready", "out_for_delivery")
    assert client.get("/api/student/metrics", headers=s).json()["pending_orders"] == 1
    vendor_item("Kathi Junction", False)  # leave Kathi as pickup for other tests
