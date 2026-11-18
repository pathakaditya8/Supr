"""Browser end-to-end tests (system testing) for Supr's main user journeys.

Each run starts an isolated backend + frontend with a freshly seeded database
(see stack.py). Run from the project root:
    backend/.venv311/Scripts/python.exe -m pytest e2e -v
"""
import re
from playwright.sync_api import expect
from conftest import sign_in, tab, clear_cart
from stack import call, token

STUDENT = "student@supr.bmu.edu.in"
ADMIN = "admin@supr.bmu.edu.in"
KATHI = "kathijunction@supr.demo"
DOMINOS = "dominos@supr.demo"


def open_vendor(page, name):
    page.get_by_role("navigation").get_by_role("button", name="Vendors", exact=True).click()  # vendors have their own page
    tile = page.get_by_role("button", name=re.compile(rf"^{re.escape(name)} \d+ menu items"))
    page.wait_for_load_state("networkidle")  # the vendor list re-renders once its data arrives
    for attempt in range(3):
        try:
            tile.click(timeout=5_000); break
        except Exception:
            if attempt == 2: raise
            page.wait_for_load_state("networkidle")
    expect(page.get_by_role("heading", name=name, level=1)).to_be_visible()


def wait_for_dialog(page, count, seconds=10):
    for _ in range(seconds * 10):
        if len(page.dialog_messages) >= count: return
        page.wait_for_timeout(100)
    raise AssertionError(f"expected {count} confirm prompt(s), saw {page.dialog_messages}")


def add_item(page, item):
    page.get_by_role("article").filter(has=page.get_by_role("heading", name=item, exact=True)).get_by_role("button", name="Add", exact=True).click()


def test_e2e_01_wrong_password_is_refused(new_page):
    page = new_page()
    sign_in(page, STUDENT, "not-the-password")
    expect(page.get_by_text("Email or password is incorrect")).to_be_visible()
    expect(page.locator(".workspace-tabs")).to_have_count(0)


def test_e2e_02_student_orders_and_vendor_fulfils(new_page):
    clear_cart(STUDENT)
    student = new_page()
    sign_in(student, STUDENT)
    expect(student.locator(".workspace-tabs")).to_be_visible()
    open_vendor(student, "Kathi Junction")
    add_item(student, "Aloo Roll")
    expect(student.get_by_text("Aloo Roll added to your bag")).to_be_visible()
    student.get_by_role("button", name="Shopping bag").click()
    student.get_by_role("button", name="Review order").click()
    student.get_by_role("button", name=re.compile(r"^Place order request")).click()
    expect(student.get_by_text(re.compile(r"Order #\d+")).first).to_be_visible()
    order_id = max(o["id"] for o in call("GET", "/api/orders", token=token(STUDENT)))

    vendor = new_page()
    sign_in(vendor, KATHI)
    tab(vendor, "Orders")
    row = vendor.locator(".record-row, .order-row, .application-card").filter(has_text=f"#{order_id}")
    expect(row.first).to_be_visible()
    row.first.get_by_role("button", name="Accept", exact=True).click()
    expect(vendor.get_by_text("Order marked accepted")).to_be_visible()
    row.first.get_by_role("button", name="Mark preparing").click()
    expect(vendor.get_by_text("Order marked preparing")).to_be_visible()

    expect(student.get_by_role("heading", name=re.compile("^Thanks"))).to_be_visible()
    student.get_by_role("button", name="View my orders").click()
    student.reload(); student.wait_for_load_state("networkidle")
    tab(student, "Your orders")
    card = student.locator(".order-card").filter(has_text=f"Order #{order_id}")
    expect(card.locator(".status-pill")).to_have_text("Being prepared")
    expect(card.locator(".order-tracker li.current")).to_contain_text("Being prepared")
    expect(card.locator(".order-tracker li.done")).to_have_count(2)  # placed, accepted
    assert next(o for o in call("GET", "/api/orders", token=token(STUDENT)) if o["id"] == order_id)["status"] == "preparing"
    # Finish the pickup order; it moves from Your orders to Order history.
    row.first.get_by_role("button", name="Mark ready").click()
    expect(vendor.get_by_text("Order marked ready")).to_be_visible()
    row.first.get_by_role("button", name="Mark collected").click()
    expect(vendor.get_by_text("Order marked collected")).to_be_visible()
    student.reload(); student.wait_for_load_state("networkidle")
    tab(student, "Your orders")
    expect(student.locator(".order-card").filter(has_text=f"Order #{order_id}")).to_have_count(0)
    tab(student, "Order history")
    expect(student.locator(".history-row").filter(has_text=f"Order #{order_id}").locator(".status-pill")).to_have_text("Collected")


