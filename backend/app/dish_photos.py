"""Illustrative Unsplash photos per dish type and diet (e.g. "kathi roll | vegetarian").

Dishes are grouped by type with the rules below, so about 40 photos cover the whole menu instead of one per dish.
A vegetarian item only ever gets a vegetarian photo. Photos are hotlinked from Unsplash and credited to the
photographer, as Unsplash requires. The shop's own photo (if any) always takes priority over these.

Run from backend/:
    python -m app.dish_photos --dry-run   # list the photos needed and their searches
    python -m app.dish_photos             # fetch missing photos (Unsplash demo apps: 50 requests/hour; resumable)
"""
import argparse, os, re, sys
from pathlib import Path
import httpx
from sqlalchemy import select
from .database import SessionLocal
from .models import DishPhoto, Product, Category

VEG, NONVEG, ANY = "vegetarian", "non_vegetarian", "any"

# (type, regex over "name | section | category", {diet: unsplash search}) — first match wins.
RULES = [
    ("kathi-roll",    r"\broll\b",                                       {VEG: "paneer kathi roll", NONVEG: "chicken kathi roll"}),
    ("noodles",       r"noodle|chinese|manchurian|chow",                 {VEG: "veg hakka noodles", NONVEG: "chicken noodles"}),
    ("fried-rice",    r"\brice\b",                                       {VEG: "veg fried rice", NONVEG: "chicken fried rice"}),
    ("fries",         r"fries",                                          {ANY: "french fries"}),
    ("momos",         r"momo",                                           {ANY: "momos dumplings"}),
    ("potato",       r"potato|aloo jeera|jeera",                         {ANY: "spicy potato fries chilli"}),
    ("biryani",       r"biryani",                                        {VEG: "veg biryani rice", NONVEG: "chicken biryani"}),
    ("tacos",         r"taco|parcel",                                    {VEG: "vegetarian tacos", NONVEG: "chicken tacos"}),
    ("garlic-bread",  r"garlic bread|breadstick|stuffed gb|\bgb\b",      {ANY: "garlic bread"}),
    ("lava-cake",     r"lava cake|choco|dessert",                        {ANY: "chocolate lava cake"}),
    ("chai",          r"\btea\b",                                        {ANY: "masala chai tea cup"}),
    ("cola",          r"coca|cola|sprite|soft drink|coke",               {ANY: "cold drink soda glass"}),
    ("water",         r"water",                                          {ANY: "bottled water"}),
    ("juice",         r"juice|natural|alphonso|mango",                   {ANY: "mango juice glass"}),
    ("naan",          r"naan|kulcha",                                    {ANY: "naan bread"}),
    ("roti",          r"roti|paratha|pratha",                            {ANY: "indian flatbread roti"}),
    ("chaap",         r"chaap",                                          {ANY: "soya chaap tandoori"}),
    ("tikka",         r"tikka|kabab|kebab|seekh|tandoori",               {VEG: "paneer tikka", NONVEG: "chicken tikka"}),
    ("paneer-curry",  r"paneer",                                         {ANY: "paneer curry"}),
    ("dal",           r"\bdal\b|dal ",                                   {ANY: "dal makhani"}),
    ("egg-curry",     r"egg",                                            {ANY: "egg curry"}),
    ("mutton",        r"mutton",                                         {ANY: "mutton curry"}),
    ("chicken-curry", r"chicken|chilli|kadhai|tawa",                     {ANY: "butter chicken curry"}),
    ("veg-curry",     r"mix veg|raita|curry",                            {ANY: "indian vegetable curry"}),
    ("pizza",         r"pizza|margherita|farmhouse|peppy|paneer spice|veggie|cheese|corn|green wave|fiesta|pepperoni|bbq|deluxe|extravaganza|golden|lava|volcano|burst|mania|feast|big big|sausage|achari|onion",
                                                                         {VEG: "vegetable pizza", NONVEG: "pepperoni chicken pizza"}),
    ("laptop-repair", r"laptop|motherboard|macbook|data recovery|desktop|computer|os install|printer|ups|diagnosis|screen|keyboard|battery|hinge|boot|virus", {ANY: "laptop repair technician"}),
    ("laptop",        r"refurbished|laptop|accessor",                    {ANY: "laptop on desk"}),
    ("phone-repair",  r"phone|mobile|iphone|display",                    {ANY: "smartphone screen repair"}),
]
PIZZA_SECTIONS = re.compile(r"pizza|cheese burst|cheese lava|cheese volcano|chicken feast|big big|2in1|no onion|^deals$")
TECH_CATEGORIES = {"Laptop Repair", "Laptops and Accessories", "Phone Repair", "Phones and Accessories"}


