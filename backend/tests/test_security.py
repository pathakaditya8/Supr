"""Security and access-control tests (CSE3005 security testing).

Each test sets up the state it needs, so the file does not depend on test order.
Test passwords below are fixture values for the throwaway test database only.
"""
import base64
import json
import time

import pytest
from sqlalchemy import select

from app.database import SessionLocal
from app.models import Notification, Product, User, Vendor
from app.security import issue_token

TEST_PASSWORD = "Test@123456"


def login(client, email, password="Demo@12345"):
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def stocked_item(vendor_name, product_name=None):
    """Approve the vendor and make one simple (no-variant) item orderable. Returns (product_id, vendor_id)."""
    db = SessionLocal()
    vendor = db.scalar(select(Vendor).where(Vendor.business_name == vendor_name))
    vendor.status = "approved"; vendor.delivers_to_bmu = False
    query = select(Product).where(Product.vendor_id == vendor.id, Product.price.is_not(None), ~Product.variants.any())
    if product_name: query = query.where(Product.name == product_name)
    product = db.scalar(query.limit(1))
    product.menu_status = "published"; product.available = True; product.stock = 50
    ids = (product.id, vendor.id); db.commit(); db.close()
    return ids


def new_student(client, admin, tag):
    email = f"sec-{tag}-{time.time_ns()}@supr.test"
    r = client.post("/api/admin/students", headers=admin, json={"name": f"Security {tag}", "email": email, "phone": "9000000000", "password": TEST_PASSWORD})
    assert r.status_code == 201, r.text
    return r.json()["id"], login(client, email, TEST_PASSWORD)


def place_order(client, student, product_id):
    client.delete("/api/cart", headers=student)
    assert client.post("/api/cart/items", headers=student, json={"product_id": product_id, "quantity": 1}).status_code == 201
    r = client.post("/api/orders", headers=student, json={"delivery_location": ""})
    assert r.status_code == 201, r.text
    return r.json()["id"]


# ---------- Registration and tokens ----------

def test_self_registration_cannot_create_admin_or_student(client):
    for role in ("admin", "student"):
        r = client.post("/api/auth/register", json={"name": "Mallory", "email": f"mallory-{role}@supr.test", "password": TEST_PASSWORD, "role": role})
        assert r.status_code == 403
    weak = client.post("/api/auth/register", json={"name": "Weak", "email": "weak@supr.test", "password": "short", "role": "vendor"})
    assert weak.status_code == 422
    dup = client.post("/api/auth/register", json={"name": "Dup", "email": "student@supr.bmu.edu.in", "password": TEST_PASSWORD, "role": "vendor"})
    assert dup.status_code == 409


def test_tampered_forged_and_expired_tokens_are_rejected(client, auth_headers, monkeypatch):
    student_token = auth_headers["student"]["Authorization"].split()[1]
    payload, sig = student_token.split(".")
    data = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
    data["role"] = "admin"
    forged_payload = base64.urlsafe_b64encode(json.dumps(data).encode()).decode().rstrip("=")
    # Role changed but signature kept: must be rejected.
    assert client.get("/api/admin/metrics", headers={"Authorization": f"Bearer {forged_payload}.{sig}"}).status_code == 401
    for bad in ("garbage", "a.b", "", "Bearer"):
        assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {bad}"}).status_code == 401
    assert client.get("/api/auth/me").status_code == 401
    # A real token stops working once its expiry passes.
    token = issue_token(1, "admin")
    real_time = time.time
    monkeypatch.setattr(time, "time", lambda: real_time() + 7 * 24 * 3600)
    assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_disabled_student_token_stops_working(client, auth_headers):
    student_id, headers = new_student(client, auth_headers["admin"], "disable")
    assert client.get("/api/auth/me", headers=headers).status_code == 200
    assert client.delete(f"/api/admin/students/{student_id}", headers=auth_headers["admin"]).status_code == 200
    assert client.get("/api/auth/me", headers=headers).status_code == 401


def test_login_error_does_not_reveal_which_part_was_wrong(client):
    unknown = client.post("/api/auth/login", json={"email": "nobody@supr.test", "password": "whatever-123"})
    wrong = client.post("/api/auth/login", json={"email": "student@supr.bmu.edu.in", "password": "whatever-123"})
    assert unknown.status_code == wrong.status_code == 401
    assert unknown.json() == wrong.json()