def test_e2e_03_bag_holds_one_vendor_and_asks_before_switching(new_page):
    clear_cart(STUDENT)
    page = new_page()
    sign_in(page, STUDENT)
    open_vendor(page, "Kathi Junction")
    add_item(page, "Aloo Roll")
    expect(page.get_by_text("Aloo Roll added to your bag")).to_be_visible()
    page.get_by_role("button", name="← Back to marketplace").click()  # returns to the Vendors page
    open_vendor(page, "Domino's")
    page.get_by_placeholder(re.compile("Search Domino")).fill("Garlic Breadsticks")
    breadsticks = page.get_by_role("article").filter(has=page.get_by_role("heading", name="Garlic Breadsticks", exact=True))
    # Cancel: the bag keeps the Kathi Junction item.
    page.dialog_answer = False
    breadsticks.get_by_role("button", name="Add", exact=True).click()
    wait_for_dialog(page, 1)
    expect(page.get_by_role("button", name="Shopping bag")).to_have_text("1")
    assert page.dialog_messages and "Kathi Junction" in page.dialog_messages[-1] and "clear your existing cart" in page.dialog_messages[-1]
    assert [i["name"] for i in call("GET", "/api/cart", token=token(STUDENT))["items"]] == ["Aloo Roll"]
    # Accept: the bag is cleared and restarted with Domino's.
    page.dialog_answer = True
    breadsticks.get_by_role("button", name="Add", exact=True).click()
    expect(page.get_by_text("Cart started with Domino's")).to_be_visible()
    cart = call("GET", "/api/cart", token=token(STUDENT))
    assert cart["vendor_name"] == "Domino's" and [i["name"] for i in cart["items"]] == ["Garlic Breadsticks"]
    clear_cart(STUDENT)


def test_e2e_04_admin_approves_a_pending_vendor(new_page):
    page = new_page()
    sign_in(page, ADMIN)
    tab(page, "Applications")
    card = page.locator(".application-card").filter(has_text="Greenox")
    expect(card).to_be_visible()
    card.get_by_role("button", name=re.compile("^Approve")).click()
    expect(page.get_by_text("Application approved")).to_be_visible()
    greenox = next(v for v in call("GET", "/api/vendors") if v["business_name"] == "Greenox")
    history = call("GET", "/api/admin/history", token=token(ADMIN))
    assert any(h["vendor_id"] == greenox["id"] and h["decision"] == "approved" for h in history)


def test_e2e_05_vendor_marks_whole_menu_out_of_stock(new_page):
    page = new_page()
    sign_in(page, DOMINOS)
    tab(page, "Your food")
    bar = page.locator(".bulk-availability")
    expect(bar).to_contain_text("121 of 121 items in stock")
    bar.get_by_role("button", name="Mark all out of stock").click()
    expect(bar).to_contain_text("0 of 121 items in stock")
    in_stock = call("GET", "/api/products?vendor_id=4&available_only=true&limit=100")
    assert in_stock["total"] == 0
    bar.get_by_role("button", name="Mark all in stock").click()
    expect(bar).to_contain_text("121 of 121 items in stock")


def test_e2e_06_student_favourites(new_page):
    page = new_page()
    sign_in(page, STUDENT)
    open_vendor(page, "Kathi Junction")
    card = page.get_by_role("article").filter(has=page.get_by_role("heading", name="Veg Biryani", exact=True))
    heart = card.get_by_role("button", name="Save food to favourites")
    card_box, heart_box = card.bounding_box(), heart.bounding_box()
    # Regression check: the heart must be drawn on its own card (it used to float to one shared spot).
    assert card_box["x"] <= heart_box["x"] and heart_box["x"] + heart_box["width"] <= card_box["x"] + card_box["width"]
    assert card_box["y"] <= heart_box["y"] and heart_box["y"] + heart_box["height"] <= card_box["y"] + card_box["height"]
    heart.click()
    expect(page.get_by_text("Saved to your favourites")).to_be_visible()
    tab(page, "Favourites")
    expect(page.get_by_role("heading", name="Your favourites")).to_be_visible()
    expect(page.get_by_role("heading", name="Veg Biryani", exact=True)).to_be_visible()
    expect(page.get_by_text("1 saved item")).to_be_visible()


