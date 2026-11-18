"""Cart and Order Management module: the six cases of the unit test case submission (TC01 to TC06), plus the rule that a
failed checkout is never shown as a successful order (TC07).

When SUPR_RECORD_ACTUALS names a file, each test also writes what the system actually returned, one JSON line per case,
so the submission document can quote real output instead of expectations.
"""
import json
import os

from sqlalchemy import func, select
from test_security import login, new_student, stocked_item

from app.database import SessionLocal
from app.models import Order, Product


def record(case, text):
    path = os.environ.get("SUPR_RECORD_ACTUALS")
    if path:
        with open(path, "a", encoding="utf-8") as f: f.write(json.dumps({"case": case, "actual": text}) + "\n")


def order_count(student_id):
    db = SessionLocal()
    try: return db.scalar(select(func.count()).select_from(Order).where(Order.student_id == student_id))
    finally: db.close()


def test_tc01_add_an_available_product_to_the_cart(client):
    product_id, _ = stocked_item("Kathi Junction")
    _, student = new_student(client, login(client, "admin@supr.bmu.edu.in"), "tc01")
    r = client.post("/api/cart/items", headers=student, json={"product_id": product_id, "quantity": 1})
    assert r.status_code == 201
    cart = r.json()
    assert len(cart["items"]) == 1 and cart["items"][0]["id"] == product_id and cart["items"][0]["quantity"] == 1
    assert cart["subtotal"] == cart["items"][0]["line_total"] > 0
    record("TC01", f"HTTP 201. Cart holds 1 line: {cart['items'][0]['name']} x {cart['items'][0]['quantity']}; subtotal Rs {cart['subtotal']:g}.")


def test_tc02_attempt_to_add_an_unavailable_product(client):
    product_id, _ = stocked_item("Kathi Junction")
    db = SessionLocal(); db.get(Product, product_id).available = False; db.commit(); db.close()
    _, student = new_student(client, login(client, "admin@supr.bmu.edu.in"), "tc02")
    try:
        r = client.post("/api/cart/items", headers=student, json={"product_id": product_id, "quantity": 1})
        assert r.status_code == 409 and "unavailable" in r.json()["detail"]
        cart = client.get("/api/cart", headers=student).json()
        assert cart["items"] == []                                   # nothing was added
        record("TC02", f"HTTP 409: \"{r.json()['detail']}\". Cart stays empty.")
    finally:
        db = SessionLocal(); db.get(Product, product_id).available = True; db.commit(); db.close()


def test_tc03_prevent_products_from_different_sellers_in_one_cart(client):
    first, _ = stocked_item("Kathi Junction")
    second, _ = stocked_item("Domino's", "Garlic Breadsticks")
    _, student = new_student(client, login(client, "admin@supr.bmu.edu.in"), "tc03")
    assert client.post("/api/cart/items", headers=student, json={"product_id": first, "quantity": 1}).status_code == 201
    r = client.post("/api/cart/items", headers=student, json={"product_id": second, "quantity": 1})
    assert r.status_code == 409 and "one vendor only" in r.json()["detail"]
    cart = client.get("/api/cart", headers=student).json()
    assert [i["id"] for i in cart["items"]] == [first] and cart["vendor_name"] == "Kathi Junction"   # sellers are never mixed
    record("TC03", f"HTTP 409: \"{r.json()['detail']}\" Cart still holds only the Kathi Junction item.")


def test_tc04_attempt_checkout_with_an_empty_cart(client):
    _, student = new_student(client, login(client, "admin@supr.bmu.edu.in"), "tc04")
    student_id = client.get("/api/auth/me", headers=student).json()["id"]
    r = client.post("/api/orders", headers=student, json={"delivery_location": ""})
    assert r.status_code == 400 and r.json()["detail"] == "Your cart is empty"
    assert order_count(student_id) == 0
    record("TC04", f"HTTP 400: \"{r.json()['detail']}\". No order created.")


def test_tc05_validate_product_quantity(client):
    product_id, _ = stocked_item("Kathi Junction")
    _, student = new_student(client, login(client, "admin@supr.bmu.edu.in"), "tc05")
    student_id = client.get("/api/auth/me", headers=student).json()["id"]
    refused = []
    for quantity in (0, -1, 100):
        r = client.post("/api/cart/items", headers=student, json={"product_id": product_id, "quantity": quantity})
        assert r.status_code == 422, quantity
        refused.append(quantity)
    assert client.get("/api/cart", headers=student).json()["items"] == []        # no cart item was created
    assert order_count(student_id) == 0                                           # and no order
    record("TC05", f"HTTP 422 for quantity {', '.join(map(str, refused))} (allowed 1 to 99). No cart item or order created.")


def test_tc06_place_an_order_using_a_valid_cart(client):
    product_id, vendor_id = stocked_item("Kathi Junction")
    student_id, student = new_student(client, login(client, "admin@supr.bmu.edu.in"), "tc06")
    db = SessionLocal(); before = db.get(Product, product_id).stock; db.close()
    client.post("/api/cart/items", headers=student, json={"product_id": product_id, "quantity": 2})
    r = client.post("/api/orders", headers=student, json={"delivery_location": ""})
    assert r.status_code == 201
    order = r.json()
    assert order["status"] == "pending" and order["subtotal"] > 0 and order_count(student_id) == 1     # a single order
    detail = client.get(f"/api/orders/{order['id']}", headers=student).json()                           # details are stored
    assert len(detail["items"]) == 1 and detail["items"][0]["quantity"] == 2 and detail["vendor"]["id"] == vendor_id
    assert client.get("/api/cart", headers=student).json()["items"] == []                                # the cart is emptied
    db = SessionLocal(); assert db.get(Product, product_id).stock == before - 2; db.close()             # stock reduced
    record("TC06", f"HTTP 201. One order created, status {order['status']}, subtotal Rs {order['subtotal']:g}; details stored, cart emptied, stock reduced by 2.")


def test_tc07_failed_checkout_is_not_shown_as_a_successful_order(client):
    product_id, _ = stocked_item("Kathi Junction")
    student_id, student = new_student(client, login(client, "admin@supr.bmu.edu.in"), "tc07")
    client.post("/api/cart/items", headers=student, json={"product_id": product_id, "quantity": 1})
    db = SessionLocal(); db.get(Product, product_id).stock = 0; db.commit(); db.close()        # it sells out before checkout
    try:
        r = client.post("/api/orders", headers=student, json={"delivery_location": ""})
        assert r.status_code == 409 and "no longer available" in r.json()["detail"]
        assert "id" not in r.json() and order_count(student_id) == 0                              # no order, no order number
        assert len(client.get("/api/cart", headers=student).json()["items"]) == 1                  # the cart is kept for the student
        record("TC07", f"HTTP 409: \"{r.json()['detail']}\". No order created; the cart is kept.")
    finally:
        db = SessionLocal(); db.get(Product, product_id).stock = 50; db.commit(); db.close()