# ---------- Role boundaries ----------

@pytest.mark.parametrize("method,path", [
    ("get", "/api/admin/applications"), ("get", "/api/admin/history"), ("get", "/api/admin/students"),
    ("get", "/api/admin/listings"), ("get", "/api/admin/documents/1"), ("post", "/api/admin/vendors/1/participation"),
])
def test_admin_endpoints_refuse_students_and_vendors(client, auth_headers, method, path):
    for role in ("student", "vendor"):
        r = getattr(client, method)(path, headers=auth_headers[role], **({"json": {"status": "stopped"}} if method == "post" else {}))
        assert r.status_code == 403, (role, path, r.status_code)


def test_vendor_endpoints_refuse_students(client, auth_headers):
    student = auth_headers["student"]
    assert client.post("/api/vendor/products/availability", headers=student, json={"available": True}).status_code == 403
    assert client.post("/api/vendor/product-images", headers=student, files={"file": ("x.png", b"\x89PNG\r\n\x1a\n", "image/png")}).status_code == 403
    assert client.patch("/api/orders/1/status", headers=student, json={"status": "accepted"}).status_code == 403


# ---------- Ownership (one user reaching another user's data) ----------

def test_student_cannot_see_or_cancel_another_students_order(client, auth_headers):
    product_id, _ = stocked_item("Kathi Junction")
    _, alice = new_student(client, auth_headers["admin"], "alice")
    _, bob = new_student(client, auth_headers["admin"], "bob")
    order_id = place_order(client, alice, product_id)
    assert all(o["id"] != order_id for o in client.get("/api/orders", headers=bob).json())
    assert client.post(f"/api/orders/{order_id}/cancel", headers=bob).status_code == 404
    assert client.post(f"/api/orders/{order_id}/cancel", headers=alice).status_code == 200


def test_vendor_cannot_touch_another_vendors_listing_or_order(client, auth_headers):
    product_id, _ = stocked_item("Domino's", "Garlic Breadsticks")
    _, student = new_student(client, auth_headers["admin"], "xvendor")
    order_id = place_order(client, student, product_id)
    kathi = auth_headers["vendor"]  # Kathi Junction's vendor account
    stocked_item("Kathi Junction")  # make sure Kathi is approved
    assert client.patch(f"/api/vendor/products/{product_id}", headers=kathi, json={"price": 1}).status_code == 404
    assert client.delete(f"/api/vendor/products/{product_id}", headers=kathi).status_code == 404
    assert client.put(f"/api/vendor/products/{product_id}/variants", headers=kathi, json={"variants": []}).status_code == 404
    assert client.patch(f"/api/orders/{order_id}/status", headers=kathi, json={"status": "accepted"}).status_code == 404
    assert all(o["id"] != order_id for o in client.get("/api/orders", headers=kathi).json())
    db = SessionLocal(); assert float(db.get(Product, product_id).price) != 1; db.close()


def test_user_cannot_mark_someone_elses_notification(client, auth_headers):
    db = SessionLocal()
    admin = db.scalar(select(User).where(User.role == "admin"))
    note = Notification(recipient_id=admin.id, event_type="test", message="private")
    db.add(note); db.commit(); nid = note.id; db.close()
    assert client.post(f"/api/notifications/{nid}/read", headers=auth_headers["student"]).status_code == 404
    db = SessionLocal(); assert db.get(Notification, nid).read is False; db.close()


# ---------- Business rules that protect data integrity ----------

def test_cart_refuses_items_from_a_second_vendor(client, auth_headers):
    first, _ = stocked_item("Kathi Junction")
    second, _ = stocked_item("Domino's", "Garlic Breadsticks")
    _, student = new_student(client, auth_headers["admin"], "twovendor")
    assert client.post("/api/cart/items", headers=student, json={"product_id": first, "quantity": 1}).status_code == 201
    r = client.post("/api/cart/items", headers=student, json={"product_id": second, "quantity": 1})
    assert r.status_code == 409 and "one vendor" in r.json()["detail"]