def test_e2e_07_student_sees_no_admin_or_vendor_tabs(new_page):
    page = new_page()
    sign_in(page, STUDENT)
    tabs = page.locator(".workspace-tabs")
    expect(tabs).to_be_visible()
    for forbidden in ("Applications", "Food listings", "Students", "Approval history", "Your food"):
        expect(tabs.get_by_role("button", name=forbidden, exact=True)).to_have_count(0)


def test_e2e_08_visitor_pages_and_join_button(new_page):
    page = new_page()
    # Visitors get "Join the marketplace" right beside "Explore food"; the old boxed section is gone from the home page.
    actions = page.locator(".hero-actions")
    expect(actions.get_by_role("button")).to_have_count(2)
    expect(actions.get_by_role("button").nth(0)).to_have_accessible_name("Explore food")
    expect(actions.get_by_role("button").nth(1)).to_have_accessible_name("Join the marketplace")  # filled copy is aria-hidden
    expect(page.locator(".vendor-cta-top")).to_have_count(0)
    nav = page.get_by_role("navigation")
    nav.get_by_role("button", name="Discover", exact=True).click()
    expect(page.get_by_role("heading", name="Discover food around BMU.", level=1)).to_be_visible()
    expect(page.locator(".vendor-section")).to_have_count(0)
    nav.get_by_role("button", name="Vendors", exact=True).click()
    expect(page.get_by_role("heading", name="The food spots around BMU.", level=1)).to_be_visible()
    expect(page.locator(".vendor-tile").first).to_be_visible()
    nav.get_by_role("button", name="Menu", exact=True).click()
    expect(page.get_by_role("heading", name="Find your next favourite bite.")).to_be_visible()
    expect(page.locator(".product-card").first).to_be_visible()
    expect(page.locator(".product-card .dish-photo, .product-card .name-tile").first).to_be_visible()   # dish photo, or the name tile when there is none
    credit = page.locator(".product-card .photo-credit").first
    if credit.count(): expect(credit).to_contain_text("Unsplash")                                        # stock photos are always credited
    nav.get_by_role("button", name="Marketplace", exact=True).click()
    expect(page.locator(".category-section, .vendor-section, .market-section")).to_have_count(0)  # each has its own page
    expect(page.locator("header.topbar")).to_have_css("position", "sticky")
    actions.get_by_role("button", name="Join the marketplace").click()
    expect(page.get_by_text("GROW WITH SUPR")).to_be_visible()


def test_e2e_09_door_intro_plays_on_every_load(new_page):
    page = new_page(intro=True)
    intro = page.locator(".door-intro")
    expect(intro).to_be_visible()
    expect(intro.get_by_text("supr.")).to_be_visible()
    expect(intro.locator(".door")).to_have_count(2)
    expect(intro).to_have_count(0, timeout=5_000)          # doors open and the overlay removes itself
    expect(page.locator(".hero-actions")).to_be_visible()
    page.reload()
    expect(page.locator(".door-intro")).to_be_visible()   # plays again after a refresh
    expect(page.locator(".door-intro")).to_have_count(0, timeout=5_000)


def test_e2e_10_language_switch(new_page):
    page = new_page()
    nav = page.get_by_role("navigation")
    switch = page.locator(".lang-btn")
    expect(switch).to_have_text("हिंदी")
    switch.click()
    expect(nav.get_by_role("button").first).to_have_text("मार्केटप्लेस")
    expect(page.locator(".hero-actions .primary-btn")).to_contain_text("खाना देखें")
    expect(page.locator("html")).to_have_attribute("lang", "hi")
    nav.get_by_role("button").nth(1).click()                       # Menu, opened while in Hindi
    expect(page.locator(".market-section h2")).to_have_text("अपना अगला पसंदीदा व्यंजन खोजें।")
    page.reload(); page.locator(".door-intro").wait_for(state="detached", timeout=15_000)
    expect(page.locator("html")).to_have_attribute("lang", "hi")   # choice is remembered
    page.locator(".lang-btn").click()
    expect(nav.get_by_role("button").first).to_have_text("Marketplace")
    expect(page.locator(".lang-btn")).to_have_text("हिंदी")


