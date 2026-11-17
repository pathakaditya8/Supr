import os, sys
from pathlib import Path
import pytest
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).parent))
from stack import Stack, WEB, PASSWORD, call, token  # noqa: E402

# Edge ships with Windows; set E2E_BROWSER_CHANNEL=chrome (or "" for Playwright's bundled Chromium) elsewhere.
CHANNEL = os.environ.get("E2E_BROWSER_CHANNEL", "msedge")
HEADED = os.environ.get("E2E_HEADED") == "1"


@pytest.fixture(scope="session")
def stack():
    s = Stack().start()
    yield s
    s.stop()


@pytest.fixture(scope="session")
def browser(stack):
    with sync_playwright() as p:
        b = p.chromium.launch(channel=CHANNEL or None, headless=not HEADED)
        yield b
        b.close()


@pytest.fixture
def new_page(browser):
    """Factory: each call is a separate browser context (own localStorage), like a different person's device."""
    contexts = []
    def make(intro=False):
        ctx = browser.new_context(viewport={"width": 1280, "height": 900})
        ctx.set_default_timeout(15_000)
        contexts.append(ctx)
        page = ctx.new_page()
        # confirm() prompts: accepted by default; a test can set page.dialog_answer = False to cancel.
        page.dialog_answer = True
        page.dialog_messages = []
        def on_dialog(d, page=page):
            page.dialog_messages.append(d.message)
            d.accept() if page.dialog_answer else d.dismiss()
        page.on("dialog", on_dialog)
        # The door animation lasts ~2 s, so a test about it must not wait for slow third-party fonts/images ("load").
        page.goto(WEB, timeout=90_000, wait_until="domcontentloaded" if intro else "load")
        if not intro:  # let the door animation finish before the test starts clicking
            page.locator(".door-intro").wait_for(state="detached", timeout=15_000)
            page.wait_for_load_state("networkidle")
        return page
    yield make
    for c in contexts: c.close()


def sign_in(page, email, password=PASSWORD):
    page.get_by_role("button", name="Account", exact=True).click()
    page.locator(".profile-dropdown").get_by_role("button", name="Sign in").click()  # account menu -> sign in
    page.get_by_label("BMU email").fill(email)
    page.get_by_label("Password").fill(password)
    page.get_by_role("button", name="Sign in", exact=True).click()


def tab(page, name):
    page.locator(".workspace-tabs").get_by_role("button", name=name, exact=True).click()


def clear_cart(email):
    call("DELETE", "/api/cart", token=token(email))
