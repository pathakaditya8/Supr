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
from app.models import Cart, Notification, Product, User, Vendor
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

def test_self_registration_cannot_create_an_admin_or_a_student_without_a_bmu_address(client):
    r = client.post("/api/auth/register", json={"name": "Mallory", "email": "mallory-admin@supr.test", "password": TEST_PASSWORD, "role": "admin"})
    assert r.status_code == 403
    r = client.post("/api/auth/register", json={"name": "Mallory", "email": "mallory-student@supr.test", "password": TEST_PASSWORD, "role": "student"})
    assert r.status_code == 422
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


def test_emptied_cart_does_not_block_switching_vendors(client, auth_headers):
    first, _ = stocked_item("Kathi Junction")
    second, second_vendor = stocked_item("Domino's", "Garlic Breadsticks")
    student_id, student = new_student(client, auth_headers["admin"], "emptied")
    cart = client.post("/api/cart/items", headers=student, json={"product_id": first, "quantity": 1}).json()
    assert client.delete(f"/api/cart/items/{cart['items'][0]['cart_item_id']}", headers=student).status_code == 200
    db = SessionLocal(); saved = db.scalar(select(Cart).where(Cart.student_id == student_id)); assert saved.vendor_id is None; db.close()   # removing the last item frees the cart
    # a cart left empty but still pointing at its old vendor (an older build could leave this behind)
    db = SessionLocal()
    stale = db.scalar(select(Cart).where(Cart.student_id == student_id)); stale.vendor_id = stocked_item("Kathi Junction")[1]; db.commit(); db.close()
    r = client.post("/api/cart/items", headers=student, json={"product_id": second, "quantity": 1})
    assert r.status_code == 201, r.text
    assert r.json()["vendor_id"] == second_vendor


def test_admin_history_names_vendors_admins_and_every_decision(client):
    admin = login(client, "admin@supr.bmu.edu.in")
    _, vendor_id = stocked_item("Kathi Junction")
    assert client.post(f"/api/admin/vendors/{vendor_id}/participation", headers=admin, json={"status": "stopped"}).status_code == 200
    assert client.post(f"/api/admin/vendors/{vendor_id}/participation", headers=admin, json={"status": "approved"}).status_code == 200
    rows = client.get("/api/admin/history", headers=admin).json()
    assert rows and all(r["vendor_name"] and not r["vendor_name"].startswith("Vendor #") for r in rows)
    mine = client.get(f"/api/admin/history?vendor_id={vendor_id}", headers=admin).json()
    assert mine and {r["vendor_id"] for r in mine} == {vendor_id}
    labels = [r["label"] for r in mine]
    assert "Participation stopped" in labels and "Participation restarted" in labels
    assert labels.index("Participation restarted") < labels.index("Participation stopped")      # newest first
    decided = [r for r in mine if r["action"] in ("vendor_stopped", "vendor_restarted")]
    assert all(r["by"] == "BMU Marketplace Admin" for r in decided)
    assert any(r["action"] == "application_submitted" and r["by"] == "Vendor" for r in mine)
    assert client.get("/api/admin/history", headers=login(client, "kathijunction@supr.demo")).status_code == 403


def test_student_can_sign_up_only_with_name_yearcourse_bmu_address(client):
    def sign_up(email, password=TEST_PASSWORD, name="Test Student"):
        return client.post("/api/auth/register", json={"name": name, "email": email, "password": password, "role": "student"})
    tag = "t" + "".join(chr(97 + int(c)) for c in str(time.time_ns())[-8:])        # letters only: the name part has no digits
    good = f"{tag}.24cse@bmu.edu.in"
    ok = sign_up(good.upper())                                                   # case does not matter
    assert ok.status_code == 200, ok.text
    assert ok.json()["user"]["role"] == "student" and ok.json()["user"]["email"] == good
    assert login(client, good, TEST_PASSWORD)                                    # the new account can sign in
    assert sign_up(good).status_code == 409                                      # one account per address
    for bad in (f"{tag}24cse@bmu.edu.in", f"{tag}.24@bmu.edu.in", f"{tag}.2024cse@bmu.edu.in", f"{tag}.24cse@gmail.com",
                f"{tag}.24cse@bmu.edu.in.evil.com", f"{tag}.24cse@mail.bmu.edu.in", "dhruv@bmu.edu.in", ".24cse@bmu.edu.in", "x" + "." + "99cse@bmu.edu.in", f"{tag}.12cse@bmu.edu.in"):
        r = sign_up(bad)
        assert r.status_code == 422 and "name.yearcourse@bmu.edu.in" in r.json()["detail"], bad
    assert sign_up(f"{tag}x.24ece@bmu.edu.in", password="short").status_code == 422   # password rule still applies
    two_part = sign_up(f"{tag}.sharma.25bba@bmu.edu.in", name="With Surname")
    assert two_part.status_code == 200
    students = {u["email"] for u in client.get("/api/admin/students", headers=login(client, "admin@supr.bmu.edu.in")).json()}
    assert good in students and f"{tag}.sharma.25bba@bmu.edu.in" in students   # they appear in the admin's student list