def diet_of(value):
    return VEG if value in ("vegetarian", "vegan") else NONVEG if value == "non_vegetarian" else ANY


def dish_key(name, section, category, dietary):
    """Return "type|diet" for a product, or None if no rule matches."""
    d0 = diet_of(dietary)
    if PIZZA_SECTIONS.search(section.lower()):                      # Domino's pizza sections: always a pizza
        d = d0 if d0 != ANY else VEG
        return f"pizza|{d}", "vegetable pizza" if d == VEG else "pepperoni chicken pizza"
    text = f"{name} | {section} | {category}".lower()
    if category == "Phone Repair" or category == "Phones and Accessories":
        text = "phone " + text
    elif category in ("Laptop Repair", "Laptops and Accessories") and "refurbished" not in text:
        text = "laptop " + text
    for kind, pattern, searches in RULES:
        if re.search(pattern, text):
            d = diet_of(dietary)
            if category in TECH_CATEGORIES or ANY in searches: d = ANY
            elif d == ANY: d = VEG if VEG in searches else NONVEG
            if d not in searches: d = VEG if VEG in searches else next(iter(searches))
            return f"{kind}|{d}", searches[d]
    return None, None


def needed(db):
    """{key: search query} for every published product, with how many products each photo covers."""
    cats = {c.id: c.name for c in db.scalars(select(Category))}
    found, count = {}, {}
    for p in db.scalars(select(Product).where(Product.menu_status == "published")):
        key, query = dish_key(p.name, p.menu_section or "", cats.get(p.category_id, ""), p.dietary)
        if key: found[key] = query; count[key] = count.get(key, 0) + 1
    return found, count


def access_key():
    key = os.environ.get("UNSPLASH_ACCESS_KEY", "").strip()
    env = Path(__file__).resolve().parents[1] / ".env"
    if not key and env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if line.startswith("UNSPLASH_ACCESS_KEY="): key = line.split("=", 1)[1].strip().strip('"').strip("'")
    return key


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true"); ap.add_argument("--redo", action="append", default=[], metavar="KEY", help='replace one photo, e.g. "pizza|vegetarian"')
    args = ap.parse_args()
    db = SessionLocal(); found, count = needed(db)
    have = {x.key: x for x in db.scalars(select(DishPhoto))}
    for k in args.redo:
        if k in have and not args.dry_run: db.delete(have.pop(k)); db.commit()
    todo = sorted((k for k in found if k not in have), key=lambda k: -count[k])      # biggest groups first
    print(f"{len(found)} dish photos cover {sum(count.values())} items; {len(have)} already saved, {len(todo)} to fetch.")
    if args.dry_run:
        for k in todo: print(f"  {k:<30} {count[k]:>3} items  search '{found[k]}'")
        return
    key = access_key()
    if not key: sys.exit("No UNSPLASH_ACCESS_KEY found in backend/.env.")
    used = {x.photo_page_url for x in db.scalars(select(DishPhoto))}
    done = 0
    with httpx.Client(base_url="https://api.unsplash.com", headers={"Authorization": f"Client-ID {key}", "Accept-Version": "v1"}, timeout=20) as api:
        for k in todo:
            r = api.get("/search/photos", params={"query": found[k], "per_page": 15, "orientation": "landscape", "content_filter": "high"})
            if r.status_code == 401: sys.exit("Unsplash rejected the key (401).")
            if r.status_code == 403: print("Hourly Unsplash limit reached; run again later to continue."); break
            r.raise_for_status()
            photo = next((p for p in r.json()["results"] if p["links"]["html"] not in used), None)
            if not photo: print(f"  {k}: no new photo for '{found[k]}', skipped"); continue
            api.get(photo["links"]["download_location"].replace("https://api.unsplash.com", ""))   # Unsplash API guideline
            row = DishPhoto(key=k, query=found[k], source="Unsplash", image_url=photo["urls"]["raw"] + "&w=800&h=600&fit=crop&q=75",
                            photographer=photo["user"]["name"], photographer_url=photo["user"]["links"]["html"], photo_page_url=photo["links"]["html"])
            db.add(row); db.commit(); used.add(row.photo_page_url); done += 1
            print(f"  {k:<28} ({count[k]} items) photo by {row.photographer}")
            if int(r.headers.get("X-Ratelimit-Remaining", "50")) < 3: print("Unsplash hourly limit almost used; run again in an hour."); break
    print(f"Saved {done} photo(s). {len(todo) - done} still to do.")


if __name__ == "__main__":
    main()