def test_e2e_11_tech_page_is_separate_from_food(new_page):
    page = new_page()
    nav = page.get_by_role("navigation")
    nav.get_by_role("button", name="Menu", exact=True).click()
    expect(page.locator(".category-chips .chip", has_text="Laptop Repair")).to_have_count(0)   # food menu stays food
    nav.get_by_role("button", name="Tech", exact=True).click()
    expect(page.get_by_role("heading", name="Laptop and phone help near BMU.", level=1)).to_be_visible()
    expect(page.locator(".product-card").first).to_be_visible()
    expect(page.locator(".product-card .dietary-tag")).to_have_count(0)                        # no veg / non-veg labels
    expect(page.locator(".product-card .add-btn").first).to_contain_text("Details")             # listed shops: contact, not order
    page.locator(".category-chips").get_by_role("button", name="Phone Repair").click()
    expect(page.locator(".product-card .service-tag").first).to_have_text("Phone Repair")
    expect(page.locator(".listed-tile")).to_have_count(5)


def test_e2e_12_sign_out_from_account_menu(new_page):
    page = new_page()
    sign_in(page, "student@supr.bmu.edu.in")
    expect(page.locator(".workspace-tabs")).to_be_visible()
    page.locator(".account-btn").click()
    page.locator(".profile-dropdown").get_by_role("button", name="Sign out").click()
    expect(page.locator(".workspace-tabs")).to_have_count(0)
    expect(page.get_by_role("button", name="Account", exact=True)).to_be_visible()


def test_e2e_13_account_menu_when_signed_out(new_page):
    page = new_page()
    page.get_by_role("button", name="Account", exact=True).click()
    menu = page.locator(".profile-dropdown")
    expect(menu.get_by_role("button", name="Sign in")).to_be_visible()
    expect(menu.get_by_role("button", name="Join the marketplace")).to_be_visible()
    expect(menu.get_by_role("button", name="Sign out")).to_have_count(0)
    menu.get_by_role("button", name="Sign in").click()
    expect(page.get_by_label("BMU email")).to_be_visible()


def _change_password_from_profile(page, current, new):
    page.locator(".account-btn").click()
    page.locator(".profile-dropdown").get_by_role("button", name="My profile").click()
    form = page.locator(".password-card")
    expect(form.get_by_role("heading", name="Reset password")).to_be_visible()
    form.get_by_label("Current password").fill(current)
    form.get_by_label("New password", exact=True).fill(new)
    form.get_by_label("Confirm new password").fill(new)
    form.get_by_role("button", name="Reset password").click()


def test_e2e_14_student_and_vendor_can_reset_their_password(new_page):
    for email, role_text in ((STUDENT, "BMU STUDENT ACCOUNT"), (KATHI, "VENDOR ACCOUNT")):
        page = new_page()
        sign_in(page, email)
        _change_password_from_profile(page, "Demo@12345", "Changed-pass-123")
        expect(page.get_by_text("Password changed")).to_be_visible()
        expect(page.get_by_text(role_text)).to_be_visible()
        _change_password_from_profile(page, "Changed-pass-123", "Demo@12345")   # restore for the other tests
        expect(page.get_by_text("Password changed").first).to_be_visible()


def test_e2e_15_reset_password_rejects_wrong_current_password(new_page):
    page = new_page()
    sign_in(page, STUDENT)
    _change_password_from_profile(page, "not-my-password", "Changed-pass-123")
    expect(page.get_by_role("alert").filter(has_text="Current password is incorrect")).to_be_visible()


def test_e2e_16_vendor_can_select_all_campus_places(new_page):
    page = new_page()
    sign_in(page, DOMINOS)
    box = page.locator(".vendor-delivery-card")
    all_places = box.get_by_label("All campus places")
    expect(all_places).to_be_visible()
    all_places.click()                      # the box updates once the server has saved
    expect(all_places).to_be_checked()
    options = box.locator(".delivery-check-option:not(.delivery-check-all) input")
    expect(options.first).to_be_checked()
    for i in range(options.count()): expect(options.nth(i)).to_be_checked()
    assert len(call("GET", "/api/vendor/delivery-points", token=token(DOMINOS))["delivery_points"]) == options.count()
    all_places.click()
    expect(all_places).not_to_be_checked()
    for i in range(options.count()): expect(options.nth(i)).not_to_be_checked()


