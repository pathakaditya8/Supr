"""Pick illustrative Unsplash photos for vendor menu sections.

Items without their own photo show their section's photo, labelled as
illustrative, with the photographer credited as Unsplash requires.
Sections that mix vegetarian and non-vegetarian items get two photos, one per
diet, so a vegetarian item never shows meat.

Setup: create a free app at https://unsplash.com/oauth/applications and put
    UNSPLASH_ACCESS_KEY=<your access key>
in backend/.env (or set it as an environment variable).

Run from backend/:
    python -m app.import_unsplash_photos             # fill photos that are still missing
    python -m app.import_unsplash_photos --dry-run   # show the planned searches only
    python -m app.import_unsplash_photos --refresh   # replace every section photo
    python -m app.import_unsplash_photos --redo "Kathi Junction/Roll (Veg)"   # replace one section's photo(s)

Unsplash "demo" apps allow 50 requests per hour. Each photo uses two (a search
and the required download notice), so the script stops when the limit runs low;
run it again later and it continues with what is left.
"""
import argparse, os, sys
from pathlib import Path
import httpx
from sqlalchemy import select
from .database import SessionLocal
from .models import MenuSectionPhoto, Product, Vendor

API = "https://api.unsplash.com"
VEG, NONVEG, ANY = "vegetarian", "non_vegetarian", "any"

# Hand-written search terms. Section names alone ("Deals", "Roll (Veg)") search badly.
# Mixed veg/non-veg sections have one search per diet.
QUERIES = {
    ("Domino's", "2in1 Cheese Burst"): {VEG: "cheese corn pizza", NONVEG: "chicken cheese pizza"},
    ("Domino's", "Beverages"): "cold drink soda glass",
    ("Domino's", "Big Big Pizza"): {VEG: "large vegetable pizza", NONVEG: "large pepperoni pizza"},
    ("Domino's", "Cheese Burst Pizza"): {VEG: "paneer pizza", NONVEG: "chicken pizza slice"},
    ("Domino's", "Cheese Lava"): {VEG: "cheese pull pizza margherita", NONVEG: "chicken pizza cheese pull"},
    ("Domino's", "Cheese Volcano"): {VEG: "margherita pizza melted cheese", NONVEG: "meat pizza melted cheese"},
    ("Domino's", "Chicken Feast"): "chicken pizza",
    ("Domino's", "Deals"): "pizza party",
    ("Domino's", "Desserts"): "chocolate lava cake",
    ("Domino's", "Garlic Breads & Dips"): {VEG: "garlic bread", NONVEG: "pepperoni garlic bread"},
    ("Domino's", "Non-Veg Pizza"): "pepperoni pizza",
    ("Domino's", "Pizza Mania"): {VEG: "margherita pizza", NONVEG: "sausage pizza"},
    ("Domino's", "Tacos & Parcels"): {VEG: "vegetarian tacos", NONVEG: "chicken tacos"},
    ("Domino's", "Veg Pizza"): "vegetable pizza",
    ("Kathi Junction", "Beverages"): "masala chai tea",
    ("Kathi Junction", "Biryani"): {VEG: "veg biryani", NONVEG: "chicken biryani"},
    ("Kathi Junction", "Breads"): "naan bread",
    ("Kathi Junction", "Main Course Non Veg"): "butter chicken",
    ("Kathi Junction", "Main Course Veg"): "paneer curry",
    ("Kathi Junction", "Roll (Non Veg)"): "chicken wrap roll",
    ("Kathi Junction", "Roll (Veg)"): "paneer kathi roll",
    ("Kathi Junction", "Starters Non Veg"): "tandoori chicken",
    ("Kathi Junction", "Starters Veg"): "paneer tikka",
    ("Kolkata's Lazeez", "Chinese"): {VEG: "veg hakka noodles", NONVEG: "chicken noodles"},
    ("Kolkata's Lazeez", "French Fries"): "french fries",
    ("Kolkata's Lazeez", "Main Course (Non Veg)"): "chicken curry",
    ("Kolkata's Lazeez", "Main Course (Veg)"): "dal makhani",
    ("Kolkata's Lazeez", "Momos"): "momos dumplings",
    ("Kolkata's Lazeez", "Non Veg. Kathi Rolls"): "egg roll kolkata",
    ("Kolkata's Lazeez", "Rice"): {VEG: "veg fried rice", NONVEG: "chicken fried rice"},
    ("Kolkata's Lazeez", "Roti"): {VEG: "roti flatbread", NONVEG: "egg paratha"},
    ("Kolkata's Lazeez", "Tandoori Snacks"): {VEG: "paneer tikka skewers", NONVEG: "chicken tikka"},
    ("Kolkata's Lazeez", "Veg rolls"): "vegetable wrap",
    ("Kolkata's Lazeez", "Veg. Kathi Rolls"): "veg frankie roll",
}


def access_key():
    key = os.environ.get("UNSPLASH_ACCESS_KEY", "").strip()
    env = Path(__file__).resolve().parents[1] / ".env"
    if not key and env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            name, _, value = line.partition("=")
            if name.strip() == "UNSPLASH_ACCESS_KEY":
                key = value.strip().strip('"').strip("'")
    return key