def test_stopped_vendor_is_hidden_and_cannot_be_ordered_from(client, auth_headers):
    product_id, vendor_id = stocked_item("Kathi Junction")
    _, student = new_student(client, auth_headers["admin"], "stopped")
    assert client.post("/api/cart/items", headers=student, json={"product_id": product_id, "quantity": 1}).status_code == 201
    assert client.post(f"/api/admin/vendors/{vendor_id}/participation", headers=auth_headers["admin"], json={"status": "stopped"}).status_code == 200
    try:
        assert client.get(f"/api/products/{product_id}").status_code == 404
        assert client.post("/api/orders", headers=student, json={"delivery_location": ""}).status_code == 409
    finally:
        client.post(f"/api/admin/vendors/{vendor_id}/participation", headers=auth_headers["admin"], json={"status": "approved"})


def test_order_status_cannot_skip_steps(client, auth_headers):
    product_id, _ = stocked_item("Kathi Junction")
    _, student = new_student(client, auth_headers["admin"], "skip")
    order_id = place_order(client, student, product_id)
    vendor = auth_headers["vendor"]
    assert client.patch(f"/api/orders/{order_id}/status", headers=vendor, json={"status": "completed"}).status_code == 409
    assert client.patch(f"/api/orders/{order_id}/status", headers=vendor, json={"status": "accepted"}).status_code == 200
    assert client.post(f"/api/orders/{order_id}/cancel", headers=student).status_code == 409  # only pending orders


def test_cancelling_restores_stock(client, auth_headers):
    product_id, _ = stocked_item("Kathi Junction")
    db = SessionLocal(); before = db.get(Product, product_id).stock; db.close()
    _, student = new_student(client, auth_headers["admin"], "restock")
    order_id = place_order(client, student, product_id)
    db = SessionLocal(); assert db.get(Product, product_id).stock == before - 1; db.close()
    assert client.post(f"/api/orders/{order_id}/cancel", headers=student).status_code == 200
    db = SessionLocal(); assert db.get(Product, product_id).stock == before; db.close()


def test_client_cannot_set_its_own_price(client, auth_headers):
    product_id, _ = stocked_item("Kathi Junction")
    _, student = new_student(client, auth_headers["admin"], "price")
    r = client.post("/api/cart/items", headers=student, json={"product_id": product_id, "quantity": 1, "price": 0, "unit_price": 0, "subtotal": 0})
    db = SessionLocal(); real = float(db.get(Product, product_id).price); db.close()
    assert r.status_code == 201 and r.json()["subtotal"] == real


# ---------- Input handling ----------

@pytest.mark.parametrize("term", ["' OR 1=1 --", "\"; DROP TABLE products; --", "<script>alert(1)</script>", "%' UNION SELECT password_hash FROM users --"])
def test_injection_shaped_search_is_harmless(client, term):
    r = client.get("/api/products", params={"q": term})
    assert r.status_code == 200 and r.json()["items"] == []
    db = SessionLocal(); assert db.scalar(select(Product).limit(1)) is not None; db.close()


def test_uploads_reject_wrong_type_fake_content_and_oversize(client, auth_headers):
    stocked_item("Domino's", "Garlic Breadsticks")
    vendor = login(client, "dominos@supr.demo")
    def up(name, data, kind="image/png"):
        return client.post("/api/vendor/product-images", headers=vendor, files={"file": (name, data, kind)}).status_code
    assert up("shell.php", b"<?php system($_GET['c']); ?>", "application/x-php") == 415
    assert up("photo.svg", b"<svg onload=alert(1)>", "image/svg+xml") == 415
    assert up("photo.png", b"GIF89a not really a png") == 415
    assert up("big.png", b"\x89PNG\r\n\x1a\n" + b"0" * (5 * 1024 * 1024)) == 413
    ok = client.post("/api/vendor/product-images", headers=vendor, files={"file": ("../../../evil.png", b"\x89PNG\r\n\x1a\n" + b"0" * 32, "image/png")})
    assert ok.status_code == 201
    name = ok.json()["image_url"].rsplit("/", 1)[1]
    assert ".." not in name and len(name) == 36  # random 32-hex name + .png, path ignored


@pytest.mark.parametrize("name", ["..%2F..%2Fsupr.db", "../app/config.py", "secret.txt", "AAAA.png"])
def test_public_image_route_refuses_path_tricks(client, name):
    assert client.get(f"/api/public/product-images/{name}").status_code == 404


