"""Shop photos and logos shown on the landing page, Vendors and Tech pages, and each shop's page.

Files live in frontend/public/vendors/. Sources:
  kolkatas-lazeez.png       storefront photo supplied by the project owner (2026-11-17)
  dominos-logo.png          Domino's logo supplied by the project owner; dark screenshot edges trimmed
  kathi-junction-logo.png   logo badge cropped from the Kathi Junction menu photo supplied earlier (docs/menu-sources)
  hi-tech-computer-logo.png from the shop's own website, https://www.hitech-computer.com/ (share image)
  make-my-lappy-logo.png    from the shop's own website, https://makemylappy.net/ (site icon)
Shops without an official image (Greenox: site blocks automated access; Shivam, Vislor, AJ Mobile: no own website)
keep the name tile.

Run from backend/: python -m app.vendor_images   (applies the paths to an existing database)
"""
from sqlalchemy import select

from .database import SessionLocal
from .models import Vendor

VENDOR_IMAGES = {
    "Kolkata's Lazeez": "/vendors/kolkatas-lazeez.png",
    "Domino's": "/vendors/dominos-logo.png",
    "Kathi Junction": "/vendors/kathi-junction-logo.png",
    "Hi-Tech Computer": "/vendors/hi-tech-computer-logo.png",
    "Make My Lappy": "/vendors/make-my-lappy-logo.png",
}


def apply_vendor_images(db):
    changed = 0
    for v in db.scalars(select(Vendor).where(Vendor.business_name.in_(VENDOR_IMAGES))):
        if v.image_url != VENDOR_IMAGES[v.business_name]:
            v.image_url = VENDOR_IMAGES[v.business_name]; changed += 1
    return changed


if __name__ == "__main__":
    db = SessionLocal(); n = apply_vendor_images(db); db.commit(); db.close()
    print(f"Updated {n} shop image(s).")
