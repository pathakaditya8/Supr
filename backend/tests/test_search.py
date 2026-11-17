"""Search must treat every character the student types literally (TDD example, 2026-11-17).

SQL LIKE treats % and _ as wildcards, so before the fix a search for "%" or "_"
matched every menu item. See docs/AI_ENGINEERING.md for the red/green record.
"""
import pytest
from sqlalchemy import select

from app.database import SessionLocal
from app.models import Vendor


def approve_all_vendors():
    db = SessionLocal()
    for v in db.scalars(select(Vendor)): v.status = "approved"
    db.commit(); db.close()


def searchable_text(item):
    return " ".join([item["name"], item["description"] or "", item["category"], item["vendor_name"]]).lower()


@pytest.mark.parametrize("term", ["%", "_", "a_b", "100%", "%%"])
def test_search_treats_wildcard_characters_literally(client, term):
    approve_all_vendors()
    everything = client.get("/api/products", params={"limit": 1}).json()["total"]
    result = client.get("/api/products", params={"q": term, "limit": 100}).json()
    assert result["total"] < everything, f"searching {term!r} matched the whole menu"
    assert all(term.lower() in searchable_text(item) for item in result["items"]), f"{term!r} returned items that do not contain it"


def test_search_still_finds_ordinary_words(client):
    approve_all_vendors()
    result = client.get("/api/products", params={"q": "paneer", "limit": 100}).json()
    assert result["total"] > 0
    assert all("paneer" in searchable_text(item) for item in result["items"])