def test_error_responses_do_not_leak_internals(client, auth_headers):
    r = client.post("/api/cart/items", headers=auth_headers["student"], json={"product_id": 999999999, "quantity": 1})
    body = r.text.lower()
    assert r.status_code in (404, 409)
    for leak in ("traceback", "sqlalchemy", "select ", "password_hash", "secret"):
        assert leak not in body


def test_keep_alive_is_off_by_default_and_only_uses_https(monkeypatch):
    from app import keepalive
    monkeypatch.delenv("KEEP_ALIVE", raising=False)
    assert keepalive.target_url() is None
    monkeypatch.setenv("KEEP_ALIVE", "true")
    monkeypatch.setenv("RENDER_EXTERNAL_URL", "http://insecure.example")
    assert keepalive.target_url() is None
    monkeypatch.setenv("RENDER_EXTERNAL_URL", "https://supr-api.onrender.com/")
    assert keepalive.target_url() == "https://supr-api.onrender.com/api/health"


def test_change_password_requires_current_password_and_works(client):
    headers = login(client, "student@supr.bmu.edu.in")
    wrong = client.post("/api/auth/change-password", headers=headers, json={"current_password": "wrong-password", "new_password": "Another-pass-123"})
    assert wrong.status_code == 400
    short = client.post("/api/auth/change-password", headers=headers, json={"current_password": "Demo@12345", "new_password": "short"})
    assert short.status_code == 422
    same = client.post("/api/auth/change-password", headers=headers, json={"current_password": "Demo@12345", "new_password": "Demo@12345"})
    assert same.status_code == 400
    assert client.post("/api/auth/change-password", json={"current_password": "x", "new_password": "Another-pass-123"}).status_code in (401, 403)
    ok = client.post("/api/auth/change-password", headers=headers, json={"current_password": "Demo@12345", "new_password": "Another-pass-123"})
    assert ok.status_code == 200
    assert client.post("/api/auth/login", json={"email": "student@supr.bmu.edu.in", "password": "Demo@12345"}).status_code == 401
    assert client.post("/api/auth/login", json={"email": "student@supr.bmu.edu.in", "password": "Another-pass-123"}).status_code == 200
    # restore so later tests in the session still sign in with the demo password
    back = client.post("/api/auth/change-password", headers=headers, json={"current_password": "Another-pass-123", "new_password": "Demo@12345"})
    assert back.status_code == 200


def test_admin_can_set_student_and_vendor_passwords_but_nobody_else_can(client):
    admin = login(client, "admin@supr.bmu.edu.in")
    student = login(client, "student@supr.bmu.edu.in")
    vendor = login(client, "kathijunction@supr.demo")
    ids = {u["email"]: u["id"] for u in client.get("/api/admin/students", headers=admin).json()}
    student_id = ids["student@supr.bmu.edu.in"]
    vendor_id = client.get("/api/admin/applications", headers=admin).json()
    vendor_user = next(a["user_id"] for a in vendor_id if a["email"] == "kathijunction@supr.demo")
    new = {"new_password": "Reset-by-admin-1"}
    assert client.post(f"/api/admin/users/{student_id}/password", headers=student, json=new).status_code == 403
    assert client.post(f"/api/admin/users/{student_id}/password", headers=vendor, json=new).status_code == 403
    assert client.post(f"/api/admin/users/{student_id}/password", json=new).status_code in (401, 403)
    assert client.post(f"/api/admin/users/{student_id}/password", headers=admin, json={"new_password": "short"}).status_code == 422
    for uid, email in ((student_id, "student@supr.bmu.edu.in"), (vendor_user, "kathijunction@supr.demo")):
        assert client.post(f"/api/admin/users/{uid}/password", headers=admin, json=new).status_code == 200
        assert client.post("/api/auth/login", json={"email": email, "password": "Demo@12345"}).status_code == 401
        assert client.post("/api/auth/login", json={"email": email, "password": new["new_password"]}).status_code == 200
        assert client.post(f"/api/admin/users/{uid}/password", headers=admin, json={"new_password": "Demo@12345"}).status_code == 200   # restore
    admin_id = client.get("/api/auth/me", headers=admin).json()["id"]
    assert client.post(f"/api/admin/users/{admin_id}/password", headers=admin, json=new).status_code == 404          # admins use their own profile
    assert client.post("/api/admin/users/999999/password", headers=admin, json=new).status_code == 404