def test_e2e_17_admin_can_reset_their_password(new_page):
    page = new_page()
    sign_in(page, ADMIN)
    _change_password_from_profile(page, "Demo@12345", "Changed-pass-123")
    expect(page.get_by_text("Password changed")).to_be_visible()
    expect(page.get_by_text("UNIVERSITY ADMIN ACCOUNT")).to_be_visible()
    _change_password_from_profile(page, "Changed-pass-123", "Demo@12345")
    expect(page.get_by_text("Password changed").first).to_be_visible()


def test_e2e_18_admin_can_show_the_temporary_password_and_browser_does_not_autofill(new_page):
    page = new_page()
    sign_in(page, ADMIN)
    tab(page, "Students")
    form = page.locator(".student-create-card")
    field = form.get_by_placeholder("At least 10 characters")
    field.fill("Temp-pass-12345")
    expect(field).to_have_attribute("type", "password")
    form.get_by_role("button", name="Show password").click()
    expect(field).to_have_attribute("type", "text")
    expect(field).to_have_value("Temp-pass-12345")
    form.get_by_role("button", name="Hide password").click()
    expect(field).to_have_attribute("type", "password")
    expect(form.get_by_label("BMU email")).to_have_value("")      # the admin's own login is not pre-filled


def _login_status(email, password):
    try:
        call("POST", "/api/auth/login", {"email": email, "password": password}); return 200
    except Exception as exc:
        return getattr(exc, "code", 0)


def test_e2e_19_admin_can_reset_a_students_and_a_vendors_password(new_page):
    page = new_page()
    sign_in(page, ADMIN)
    # student
    tab(page, "Students")
    row = page.locator(".student-account-row").filter(has_text=STUDENT)
    row.get_by_role("button", name="Reset password").click()
    row.get_by_placeholder("At least 10 characters").fill("Admin-set-pass-1")
    row.get_by_role("button", name="Save new password").click()
    expect(page.get_by_text("Password changed for").first).to_be_visible()
    assert _login_status(STUDENT, "Demo@12345") == 401
    assert _login_status(STUDENT, "Admin-set-pass-1") == 200
    # vendor
    tab(page, "Applications")
    card = page.locator(".application-card").filter(has_text="Kathi Junction")
    card.get_by_role("button", name="Reset password").click()
    card.get_by_placeholder("At least 10 characters").fill("Admin-set-pass-2")
    card.get_by_role("button", name="Save new password").click()
    expect(page.get_by_text("Password changed for Kathi Junction")).to_be_visible()
    assert _login_status(KATHI, "Demo@12345") == 401
    assert _login_status(KATHI, "Admin-set-pass-2") == 200
    # restore the demo passwords through the same API so later tests still sign in
    admin = token(ADMIN)
    users = {u["email"]: u["id"] for u in call("GET", "/api/admin/students", token=admin)}
    vendor_user = next(a["user_id"] for a in call("GET", "/api/admin/applications", token=admin) if a["email"] == KATHI)
    for uid in (users[STUDENT], vendor_user):
        call("POST", f"/api/admin/users/{uid}/password", {"new_password": "Demo@12345"}, token=admin)


def test_e2e_20_emptied_bag_lets_you_start_with_another_vendor_without_a_prompt(new_page):
    clear_cart(STUDENT)
    page = new_page()
    sign_in(page, STUDENT)
    open_vendor(page, "Kathi Junction")
    add_item(page, "Aloo Roll")
    expect(page.get_by_role("button", name="Shopping bag")).to_have_text("1")
    page.get_by_role("button", name="Shopping bag").click()
    page.get_by_role("button", name="−").click()                      # take the only item out of the bag
    expect(page.get_by_role("button", name="Shopping bag")).to_have_text("0")
    page.locator(".cart-panel .icon-btn").first.click()
    assert call("GET", "/api/cart", token=token(STUDENT))["vendor_id"] is None
    page.get_by_role("button", name="← Back to marketplace").click()
    open_vendor(page, "Domino's")
    page.get_by_placeholder(re.compile("Search Domino")).fill("Garlic Breadsticks")
    n = len(page.dialog_messages)
    page.get_by_role("article").filter(has=page.get_by_role("heading", name="Garlic Breadsticks", exact=True)).get_by_role("button", name="Add", exact=True).click()
    expect(page.get_by_text("Garlic Breadsticks added to your bag")).to_be_visible()
    assert len(page.dialog_messages) == n, "no 'clear your cart' prompt should appear for an empty bag"
    clear_cart(STUDENT)