def test_new_vendor_is_visible_to_the_admin_straight_after_registering(client):
    admin = login(client, "admin@supr.bmu.edu.in")
    name = f"Fresh Bites {time.time_ns() % 100000}"
    email = f"fresh-{time.time_ns()}@supr.test"
    before = {n["id"] for n in client.get("/api/notifications", headers=admin).json()["items"]}
    r = client.post("/api/auth/register", json={"name": name, "email": email, "password": TEST_PASSWORD, "role": "vendor"})
    assert r.status_code == 200, r.text
    # 1. the admin sees the vendor at once, labelled as not yet applied, and cannot approve something that was never sent
    listing = client.get("/api/admin/applications", headers=admin).json()
    row = next(a for a in listing if a["business_name"] == name)
    assert row["status"] == "unapplied" and row["vendor_status"] == "unapplied" and row["email"] == email and row["documents"] == []
    assert client.post(f"/api/admin/applications/{row['id']}/decision", headers=admin, json={"decision": "approved", "agreement_valid": True}).status_code == 404
    assert client.get("/api/admin/metrics", headers=admin).json()["unapplied_vendors"] >= 1
    # 2. the admin is told about it
    notes = [n for n in client.get("/api/notifications", headers=admin).json()["items"] if n["id"] not in before]
    assert any("New vendor registered" in n["message"] and name in n["message"] for n in notes)
    # 3. sending the application turns it into a pending application and notifies the admin again
    vendor = login(client, email, TEST_PASSWORD)
    sent = client.post("/api/vendor/applications", headers=vendor, json={"business_name": name, "phone": "9000000001", "description": "Snacks", "business_address": "Near BMU gate", "contact_person": "Owner Name", "delivery_partners": 2})
    assert sent.status_code in (200, 201), sent.text
    after = client.get("/api/admin/applications", headers=admin).json()
    assert [a["status"] for a in after if a["business_name"] == name] == ["pending"]          # no duplicate "unapplied" row
    assert any("sent a vendor application" in n["message"] and name in n["message"] for n in client.get("/api/notifications", headers=admin).json()["items"] if n["id"] not in before)
    # 4. the history records both steps
    vendor_id = row["vendor_id"]
    labels = [h["label"] for h in client.get(f"/api/admin/history?vendor_id={vendor_id}", headers=admin).json()]
    assert "Vendor registered" in labels and "Application submitted" in labels


TECH_NAMES = {"Laptop Repair", "Laptops and Accessories", "Phone Repair", "Phones and Accessories"}


def test_admin_listings_can_be_split_into_food_and_tech(client):
    admin = login(client, "admin@supr.bmu.edu.in")
    everything = client.get("/api/admin/listings", headers=admin).json()
    food = client.get("/api/admin/listings?kind=food", headers=admin).json()
    tech = client.get("/api/admin/listings?kind=tech", headers=admin).json()
    assert food and tech and len(food) + len(tech) == len(everything)
    assert not {p["category"] for p in food} & TECH_NAMES and {p["category"] for p in tech} <= TECH_NAMES
    assert {p["vendor_status"] for p in tech} == {"listed"} and "listed" not in {p["vendor_status"] for p in food}
    assert client.get("/api/admin/listings?kind=food", headers=login(client, "kathijunction@supr.demo")).status_code == 403


def test_admin_cannot_mix_food_and_tech_when_adding_a_listing(client):
    admin = login(client, "admin@supr.bmu.edu.in")
    cats = {c["name"]: c["id"] for c in client.get("/api/categories").json()}
    applications = client.get("/api/admin/applications", headers=admin).json()
    food_vendor = next(a["vendor_id"] for a in applications if a["vendor_status"] == "approved")
    tech_vendor = next(a["vendor_id"] for a in applications if a["vendor_status"] == "listed")
    body = {"name": "Mixed Up Item", "price": 100, "stock": 1, "description": "", "available": True}
    assert client.post("/api/admin/listings", headers=admin, json={**body, "vendor_id": food_vendor, "category_id": cats["Laptop Repair"]}).status_code == 422
    assert client.post("/api/admin/listings", headers=admin, json={**body, "vendor_id": tech_vendor, "category_id": cats["Fast Food"]}).status_code == 422
    assert client.post("/api/admin/listings", headers=admin, json={**body, "vendor_id": tech_vendor, "category_id": cats["Phone Repair"]}).status_code == 201
    assert client.post("/api/admin/listings", headers=admin, json={**body, "vendor_id": food_vendor, "category_id": cats["Fast Food"]}).status_code == 201


def test_application_needs_at_least_two_delivery_partners(client):
    admin = login(client, "admin@supr.bmu.edu.in")
    email = f"partners-{time.time_ns()}@supr.test"
    assert client.post("/api/auth/register", json={"name": "Partner Test Foods", "email": email, "password": TEST_PASSWORD, "role": "vendor"}).status_code == 200
    vendor = login(client, email, TEST_PASSWORD)
    form = {"business_name": "Partner Test Foods", "phone": "9000000002", "description": "Snacks", "business_address": "Near BMU gate", "contact_person": "Owner Name"}
    missing = client.post("/api/vendor/applications", headers=vendor, json=form)
    assert missing.status_code == 422 and missing.json()["detail"][0]["loc"][-1] == "delivery_partners"
    for count in (0, 1, -3):
        r = client.post("/api/vendor/applications", headers=vendor, json={**form, "delivery_partners": count})
        assert r.status_code == 422 and "At least 2 delivery partners" in r.json()["detail"][0]["msg"], count
    for bad in ("two", 2.5, None, 100000):
        assert client.post("/api/vendor/applications", headers=vendor, json={**form, "delivery_partners": bad}).status_code == 422, bad
    row = next(a for a in client.get("/api/admin/applications", headers=admin).json() if a["email"] == email)
    assert row["status"] == "unapplied"                                  # nothing was submitted by the refused attempts
    ok = client.post("/api/vendor/applications", headers=vendor, json={**form, "delivery_partners": 2})
    assert ok.status_code == 201, ok.text
    row = next(a for a in client.get("/api/admin/applications", headers=admin).json() if a["email"] == email)
    assert row["status"] == "pending" and row["delivery_partners"] == 2    # the admin can see the number