def diet(value):
    return VEG if value in ("vegetarian", "vegan") else NONVEG if value == "non_vegetarian" else ANY


def needed_photos(db):
    """[(vendor_id, vendor_name, section, photo_diet, query)] for every section with live items.
    Mixed sections need a vegetarian and a non-vegetarian photo; other sections one photo marked "any"."""
    rows = db.execute(select(Vendor.id, Vendor.business_name, Product.menu_section, Product.dietary).join(Product, Product.vendor_id == Vendor.id)
                      .where(Product.menu_status != "removed", Product.menu_section != "")).all()
    sections = {}
    for vid, vname, sec, dietary in rows:
        sections.setdefault((vid, vname, sec), set()).add(diet(dietary))
    plan = []
    for (vid, vname, sec), diets in sorted(sections.items(), key=lambda x: (x[0][1], x[0][2])):
        q = QUERIES.get((vname, sec), f"{sec} food")
        if VEG in diets and NONVEG in diets:
            veg_q, nonveg_q = (q[VEG], q[NONVEG]) if isinstance(q, dict) else (f"vegetarian {q}", f"chicken {q}")
            plan += [(vid, vname, sec, VEG, veg_q), (vid, vname, sec, NONVEG, nonveg_q)]
        else:
            single = q if isinstance(q, str) else q[VEG if VEG in diets else NONVEG]
            plan.append((vid, vname, sec, ANY, single))
    return plan


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dry-run", action="store_true", help="print planned searches without calling Unsplash")
    parser.add_argument("--refresh", action="store_true", help="replace every section photo")
    parser.add_argument("--redo", action="append", default=[], metavar="VENDOR/SECTION", help="replace the photo(s) of one section; repeatable")
    args = parser.parse_args()
    db = SessionLocal()
    plan = needed_photos(db)
    existing = {(x.vendor_id, x.menu_section, x.dietary): x for x in db.scalars(select(MenuSectionPhoto))}
    planned_keys = {(vid, sec, d) for vid, _, sec, d, _ in plan}
    redo = {tuple(r.split("/", 1)) for r in args.redo}

    # Remove photos that no longer fit the plan (e.g. a single "any" photo in a section that now needs one per diet),
    # and photos the user asked to redo, so the wrong photo stops showing straight away.
    stale = [row for key, row in existing.items() if key not in planned_keys]
    names = {vid: vname for vid, vname, *_ in plan}
    stale += [row for (vid, sec, d), row in existing.items() if (names.get(vid), sec) in redo and row not in stale]
    if args.refresh: stale = list(existing.values())
    if stale and not args.dry_run:
        for row in stale:
            print(f"  removing photo for {names.get(row.vendor_id, row.vendor_id)} / {row.menu_section} ({row.dietary})")
            db.delete(row); existing.pop((row.vendor_id, row.menu_section, row.dietary), None)
        db.commit()

    todo = [item for item in plan if (item[0], item[2], item[3]) not in existing]
    print(f"{len(todo)} photo(s) needed.")
    if args.dry_run:
        for _, vname, sec, d, q in todo: print(f"  {vname} / {sec} [{d}]: search '{q}'")
        return
    if not todo: return
    key = access_key()
    if not key:
        sys.exit("No UNSPLASH_ACCESS_KEY found. Add it to backend/.env (see the instructions at the top of this file).")
    used = {x.photo_page_url for x in db.scalars(select(MenuSectionPhoto))}
    done = 0
    with httpx.Client(base_url=API, headers={"Authorization": f"Client-ID {key}", "Accept-Version": "v1"}, timeout=20) as api:
        for vid, vname, sec, d, query in todo:
            r = api.get("/search/photos", params={"query": query, "per_page": 15, "orientation": "landscape", "content_filter": "high"})
            if r.status_code == 401: sys.exit("Unsplash rejected the access key (401). Check UNSPLASH_ACCESS_KEY.")
            if r.status_code == 403: print("Hourly Unsplash limit reached; run again later to continue."); break
            r.raise_for_status()
            photo = next((p for p in r.json()["results"] if p["links"]["html"] not in used), None)
            if not photo:
                print(f"  {vname} / {sec} [{d}]: no new photo found for '{query}', skipped"); continue
            # Unsplash API guideline: notify the download endpoint when a photo is used.
            api.get(photo["links"]["download_location"].replace(API, ""))
            row = MenuSectionPhoto(vendor_id=vid, menu_section=sec, dietary=d, source="Unsplash", search_query=query,
                                   image_url=photo["urls"]["raw"] + "&w=800&h=500&fit=crop&q=75",  # hotlinked, as Unsplash requires
                                   photographer=photo["user"]["name"], photographer_url=photo["user"]["links"]["html"],
                                   photo_page_url=photo["links"]["html"])
            db.add(row); db.commit()
            used.add(row.photo_page_url); done += 1
            print(f"  {vname} / {sec} [{d}]: photo by {row.photographer}")
            if int(r.headers.get("X-Ratelimit-Remaining", "50")) < 3:
                print("Unsplash hourly limit almost used; run again in an hour to continue."); break
    left = len(todo) - done
    print(f"Saved {done} photo(s).{f' {left} still to do.' if left else ' Every section has its photo(s).'}")
    db.close()


if __name__ == "__main__":
    main()