def test_e2e_21_admin_sees_a_readable_approval_history_per_vendor(new_page):
    page = new_page()
    sign_in(page, ADMIN)
    tab(page, "Approval history")
    history = page.locator(".admin-history")
    expect(history.get_by_text("Approved").first).to_be_visible()
    expect(history.get_by_text("By BMU Marketplace Admin").first).to_be_visible()
    expect(history.locator(".history-vendor").first).to_be_visible()                 # vendor names, not "Vendor #4"
    expect(history.get_by_text(re.compile(r"^Vendor #\d+$"))).to_have_count(0)
    history.get_by_label("Vendor").select_option(label="Kathi Junction")
    names = history.locator(".history-vendor")
    expect(names).to_have_count(0)                                                   # filtered: the vendor name is not repeated on every row
    expect(history.locator(".history-item").first).to_be_visible()
    # per-vendor timeline on the vendor card
    tab(page, "Applications")
    card = page.locator(".application-card").filter(has_text="Kathi Junction")
    card.get_by_role("button", name="Approval history").click()
    expect(card.locator(".vendor-history-panel .history-item").first).to_be_visible()
    expect(card.locator(".vendor-history-panel")).to_contain_text("Application submitted")
    card.get_by_role("button", name="Hide history").click()
    expect(card.locator(".vendor-history-panel")).to_have_count(0)


def test_e2e_22_clear_bag_button_empties_the_bag(new_page):
    clear_cart(STUDENT)
    page = new_page()
    sign_in(page, STUDENT)
    open_vendor(page, "Kathi Junction")
    add_item(page, "Aloo Roll")
    expect(page.get_by_role("button", name="Shopping bag")).to_have_text("1")
    page.get_by_role("button", name="Shopping bag").click()
    page.dialog_answer = False                                         # cancel keeps the bag
    page.get_by_role("button", name="Clear bag").click()
    wait_for_dialog(page, 1)
    assert len(call("GET", "/api/cart", token=token(STUDENT))["items"]) == 1
    page.dialog_answer = True
    page.get_by_role("button", name="Clear bag").click()
    expect(page.get_by_text("Your bag is waiting for a good find.")).to_be_visible()
    assert call("GET", "/api/cart", token=token(STUDENT))["items"] == []
    assert call("GET", "/api/cart", token=token(STUDENT))["vendor_id"] is None


def test_e2e_23_student_signs_up_with_a_name_yearcourse_bmu_address(new_page):
    page = new_page()
    page.get_by_role("button", name="Account", exact=True).click()
    page.locator(".profile-dropdown").get_by_role("button", name="Create student account").click()
    dialog = page.locator(".form-modal")
    expect(dialog.get_by_role("heading", name="Join your neighbourhood.")).to_be_visible()
    expect(dialog.get_by_text("name.yearcourse@bmu.edu.in, for example dhruv.24cse@bmu.edu.in")).to_be_visible()
    dialog.get_by_label("Your name").fill("Dhruv Test")
    dialog.get_by_label("Password").fill("Strong-pass-123")
    # an address that does not follow the rule is stopped by the form itself
    dialog.get_by_label("BMU email").fill("dhruv@gmail.com")
    dialog.get_by_role("button", name="Create student account").click()
    expect(dialog).to_be_visible()
    assert page.locator(".workspace-tabs").count() == 0
    dialog.get_by_label("BMU email").fill("dhruv.24cse@bmu.edu.in")
    dialog.get_by_role("button", name="Create student account").click()
    expect(page.locator(".workspace-tabs")).to_contain_text("Hi, Dhruv")
    assert call("POST", "/api/auth/login", {"email": "dhruv.24cse@bmu.edu.in", "password": "Strong-pass-123"})["user"]["role"] == "student"
    # and the sign-in screen can switch to sign-up and back
    page.locator(".account-btn").click()
    page.locator(".profile-dropdown").get_by_role("button", name="Sign out").click()
    page.get_by_role("button", name="Account", exact=True).click()
    page.locator(".profile-dropdown").get_by_role("button", name="Sign in").click()
    page.locator(".form-modal").get_by_role("button", name="Create a student account").click()
    expect(page.locator(".form-modal").get_by_role("heading", name="Join your neighbourhood.")).to_be_visible()
    page.locator(".form-modal").get_by_role("button", name="Sign in", exact=True).click()
    expect(page.locator(".form-modal").get_by_role("heading", name="Good to see you.")).to_be_visible()


