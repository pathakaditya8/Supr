"""Add the Domino's website menu to an existing database without resetting it.

Run from backend/: python -m app.import_dominos
Refuses to run if the Domino's vendor already has products, so it is safe to re-run.
"""
from sqlalchemy import func, select

from .database import SessionLocal
from .dominos_menu import DOMINOS
from .models import Category, Product, ProductVariant, Vendor

db=SessionLocal()
vendor=db.scalar(select(Vendor).where(Vendor.business_name=="Domino's"))
if vendor is None: raise SystemExit("No Domino's vendor found.")
existing=db.scalar(select(func.count(Product.id)).where(Product.vendor_id==vendor.id))
if existing: raise SystemExit(f"Domino's already has {existing} products; nothing imported.")
categories={c.name:c for c in db.scalars(select(Category))}
variants=0
for section,name,category,dietary,prices,portion,review,description in DOMINOS:
    text=" ".join(x for x in (description,f"Manual review: {review}" if review else "") if x)
    product=Product(vendor_id=vendor.id,category_id=categories[category].id,name=name,description=text,price=min(float(p) for _,p in prices),stock=0,available=False,image_url="",dietary=dietary,portion=portion,prep_time_minutes=None,menu_section=section,menu_status="published")
    db.add(product); db.flush()
    if len(prices)>1:
        for label,price in prices:
            db.add(ProductVariant(product_id=product.id,name=label,price=price,dietary=dietary,preparation="",portion=label,available=False)); variants+=1
vendor.description="Pizzas, garlic breads, tacos, desserts and drinks."
vendor.delivery_terms_note="Delivery terms, minimum order and serving outlet are not stated on the website menu."
db.commit(); db.close()
print(f"Imported {len(DOMINOS)} Domino's products with {variants} size/crust variants (stock 0, ordering off until the vendor enables it).")
