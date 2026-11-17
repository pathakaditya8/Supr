"""Reset to menu-source-backed BMU vendor demo records (destructive to local DB)."""
from .database import Base, SessionLocal, engine
from .dominos_menu import DOMINOS
from .menu_data import KATHI, LAZEEZ, LAZEEZ_ADDONS
from .models import Category, Product, ProductAddon, ProductVariant, User, Vendor, VendorApplication
from .security import hash_password

FOOD_CATEGORIES=["Meals and Main Course","Snacks and Quick Bites","Beverages","Desserts and Sweets","Bakery and Confectionery","Fast Food","Healthy Food","Combos and Special Offers"]
from .import_tech_vendors import add_tech_vendors
from .tech_vendors import TECH_CATEGORIES

Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
db=SessionLocal()
categories={name:Category(name=name) for name in FOOD_CATEGORIES+TECH_CATEGORIES}
db.add_all(categories.values()); db.flush()
admin=User(name="BMU Marketplace Admin",email="admin@supr.bmu.edu.in",password_hash=hash_password("Demo@12345"),role="admin")
student=User(name="Aarav Mehta",email="student@supr.bmu.edu.in",password_hash=hash_password("Demo@12345"),role="student")
db.add_all([admin,student]); db.flush()
vendor_specs=[
 ("Kolkata's Lazeez","lazeez@supr.demo","Kathi rolls, momos, tandoori snacks, Chinese, rice and Indian main course.","8432813476",100,"Menu print states free delivery; vendor must confirm this and the ₹100 minimum before publication."),
 ("Kathi Junction","kathijunction@supr.demo","Rolls, starters, main course, biryani and breads.","9211931195 / 7042680426",None,"Photo labels contacts as order mobile 9211931195 and customer care 70426 80426. Delivery and minimum order are not stated."),
 ("Greenox","greenox@supr.demo","Menu coming soon.","",None,"Menu and vendor terms not yet captured."),
 ("Domino's","dominos@supr.demo","Pizzas, garlic breads, tacos, desserts and drinks.","",None,"Delivery terms, minimum order and serving outlet are not stated on the website menu."),
]
vendors={}
for name,email,description,phone,minimum,terms in vendor_specs:
    user=User(name=name,email=email,password_hash=hash_password("Demo@12345"),role="vendor")
    db.add(user); db.flush()
    vendor=Vendor(user_id=user.id,business_name=name,phone=phone,description=description,status="pending",delivers_to_bmu=False,agreement_valid=None,minimum_order_amount=minimum,delivery_terms_note=terms)
    db.add(vendor); db.flush(); vendors[name]=vendor
    db.add(VendorApplication(vendor_id=vendor.id,business_address="To be confirmed",contact_person="To be confirmed",agreement_reference="",status="pending",decision_remarks="Vendor participation and current details require BMU/vendor review."))

def add_catalog(vendor_name, rows, addons=()):
    vendor=vendors[vendor_name]
    for section,name,category,dietary,prices,portion,review,*extra in rows:
        numeric=[float(price) for _,price in prices]
        base=min(numeric) if numeric else None
        description=" ".join(x for x in (extra[0] if extra else "",f"Manual review: {review}" if review else "") if x)
        product=Product(vendor_id=vendor.id,category_id=categories[category].id,name=name,description=description,price=base,stock=0,available=False,image_url="",dietary=dietary,portion=portion,prep_time_minutes=None,menu_section=section,menu_status="published")
        db.add(product); db.flush()
        if len(prices)>1:
            for label,price in prices:
                db.add(ProductVariant(product_id=product.id,name=label,price=price,dietary=dietary,preparation="",portion=label,available=False))
        if addons and section in {"Veg. Kathi Rolls","Non Veg. Kathi Rolls"}:
            for addon_name,price in addons:
                db.add(ProductAddon(product_id=product.id,name=addon_name,price=price,available=False))

add_catalog("Kolkata's Lazeez",LAZEEZ,LAZEEZ_ADDONS)
momos=Product(vendor_id=vendors["Kolkata's Lazeez"].id,category_id=categories["Fast Food"].id,name="Momos",description="Preparation/filling prices transcribed from the supplied Lazeez momo menu photo. Current availability awaits vendor confirmation.",price=70,stock=0,available=False,image_url="",dietary="unspecified",menu_section="Momos",menu_status="published")
db.add(momos); db.flush()
styles={"Steam":{"Veg":70,"Paneer":100,"Chicken":100},"Fry":{"Veg":80,"Paneer":110,"Chicken":110},"Kurkure":{"Veg":110,"Paneer":140,"Chicken":140},"Schezwan":{"Veg":130,"Paneer":160,"Chicken":160},"Makhani":{"Veg":130,"Paneer":160,"Chicken":160},"Tandoori":{"Veg":130,"Paneer":160,"Chicken":160},"Afghani":{"Veg":150,"Paneer":180,"Chicken":180},"Chilli Gravy":{"Veg":130,"Paneer":160,"Chicken":160}}
for preparation,prices in styles.items():
    for filling,price in prices.items():
        db.add(ProductVariant(product_id=momos.id,name=f"{preparation} · {filling} Momos",price=price,dietary="non_vegetarian" if filling=="Chicken" else "vegetarian",preparation=preparation,portion="Not specified in photo",available=False))
add_catalog("Kathi Junction",KATHI)
add_catalog("Domino's",DOMINOS)
db.flush(); add_tech_vendors(db)
from .vendor_images import apply_vendor_images

db.flush(); apply_vendor_images(db)  # laptop and phone shops from public listings (status "listed")
db.commit(); db.close()
print(f"Seeded 4 pending source vendors; Lazeez={len(LAZEEZ)+1} products including 24 momo variants; Kathi Junction={len(KATHI)} menu rows; Domino's={len(DOMINOS)} website menu items. Unconfirmed availability/terms remain disabled.")