def test_e2e_24_new_vendor_appears_for_the_admin_before_it_applies(new_page):
    call("POST", "/api/auth/register", {"name": "Brand New Bites", "email": "brandnew@supr.test", "password": "Strong-pass-123", "role": "vendor"})
    page = new_page()
    sign_in(page, ADMIN)
    tab(page, "Applications")
    card = page.locator(".application-card").filter(has_text="Brand New Bites")
    expect(card).to_be_visible()
    expect(card).to_contain_text("not applied yet")
    expect(card).to_contain_text("nothing to approve")
    expect(card.get_by_role("button", name=re.compile("^Approve"))).to_have_count(0)
    card.get_by_role("button", name="Approval history").click()
    expect(card.locator(".vendor-history-panel")).to_contain_text("Vendor registered")
    page.locator(".account-btn").click()
    page.locator(".profile-dropdown").get_by_role("button", name=re.compile("Notifications")).click()
    expect(page.get_by_text(re.compile("New vendor registered: Brand New Bites"))).to_be_visible()


def test_e2e_25_admin_food_listings_are_food_only_and_tech_has_its_own_page(new_page):
    page = new_page()
    sign_in(page, ADMIN)
    tab(page, "Food listings")
    expect(page.get_by_role("heading", name="Food listings", level=1)).to_be_visible()
    rows = page.locator(".record-row")
    expect(rows.first).to_be_visible()
    food_text = " ".join(rows.all_inner_texts())
    for shop in ("Hi-Tech Computer", "Make My Lappy", "Shivam Mobile", "Vislor", "AJ Mobile"):
        assert shop not in food_text, f"{shop} should be on the Tech listings page"
    assert "Laptop Repair" not in food_text and "Phone Repair" not in food_text
    assert page.get_by_role("button", name="Add menu item").is_visible()

    tab(page, "Tech listings")
    expect(page.get_by_role("heading", name="Laptop and phone listings", level=1)).to_be_visible()
    rows = page.locator(".record-row")
    expect(rows.filter(has_text="Make My Lappy").first).to_be_visible()      # waits for the tech rows to arrive
    tech_text = " ".join(rows.all_inner_texts())
    assert "Make My Lappy" in tech_text and "Kathi Junction" not in tech_text and "Domino" not in tech_text and "Lazeez" not in tech_text
    # adding a service offers only laptop and phone categories and listed shops
    page.get_by_role("button", name="Add service").click()
    form = page.locator(".form-modal")
    expect(form.get_by_label("Category").locator("option")).to_have_count(5)      # "Choose category" plus the four tech categories
    categories = form.get_by_label("Category").locator("option").all_inner_texts()
    assert set(categories) - {"Choose category"} == {"Laptop Repair", "Laptops and Accessories", "Phone Repair", "Phones and Accessories"}
    expect(form.get_by_label("Vendor").locator("option").nth(1)).to_be_attached()
    vendors = form.get_by_label("Vendor").locator("option").all_inner_texts()
    assert vendors and all("listed" in v or v == "Choose vendor" for v in vendors)
    assert not any("Kathi" in v or "Domino" in v for v in vendors)
    page.locator(".form-modal .modal-close").click()
    # and the food form offers only food
    tab(page, "Food listings")
    page.get_by_role("button", name="Add menu item").click()
    form = page.locator(".form-modal")
    expect(form.get_by_label("Food category").locator("option").nth(1)).to_be_attached()
    foods = form.get_by_label("Food category").locator("option").all_inner_texts()
    assert foods and not any("Laptop" in c or "Phone" in c for c in foods)
    vendors = form.get_by_label("Vendor").locator("option").all_inner_texts()
    assert not any("listed" in v for v in vendors)
