import asyncio
import json
import re
import secrets
from contextlib import asynccontextmanager
from decimal import Decimal
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.orm import Session, selectinload

from . import keepalive
from . import models as m
from . import schemas as s
from .config import ALLOWED_ORIGINS, UPLOAD_DIR
from .database import Base, engine, ensure_columns, get_db
from .security import hash_password, issue_token, read_token, verify_password


@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(bind=engine)
    ensure_columns()
    url = keepalive.target_url()
    task = asyncio.create_task(keepalive.run(url)) if url else None
    yield
    if task: task.cancel()

app = FastAPI(title="Supr BMU Campus Market API", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=ALLOWED_ORIGINS, allow_credentials=True, allow_methods=["GET","POST","PATCH","PUT","DELETE"], allow_headers=["Authorization","Content-Type"])
bearer = HTTPBearer(auto_error=False)
FOOD_CATEGORIES={"Meals and Main Course","Snacks and Quick Bites","Beverages","Desserts and Sweets","Bakery and Confectionery","Fast Food","Healthy Food","Combos and Special Offers"}
TECH_CATEGORIES={"Laptop Repair","Laptops and Accessories","Phone Repair","Phones and Accessories"}
ALLOWED_CATEGORIES=FOOD_CATEGORIES|TECH_CATEGORIES
# "listed" vendors come from public information and have not joined: visible, but orders are refused.
VISIBLE_VENDOR_STATUSES=("approved","listed")

def current_user(creds: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)):
    data = read_token(creds.credentials) if creds else None
    if not data: raise HTTPException(401, "Please sign in to continue")
    user = db.get(m.User, data["sub"])
    if not user or not user.enabled: raise HTTPException(401, "Account unavailable")
    return user
def allow(*roles):
    def dependency(user: m.User = Depends(current_user)):
        if user.role not in roles: raise HTTPException(403, "This account cannot access that area")
        return user
    return dependency
def vendor_for(user, db):
    v = db.scalar(select(m.Vendor).where(m.Vendor.user_id == user.id))
    if not v: raise HTTPException(404, "Vendor profile not found")
    return v
def active_vendor(v):
    if v.status != "approved": raise HTTPException(403, "Only approved vendors can manage listings and orders")
def notify(db, uid, kind, message): db.add(m.Notification(recipient_id=uid,event_type=kind,message=message))
def notify_admins(db, kind, message):
    for admin_id in db.scalars(select(m.User.id).where(m.User.role=="admin",m.User.enabled.is_(True))): notify(db,admin_id,kind,message)
def audit(db, admin, vendor, action, decision, remarks="", application_id=None):
    db.add(m.ApprovalHistory(admin_id=admin.id,vendor_id=vendor.id,application_id=application_id,action=action,decision=decision,remarks=remarks))
    db.add(m.AuditLog(actor_id=admin.id,event_type=action,entity_type="vendor",entity_id=vendor.id,details=f"{decision}: {remarks}"))
# Load each page's variants and add-ons in two queries instead of two per product (N+1).
WITH_OPTIONS = (selectinload(m.Product.variants), selectinload(m.Product.addons))
LIKE_ESCAPE = "\\"
# Order lifecycle: pending -> accepted -> preparing -> ready -> (campus delivery: out_for_delivery ->) completed.
ACTIVE_STATUSES = ["pending","accepted","preparing","ready","out_for_delivery"]
ACTIVE_FOR_ARRIVAL = ["accepted","preparing","ready","out_for_delivery"]
STATUS_MESSAGES = {"accepted":"the vendor accepted your order.","rejected":"the vendor could not accept your order.","cancelled":"your order was cancelled.",
                   "preparing":"your food is being prepared.","ready":"your order is ready.","out_for_delivery":"your order is on the way to campus.",
                   "completed":"your order is complete. Enjoy your food!"}
def contains_pattern(text: str) -> str:
    """LIKE pattern matching `text` anywhere, with %, _ and the escape character taken literally."""
    for ch in (LIKE_ESCAPE, "%", "_"):
        text = text.replace(ch, LIKE_ESCAPE + ch)
    return f"%{text}%"
def photo_diet(dietary):
    return "vegetarian" if dietary in ("vegetarian","vegan") else "non_vegetarian" if dietary=="non_vegetarian" else "any"
def section_photo(db, vendor_id, section, dietary="any"):
    """Stock photo for a vendor's menu section matching the item's diet; all rows (a few dozen) are loaded once per request.
    A vegetarian item only falls back to the section's "any" photo, never to a non-vegetarian one."""
    cache=db.info.get("section_photos")
    if cache is None:
        cache={(x.vendor_id,x.menu_section,x.dietary):x for x in db.scalars(select(m.MenuSectionPhoto))}
        db.info["section_photos"]=cache
    return cache.get((vendor_id,section,photo_diet(dietary))) or cache.get((vendor_id,section,"any"))
def dish_photo(db, p):
    """Photo for the item's dish type and diet (e.g. veg kathi roll); the table is tiny, so it is loaded once per request."""
    from .dish_photos import dish_key
    cache=db.info.get("dish_photos")
    if cache is None:
        cache={x.key:x for x in db.scalars(select(m.DishPhoto))}; db.info["dish_photos"]=cache
    if not cache: return None
    cats=db.info.get("category_names")
    if cats is None:
        cats={x.id:x.name for x in db.scalars(select(m.Category))}; db.info["category_names"]=cats
    key,_=dish_key(p.name,p.menu_section or "",cats.get(p.category_id,""),p.dietary)
    return cache.get(key) if key else None
UNSPLASH_UTM="?utm_source=supr_bmu_campus_market&utm_medium=referral"
def image_fields(p, db):
    """The item's own photo if it has one, otherwise its section's illustrative stock photo with credit."""
    if p.image_url: return {"image_url":p.image_url,"image_illustrative":False,"image_credit":None}
    photo=dish_photo(db,p) or section_photo(db,p.vendor_id,p.menu_section,p.dietary)
    if not photo: return {"image_url":"","image_illustrative":False,"image_credit":None}
    return {"image_url":photo.image_url,"image_illustrative":True,"image_credit":{"name":photo.photographer,"url":photo.photographer_url+UNSPLASH_UTM,"source":photo.source,"source_url":"https://unsplash.com/"+UNSPLASH_UTM}}
def cached_get(db, model, key):
    """db.get with a per-request cache; the session itself only keeps weak references, so lists re-queried each row."""
    cache=db.info.setdefault("row_cache",{})
    if (model,key) not in cache: cache[(model,key)]=db.get(model,key)
    return cache[(model,key)]
def product_out(p, db):
    v=cached_get(db,m.Vendor,p.vendor_id); c=cached_get(db,m.Category,p.category_id)
    return {"id":p.id,"vendor_id":p.vendor_id,"vendor_name":v.business_name,"category_id":p.category_id,"category":c.name,"menu_section":p.menu_section,"menu_status":p.menu_status,"vendor_minimum_order":float(v.minimum_order_amount) if v.terms_confirmed and v.minimum_order_amount is not None else None,"delivery_terms_note":v.delivery_terms_note if v.terms_confirmed else "","vendor_phone":v.phone,"vendor_listed":v.status=="listed","name":p.name,"description":p.description,"price":float(p.price) if p.price is not None else None,"stock":p.stock,"available":p.available and p.stock>0 and p.menu_status=="published" and (not p.variants or any(x.available for x in p.variants)),"delivers_to_bmu":v.delivers_to_bmu,**image_fields(p,db),"own_image_url":p.image_url,"dietary":p.dietary,"spice_level":p.spice_level,"allergens":p.allergens,"portion":p.portion,"prep_time_minutes":p.prep_time_minutes,"variants":[{"id":x.id,"name":x.name,"price":float(x.price),"dietary":x.dietary,"preparation":x.preparation,"portion":x.portion,"available":x.available} for x in p.variants],"addons":[{"id":x.id,"name":x.name,"price":float(x.price) if x.price is not None else None,"available":x.available and x.price is not None} for x in p.addons]}
def selected_price(db, product, variant_id, addon_ids):
    variant=None
    if product.variants:
        variant=db.get(m.ProductVariant,variant_id) if variant_id else None
        if not variant or variant.product_id!=product.id or not variant.available: raise HTTPException(422,"Select an available product variant")
        price=Decimal(variant.price)
    else:
        if variant_id: raise HTTPException(422,"This product has no selectable variants")
        if product.price is None: raise HTTPException(422,"This menu item has no confirmed price")
        price=Decimal(product.price)
    addons=[]
    for addon_id in sorted(set(addon_ids)):
        addon=db.get(m.ProductAddon,addon_id)
        if not addon or addon.product_id!=product.id or not addon.available or addon.price is None: raise HTTPException(422,"One or more selected add-ons are unavailable or awaiting price confirmation")
        price += Decimal(addon.price); addons.append(addon)
    return price,variant,addons
def cart_out(cart, db):
    items=[]; subtotal=Decimal("0")
    for line in cart.items:
        p=db.get(m.Product,line.product_id); addons_selected=json.loads(line.addon_ids_json or "[]"); unit,variant,addons=selected_price(db,p,line.variant_id,addons_selected); row=product_out(p,db); row["cart_item_id"]=line.id; row["quantity"]=line.quantity; row["variant_id"]=variant.id if variant else None; row["variant_name"]=variant.name if variant else ""; row["addon_ids"]=addons_selected; row["addon_names"]=[x.name for x in addons]; row["unit_price"]=float(unit); row["line_total"]=round(float(unit)*line.quantity,2); subtotal += Decimal(str(row["line_total"])); items.append(row)
    if not items: cart.vendor_id=None
    vendor=db.get(m.Vendor,cart.vendor_id) if cart.vendor_id else None
    return {"id":cart.id,"vendor_id":cart.vendor_id,"vendor_name":vendor.business_name if vendor else None,"delivers_to_bmu":vendor.delivers_to_bmu if vendor else None,"delivery_points":json.loads(vendor.delivery_points_json or "[]") if vendor else [],"items":items,"subtotal":float(subtotal)}

@app.get("/api/health")
def health(): return {"status":"ok"}

# Students sign up with their BMU address: name.yearcourse@bmu.edu.in, for example dhruv.24cse@bmu.edu.in
STUDENT_EMAIL=re.compile(r"[a-z]+(?:[._-][a-z]+)*\.(\d{2})([a-z]{2,10})@bmu\.edu\.in")
STUDENT_EMAIL_HELP="Use your BMU email in the form name.yearcourse@bmu.edu.in, for example dhruv.24cse@bmu.edu.in"
FIRST_STUDENT_YEAR=13   # BMU's first intake; a later two-digit year than the current one cannot exist either

def check_student_email(email):
    found=STUDENT_EMAIL.fullmatch(email)
    if not found or not FIRST_STUDENT_YEAR<=int(found.group(1))<=m.now_utc().year%100: raise HTTPException(422,STUDENT_EMAIL_HELP)

@app.post("/api/auth/register")
def register(data:s.RegisterIn, db:Session=Depends(get_db)):
    if data.role not in {"student","vendor"}: raise HTTPException(403,"Only student and vendor accounts can be created here")
    email=data.email.strip().lower()
    if data.role=="student": check_student_email(email)
    if db.scalar(select(m.User).where(m.User.email==email)): raise HTTPException(409,"An account with this email already exists")
    user=m.User(name=data.name.strip(),email=email,password_hash=hash_password(data.password),role=data.role)
    db.add(user); db.flush()
    if data.role=="vendor":
        db.add(m.Vendor(user_id=user.id,business_name=data.name.strip(),status="unapplied"))
        notify_admins(db,"vendor_registered",f"New vendor registered: {data.name.strip()} ({email}). They have not sent their application yet.")
    db.commit(); db.refresh(user)
    return {"access_token":issue_token(user.id,user.role),"token_type":"bearer","user":{"id":user.id,"name":user.name,"email":user.email,"phone":user.phone,"role":user.role}}

@app.post("/api/auth/login")
def login(data:s.LoginIn, db:Session=Depends(get_db)):
    u=db.scalar(select(m.User).where(m.User.email==data.email.strip().lower()))
    if not u or not verify_password(data.password,u.password_hash): raise HTTPException(401,"Email or password is incorrect")
    return {"access_token":issue_token(u.id,u.role),"token_type":"bearer","user":{"id":u.id,"name":u.name,"email":u.email,"phone":u.phone,"role":u.role}}

@app.post("/api/auth/change-password")
def change_password(data:s.ChangePasswordIn,u:m.User=Depends(current_user),db:Session=Depends(get_db)):
    """Lets a signed-in student, vendor or admin replace their own password (there is no e-mail reset)."""
    if not verify_password(data.current_password,u.password_hash): raise HTTPException(400,"Current password is incorrect")
    if data.new_password==data.current_password: raise HTTPException(400,"Choose a new password that is different from the current one")
    u.password_hash=hash_password(data.new_password); db.commit()
    return {"ok":True}

@app.get("/api/auth/me")
def me(u:m.User=Depends(current_user)):
    return {"id":u.id,"name":u.name,"email":u.email,"phone":u.phone,"role":u.role}

@app.put("/api/student/profile")
def update_student_profile(data:s.StudentProfileIn,u:m.User=Depends(allow("student")),db:Session=Depends(get_db)):
    phone=data.phone.strip()
    if len(phone)<7: raise HTTPException(422,"Enter a valid phone number")
    u.phone=phone; db.commit(); db.refresh(u)
    return {"id":u.id,"name":u.name,"email":u.email,"phone":u.phone,"role":u.role}

@app.get("/api/categories")
def categories(db:Session=Depends(get_db)):
    return [{"id":c.id,"name":c.name} for c in db.scalars(select(m.Category).order_by(m.Category.name))]

@app.get("/api/products")
def products(q:str="",kind:str|None=None,category_id:int|None=None,vendor_id:int|None=None,menu_section:str|None=None,min_price:float|None=None,max_price:float|None=None,sort:str="relevance",available_only:bool=False,campus_delivery:bool|None=None,dietary:str|None=None,page:int=Query(1,ge=1),limit:int=Query(24,ge=1,le=100),db:Session=Depends(get_db)):
    stmt=select(m.Product).join(m.Vendor).join(m.Category).where(m.Vendor.status.in_(VISIBLE_VENDOR_STATUSES),m.Product.menu_status=="published")
    if q.strip():
        term=contains_pattern(q.strip())
        stmt=stmt.where(m.Product.name.ilike(term,escape=LIKE_ESCAPE) | m.Product.description.ilike(term,escape=LIKE_ESCAPE) | m.Category.name.ilike(term,escape=LIKE_ESCAPE) | m.Vendor.business_name.ilike(term,escape=LIKE_ESCAPE))
    # kind=food or kind=tech keeps the food menu and the laptop / phone page apart
    if kind=="food": stmt=stmt.where(m.Category.name.in_(FOOD_CATEGORIES))
    elif kind=="tech": stmt=stmt.where(m.Category.name.in_(TECH_CATEGORIES))
    if category_id: stmt=stmt.where(m.Product.category_id==category_id)
    if vendor_id: stmt=stmt.where(m.Product.vendor_id==vendor_id)
    if menu_section: stmt=stmt.where(m.Product.menu_section==menu_section)
    if dietary in {"vegetarian","non_vegetarian","vegan"}:
        matching_variant=select(m.ProductVariant.id).where(m.ProductVariant.product_id==m.Product.id,m.ProductVariant.dietary==dietary).exists()
        stmt=stmt.where(or_(m.Product.dietary==dietary,matching_variant))
    if min_price is not None or max_price is not None:
        base_conditions=[m.Product.price.is_not(None)]
        variant_conditions=[]
        if min_price is not None:
            base_conditions.append(m.Product.price>=min_price); variant_conditions.append(m.ProductVariant.price>=min_price)
        if max_price is not None:
            base_conditions.append(m.Product.price<=max_price); variant_conditions.append(m.ProductVariant.price<=max_price)
        has_variants=select(m.ProductVariant.id).where(m.ProductVariant.product_id==m.Product.id).exists()
        matching_price_variant=select(m.ProductVariant.id).where(m.ProductVariant.product_id==m.Product.id,*variant_conditions).exists()
        stmt=stmt.where(or_(and_(~has_variants,*base_conditions),matching_price_variant))
    if available_only: stmt=stmt.where(m.Product.available.is_(True),m.Product.stock>0)
    if campus_delivery is not None: stmt=stmt.where(m.Vendor.delivers_to_bmu.is_(campus_delivery))
    stmt=stmt.order_by(m.Product.price.asc() if sort=="price_asc" else m.Product.price.desc() if sort=="price_desc" else m.Product.name.asc())
    total=db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows=db.scalars(stmt.options(*WITH_OPTIONS).offset((page-1)*limit).limit(limit)).all()
    return {"items":[product_out(p,db) for p in rows],"total":total,"page":page,"limit":limit}

@app.get("/api/products/{product_id}")
def product_detail(product_id:int,db:Session=Depends(get_db)):
    p=db.get(m.Product,product_id)
    if not p or p.menu_status!="published" or db.get(m.Vendor,p.vendor_id).status not in VISIBLE_VENDOR_STATUSES: raise HTTPException(404,"Listing not found")
    return product_out(p,db)

@app.get("/api/vendors/{vendor_id}")
def vendor_public(vendor_id:int,db:Session=Depends(get_db)):
    v=db.get(m.Vendor,vendor_id)
    if not v or v.status not in VISIBLE_VENDOR_STATUSES: raise HTTPException(404,"Vendor not found")
    return {"id":v.id,"business_name":v.business_name,"description":v.description,"phone":v.phone,"delivers_to_bmu":v.delivers_to_bmu,"minimum_order_amount":float(v.minimum_order_amount) if v.terms_confirmed and v.minimum_order_amount is not None else None,"delivery_terms_note":v.delivery_terms_note if v.terms_confirmed else "","delivery_points":json.loads(v.delivery_points_json or "[]"),"listed":v.status=="listed","image_url":v.image_url or "","address":v.application.business_address if v.status=="listed" and v.application else ""}

@app.get("/api/vendors")
def vendors_public(db:Session=Depends(get_db)):
    catalogue=func.count(m.Product.id).filter(m.Product.menu_status=="published").label("catalogue_count")
    available=func.count(m.Product.id).filter(m.Product.menu_status=="published",m.Product.available.is_(True),m.Product.stock>0).label("listing_count")
    rows=db.execute(select(m.Vendor.id,m.Vendor.business_name,m.Vendor.description,m.Vendor.delivers_to_bmu,m.Vendor.status,m.Vendor.image_url,catalogue,available).outerjoin(m.Product,m.Product.vendor_id==m.Vendor.id).where(m.Vendor.status.in_(VISIBLE_VENDOR_STATUSES)).group_by(m.Vendor.id).order_by(m.Vendor.business_name)).all()
    # Per-shop summary for the landing page: food or tech, lowest published price, main categories.
    summary={}
    for vid,cat,price in db.execute(select(m.Product.vendor_id,m.Category.name,m.Product.price).join(m.Category).where(m.Product.menu_status=="published")):
        d=summary.setdefault(vid,{"cats":{},"min":None})
        d["cats"][cat]=d["cats"].get(cat,0)+1
        if price is not None and price>0 and (d["min"] is None or price<d["min"]): d["min"]=price
    def info(vid):
        d=summary.get(vid,{"cats":{},"min":None}); cats=sorted(d["cats"],key=lambda c:-d["cats"][c])
        kind="tech" if cats and all(c in TECH_CATEGORIES for c in cats) else "food"
        return {"kind":kind,"min_price":float(d["min"]) if d["min"] is not None else None,"top_categories":cats[:3]}
    return [{"id":r.id,"business_name":r.business_name,"description":r.description,"delivers_to_bmu":r.delivers_to_bmu,"catalogue_count":r.catalogue_count,"listing_count":r.listing_count,"listed":r.status=="listed","image_url":r.image_url or "",**info(r.id)} for r in rows]

@app.post("/api/vendor/applications",status_code=201)
def submit_application(data:s.ApplicationIn,u:m.User=Depends(allow("vendor")),db:Session=Depends(get_db)):
    v=vendor_for(u,db)
    if v.status in {"approved","stopped"}: raise HTTPException(409,"This vendor is already participating in the marketplace")
    existing=v.application
    if existing and existing.status=="pending": raise HTTPException(409,"An application is already awaiting review")
    v.business_name=data.business_name.strip(); v.phone=data.phone.strip(); v.description=data.description.strip(); v.status="pending"
    if existing:
        application=existing; application.business_address=data.business_address; application.contact_person=data.contact_person; application.agreement_reference=data.agreement_reference; application.delivery_partners=data.delivery_partners; application.status="pending"; application.decision_at=None; application.decision_remarks=""
    else:
        application=m.VendorApplication(vendor_id=v.id,business_address=data.business_address,contact_person=data.contact_person,agreement_reference=data.agreement_reference,delivery_partners=data.delivery_partners); db.add(application)
    db.flush(); notify(db,u.id,"application_submitted","Your vendor application is awaiting University review.")
    notify_admins(db,"application_submitted",f"{v.business_name} sent a vendor application for review."); db.commit()
    return {"id":application.id,"status":application.status,"submitted_at":application.submitted_at}

@app.get("/api/vendor/application")
def my_application(u:m.User=Depends(allow("vendor")),db:Session=Depends(get_db)):
    v=vendor_for(u,db); a=v.application
    return {"status":v.status,"application":{"id":a.id,"status":a.status,"decision_remarks":a.decision_remarks,"submitted_at":a.submitted_at,"decision_at":a.decision_at} if a else None}

@app.post("/api/vendor/application/documents",status_code=201)
async def upload_document(file:UploadFile=File(...),u:m.User=Depends(allow("vendor")),db:Session=Depends(get_db)):
    v=vendor_for(u,db); a=v.application
    if not a or a.status!="pending": raise HTTPException(409,"Submit a pending application before uploading documents")
    ext=Path(file.filename or "").suffix.lower()
    if ext not in {".pdf",".png",".jpg",".jpeg"}: raise HTTPException(415,"Upload a PDF, PNG, or JPEG document")
    data=await file.read(5*1024*1024+1)
    if len(data)>5*1024*1024: raise HTTPException(413,"Documents must be 5 MB or smaller")
    signatures={".pdf":b"%PDF-",".png":b"\x89PNG\r\n\x1a\n",".jpg":b"\xff\xd8\xff",".jpeg":b"\xff\xd8\xff"}
    if not data.startswith(signatures[ext]): raise HTTPException(415,"File contents do not match the selected document type")
    saved=f"{secrets.token_hex(16)}{ext}"; content_type=file.content_type or "application/octet-stream"; db.add(m.StoredFile(key=saved,content_type=content_type,content=data))
    doc=m.VendorDocument(application_id=a.id,filename=Path(file.filename).name,stored_path=saved,content_type=content_type); db.add(doc); db.commit()
    return {"id":doc.id,"filename":doc.filename,"uploaded_at":doc.uploaded_at}

@app.get("/api/vendor/products")
def my_products(u:m.User=Depends(allow("vendor")),db:Session=Depends(get_db)):
    v=vendor_for(u,db); return [product_out(p,db) for p in db.scalars(select(m.Product).options(*WITH_OPTIONS).where(m.Product.vendor_id==v.id,m.Product.menu_status!="removed").order_by(m.Product.id.desc()))]

@app.post("/api/vendor/products",status_code=201)
def create_product(data:s.ProductIn,u:m.User=Depends(allow("vendor")),db:Session=Depends(get_db)):
    v=vendor_for(u,db); active_vendor(v)
    category=db.get(m.Category,data.category_id)
    if not category: raise HTTPException(404,"Food category not found")
    if category.name not in ALLOWED_CATEGORIES: raise HTTPException(422,"Listings must use one of the approved categories")
    p=m.Product(vendor_id=v.id,menu_status="published",**data.model_dump()); db.add(p); db.commit(); db.refresh(p); return product_out(p,db)

STOCK_ON_HAND=9999  # matches the frontend's "in stock" quantity

@app.post("/api/vendor/products/availability")
def bulk_product_availability(data:s.BulkAvailabilityIn,u:m.User=Depends(allow("vendor")),db:Session=Depends(get_db)):
    """Mark every live (published or review) listing in or out of stock. Paused/removed items are untouched."""
    v=vendor_for(u,db); active_vendor(v)
    updated=skipped=0
    for p in db.scalars(select(m.Product).where(m.Product.vendor_id==v.id,m.Product.menu_status.in_(("published","review")))):
        if data.available:
            if p.price is None and not p.variants: skipped+=1; continue
            p.stock=STOCK_ON_HAND; p.available=True; p.menu_status="published"
        else:
            p.stock=0
            if p.menu_status=="review": p.menu_status="published"
        for x in p.variants: x.available=data.available
        updated+=1
    db.add(m.AuditLog(actor_id=u.id,event_type="vendor_bulk_availability",entity_type="vendor",entity_id=v.id,details=f"available={data.available} updated={updated} skipped={skipped}"))
    db.commit()
    return {"available":data.available,"updated":updated,"skipped_unpriced":skipped}

@app.patch("/api/vendor/products/{pid}")
def update_product(pid:int,data:s.ProductUpdate,u:m.User=Depends(allow("vendor")),db:Session=Depends(get_db)):
    v=vendor_for(u,db); active_vendor(v); p=db.get(m.Product,pid)
    if not p or p.vendor_id!=v.id: raise HTTPException(404,"Listing not found")
    values=data.model_dump(exclude_unset=True)
    if values.get("category_id") is not None:
        category=db.get(m.Category,values["category_id"])
        if not category or category.name not in ALLOWED_CATEGORIES: raise HTTPException(422,"Listings must use one of the approved categories")
    was_review=p.menu_status=="review"
    for k,val in values.items(): setattr(p,k,val)
    if values.get("available") is True:
        if p.price is None: raise HTTPException(422,"A confirmed price is required before publishing")
        p.menu_status="published"
    elif values.get("available") is False:
        p.menu_status="published" if was_review else "paused"
    elif was_review:
        p.menu_status="published"
    db.commit(); return product_out(p,db)

@app.delete("/api/vendor/products/{pid}",status_code=204)
def delete_product(pid:int,u:m.User=Depends(allow("vendor")),db:Session=Depends(get_db)):
    v=vendor_for(u,db); active_vendor(v); p=db.get(m.Product,pid)
    if not p or p.vendor_id!=v.id: raise HTTPException(404,"Listing not found")
    p.available=False; p.menu_status="removed"; db.commit()

@app.put("/api/vendor/delivery")
def update_delivery(data:s.DeliveryIn,u:m.User=Depends(allow("vendor")),db:Session=Depends(get_db)):
    v=vendor_for(u,db); active_vendor(v)
    if data.delivers_to_bmu and not json.loads(v.delivery_points_json or "[]"): raise HTTPException(409,"Add at least one supported campus delivery point first")
    v.delivers_to_bmu=data.delivers_to_bmu; db.commit(); return {"delivers_to_bmu":v.delivers_to_bmu}

@app.get("/api/vendor/delivery-points")
def get_delivery_points(u:m.User=Depends(allow("vendor")),db:Session=Depends(get_db)):
    v=vendor_for(u,db)
    return {"delivery_points":json.loads(v.delivery_points_json or "[]"),"delivers_to_bmu":v.delivers_to_bmu}

@app.put("/api/vendor/delivery-points")
def update_delivery_points(data:s.DeliveryPointsIn,u:m.User=Depends(allow("vendor")),db:Session=Depends(get_db)):
    v=vendor_for(u,db); active_vendor(v)
    points=[]
    for raw in data.points:
        point=" ".join(raw.split())
        if not point or len(point)>80: raise HTTPException(422,"Each delivery point must be 1–80 characters")
        if point.casefold() not in {x.casefold() for x in points}: points.append(point)
    v.delivery_points_json=json.dumps(points)
    if not points: v.delivers_to_bmu=False
    db.commit()
    return {"delivery_points":points,"delivers_to_bmu":v.delivers_to_bmu}

@app.put("/api/vendor/terms")
def update_vendor_terms(data:s.VendorTermsIn,u:m.User=Depends(allow("vendor")),db:Session=Depends(get_db)):
    v=vendor_for(u,db); active_vendor(v)
    v.minimum_order_amount=data.minimum_order_amount; v.delivery_terms_note=data.delivery_terms_note.strip(); v.terms_confirmed=data.terms_confirmed
    db.add(m.AuditLog(actor_id=u.id,event_type="vendor_terms_updated",entity_type="vendor",entity_id=v.id,details=f"terms_confirmed={v.terms_confirmed}")); db.commit()
    return {"minimum_order_amount":float(v.minimum_order_amount) if v.minimum_order_amount is not None else None,"delivery_terms_note":v.delivery_terms_note,"terms_confirmed":v.terms_confirmed}

@app.put("/api/vendor/products/{pid}/variants")
def replace_product_variants(pid:int,data:s.VariantListIn,u:m.User=Depends(allow("vendor")),db:Session=Depends(get_db)):
    v=vendor_for(u,db); active_vendor(v); p=db.get(m.Product,pid)
    if not p or p.vendor_id!=v.id: raise HTTPException(404,"Listing not found")
    seen=set()
    for row in data.variants:
        if row.name.strip().casefold() in seen: raise HTTPException(422,"Variant names must be unique")
        seen.add(row.name.strip().casefold())
        variant=db.get(m.ProductVariant,row.id) if row.id else None
        if variant and variant.product_id!=p.id: raise HTTPException(422,"A selected variant belongs to another listing")
        if variant is None:
            variant=m.ProductVariant(product_id=p.id,name=row.name.strip(),price=row.price,dietary=row.dietary,preparation=row.preparation.strip(),portion=row.portion.strip(),available=row.available)
            db.add(variant)
        else:
            for field in ("name","price","dietary","preparation","portion","available"): setattr(variant,field,getattr(row,field))
    for existing in list(p.variants):
        if existing.name.casefold() not in seen: existing.available=False
    if data.variants: p.price=min(row.price for row in data.variants)
    db.add(m.AuditLog(actor_id=u.id,event_type="vendor_variants_updated",entity_type="product",entity_id=p.id,details=f"variants={len(data.variants)}")); db.commit()
    return product_out(p,db)

@app.put("/api/vendor/products/{pid}/addons")
def replace_product_addons(pid:int,data:s.AddonListIn,u:m.User=Depends(allow("vendor")),db:Session=Depends(get_db)):
    v=vendor_for(u,db); active_vendor(v); p=db.get(m.Product,pid)
    if not p or p.vendor_id!=v.id: raise HTTPException(404,"Listing not found")
    seen=set()
    for row in data.addons:
        key=row.name.strip().casefold()
        if key in seen: raise HTTPException(422,"Add-on names must be unique")
        seen.add(key)
        if row.available and row.price is None: raise HTTPException(422,"An add-on needs a confirmed price before it can be enabled")
        addon=db.get(m.ProductAddon,row.id) if row.id else None
        if addon and addon.product_id!=p.id: raise HTTPException(422,"A selected add-on belongs to another listing")
        if addon is None:
            db.add(m.ProductAddon(product_id=p.id,name=row.name.strip(),price=row.price,available=row.available))
        else:
            addon.name=row.name.strip(); addon.price=row.price; addon.available=row.available
    for existing in p.addons:
        if existing.name.casefold() not in seen: existing.available=False
    db.add(m.AuditLog(actor_id=u.id,event_type="vendor_addons_updated",entity_type="product",entity_id=p.id,details=f"addons={len(data.addons)}")); db.commit()
    return product_out(p,db)

@app.get("/api/cart")
def get_cart(u:m.User=Depends(allow("student")),db:Session=Depends(get_db)):
    cart=db.scalar(select(m.Cart).where(m.Cart.student_id==u.id))
    return cart_out(cart,db) if cart else {"items":[],"subtotal":0,"vendor_id":None,"vendor_name":None,"delivers_to_bmu":None}

@app.delete("/api/cart")
def clear_cart(u:m.User=Depends(allow("student")),db:Session=Depends(get_db)):
    cart=db.scalar(select(m.Cart).where(m.Cart.student_id==u.id))
    if cart:
        for line in list(cart.items): db.delete(line)
        cart.vendor_id=None; db.commit()
    return {"items":[],"subtotal":0,"vendor_id":None,"vendor_name":None,"delivers_to_bmu":None}

@app.post("/api/cart/items",status_code=201)
def add_cart_item(data:s.CartLineIn,u:m.User=Depends(allow("student")),db:Session=Depends(get_db)):
    p=db.get(m.Product,data.product_id)
    if p and db.get(m.Vendor,p.vendor_id).status=="listed": raise HTTPException(409,"This shop has not joined Supr yet, so it cannot take orders here. Please contact the shop directly.")
    if not p or not p.available or p.menu_status!="published" or p.stock<data.quantity: raise HTTPException(409,"This listing is unavailable or has insufficient stock")
    v=db.get(m.Vendor,p.vendor_id)
    if v.status!="approved": raise HTTPException(409,"This vendor is not active")
    cart=db.scalar(select(m.Cart).where(m.Cart.student_id==u.id))
    if cart and not cart.items: cart.vendor_id=None          # an emptied cart does not stay tied to its old vendor
    if cart and cart.items and cart.vendor_id and cart.vendor_id!=v.id: raise HTTPException(409,"Your cart can contain items from one vendor only. Clear it before switching vendors.")
    if not cart: cart=m.Cart(student_id=u.id,vendor_id=v.id); db.add(cart); db.flush()
    cart.vendor_id=v.id; line=next((x for x in cart.items if x.product_id==p.id),None)
    price,variant,addons=selected_price(db,p,data.variant_id,data.addon_ids)
    selection_key=":".join([str(variant.id) if variant else "base",",".join(map(str,sorted(set(data.addon_ids))))])
    line=next((x for x in cart.items if x.product_id==p.id and x.selection_key==selection_key),None)
    if line:
        if line.quantity+data.quantity>p.stock: raise HTTPException(409,"Requested quantity exceeds available stock")
        line.quantity+=data.quantity
    else: cart.items.append(m.CartItem(product_id=p.id,variant_id=variant.id if variant else None,addon_ids_json=json.dumps([x.id for x in addons]),selection_key=selection_key,quantity=data.quantity))
    db.commit(); db.refresh(cart); return cart_out(cart,db)

@app.patch("/api/cart/items/{item_id}")
def set_cart_item(item_id:int,data:s.QuantityIn,u:m.User=Depends(allow("student")),db:Session=Depends(get_db)):
    cart=db.scalar(select(m.Cart).where(m.Cart.student_id==u.id)); line=next((x for x in cart.items if x.id==item_id),None) if cart else None
    p=db.get(m.Product,line.product_id) if line else None
    if not line or not p: raise HTTPException(404,"Cart item not found")
    if data.quantity>p.stock: raise HTTPException(409,"Requested quantity exceeds available stock")
    line.quantity=data.quantity; db.commit(); return cart_out(cart,db)

@app.delete("/api/cart/items/{item_id}")
def remove_cart_item(item_id:int,u:m.User=Depends(allow("student")),db:Session=Depends(get_db)):
    cart=db.scalar(select(m.Cart).where(m.Cart.student_id==u.id))
    if not cart: raise HTTPException(404,"Cart is empty")
    line=next((x for x in cart.items if x.id==item_id),None)
    if not line: raise HTTPException(404,"Cart item not found")
    db.delete(line); db.flush(); db.expire(cart,["items"])   # reload: the deleted line is still in the in-memory list until then
    if not cart.items: cart.vendor_id=None
    db.commit(); return cart_out(cart,db)

@app.post("/api/orders",status_code=201)
def checkout(data:s.CheckoutIn|None=None,u:m.User=Depends(allow("student")),db:Session=Depends(get_db)):
    cart=db.scalar(select(m.Cart).where(m.Cart.student_id==u.id))
    if not cart or not cart.items: raise HTTPException(400,"Your cart is empty")
    vendor=db.get(m.Vendor,cart.vendor_id)
    if not vendor or vendor.status!="approved": raise HTTPException(409,"This vendor is not active")
    delivery_points=json.loads(vendor.delivery_points_json or "[]")
    destination=(data.delivery_location if data else "").strip()
    if vendor.delivers_to_bmu:
        if not delivery_points: raise HTTPException(409,"This vendor has not configured delivery locations yet; contact them or choose a pickup vendor")
        if destination not in delivery_points: raise HTTPException(422,"Choose one of this vendor’s supported delivery locations")
    elif destination: raise HTTPException(422,"This vendor is not accepting campus delivery")
    subtotal=Decimal("0"); snapshots=[]
    for line in cart.items:
        p=db.get(m.Product,line.product_id)
        if not p or p.vendor_id!=vendor.id or not p.available or p.menu_status!="published" or p.stock<line.quantity: raise HTTPException(409,"A cart item is no longer available in the requested quantity")
        unit,variant,addons=selected_price(db,p,line.variant_id,json.loads(line.addon_ids_json or "[]")); subtotal += unit*line.quantity; snapshots.append((p,line.quantity,unit,variant,addons))
    order=m.Order(student_id=u.id,vendor_id=vendor.id,status="pending",campus_delivery=vendor.delivers_to_bmu,delivery_location=destination,subtotal=subtotal)
    db.add(order); db.flush()
    for p,qty,unit,variant,addons in snapshots:
        order.items.append(m.OrderItem(product_id=p.id,product_name=p.name,unit_price=unit,quantity=qty,was_available=p.available,variant_name=variant.name if variant else "",addons_json=json.dumps([x.name for x in addons])))
        changed=db.execute(update(m.Product).where(m.Product.id==p.id,m.Product.available.is_(True),m.Product.stock>=qty).values(stock=m.Product.stock-qty,available=(m.Product.stock-qty)>0))
        if changed.rowcount!=1: raise HTTPException(409,"A cart item just sold out; please review your cart")
    for line in list(cart.items): db.delete(line)
    cart.vendor_id=None; notify(db,vendor.user_id,"new_order",f"New order #{order.id} received."); db.add(m.AuditLog(actor_id=u.id,event_type="order_created",entity_type="order",entity_id=order.id,details=f"subtotal={subtotal}")); db.commit(); db.refresh(order)
    return {"id":order.id,"status":order.status,"subtotal":float(order.subtotal),"campus_delivery":order.campus_delivery,"delivery_location":order.delivery_location,"delivery_stage":order.delivery_stage,"created_at":order.created_at}

@app.get("/api/orders")
def orders(u:m.User=Depends(current_user),db:Session=Depends(get_db)):
    stmt=select(m.Order).order_by(m.Order.created_at.desc())
    if u.role=="student": stmt=stmt.where(m.Order.student_id==u.id)
    elif u.role=="vendor": stmt=stmt.where(m.Order.vendor_id==vendor_for(u,db).id)
    elif u.role!="admin": raise HTTPException(403,"This account cannot access orders")
    rows=db.scalars(stmt).all()
    return [{"id":o.id,"student_id":o.student_id,"student_name":db.get(m.User,o.student_id).name,"vendor_id":o.vendor_id,"vendor_name":db.get(m.Vendor,o.vendor_id).business_name,"status":o.status,"subtotal":float(o.subtotal),"campus_delivery":o.campus_delivery,"delivery_location":o.delivery_location,"delivery_stage":o.delivery_stage,"created_at":o.created_at,"items":[{"name":i.product_name,"quantity":i.quantity,"unit_price":float(i.unit_price),"variant_name":i.variant_name,"addons":json.loads(i.addons_json or "[]")} for i in o.items]} for o in rows]

@app.patch("/api/orders/{order_id}/status")
def update_order_status(order_id:int,data:s.StatusIn,u:m.User=Depends(allow("vendor")),db:Session=Depends(get_db)):
    v=vendor_for(u,db); active_vendor(v); order=db.get(m.Order,order_id)
    if not order or order.vendor_id!=v.id: raise HTTPException(404,"Order not found")
    transitions={"pending":{"accepted","rejected","cancelled"},"accepted":{"preparing","cancelled"},"preparing":{"ready"},"ready":{"out_for_delivery","completed"} if order.campus_delivery else {"completed"},"out_for_delivery":{"completed"},"completed":set(),"cancelled":set(),"rejected":set()}
    if data.status not in transitions.get(order.status,set()): raise HTTPException(409,"That order status change is not allowed")
    if data.status in {"cancelled","rejected"}:
        for item in order.items:
            p=db.get(m.Product,item.product_id); p.stock+=item.quantity; p.available=item.was_available
    order.status=data.status; notify(db,order.student_id,"order_status",f"Order #{order.id}: {STATUS_MESSAGES.get(data.status,data.status)}"); db.add(m.AuditLog(actor_id=u.id,event_type="order_status_updated",entity_type="order",entity_id=order.id,details=data.status)); db.commit(); return {"id":order.id,"status":order.status}

@app.post("/api/vendor/orders/arrival-broadcast")
def broadcast_order_arrival(data:s.ArrivalIn,u:m.User=Depends(allow("vendor")),db:Session=Depends(get_db)):
    v=vendor_for(u,db); active_vendor(v)
    rows=db.scalars(select(m.Order).where(m.Order.vendor_id==v.id,m.Order.campus_delivery.is_(True),m.Order.status.in_(ACTIVE_FOR_ARRIVAL),m.Order.delivery_stage!=data.stage)).all()
    gate="college main gate" if data.stage=="main_gate" else "hostel gate"
    for order in rows:
        order.delivery_stage=data.stage
        destination=f" for {order.delivery_location}" if order.delivery_location else ""
        notify(db,order.student_id,"order_delivery_arrival",f"Order #{order.id} has reached the {gate}{destination}. Please collect it.")
        db.add(m.AuditLog(actor_id=u.id,event_type="delivery_arrival_broadcast",entity_type="order",entity_id=order.id,details=data.stage))
    db.commit()
    return {"notified_orders":len(rows),"delivery_stage":data.stage}

@app.post("/api/orders/{order_id}/arrival")
def announce_order_arrival(order_id:int,data:s.ArrivalIn,u:m.User=Depends(allow("vendor")),db:Session=Depends(get_db)):
    v=vendor_for(u,db); active_vendor(v); order=db.get(m.Order,order_id)
    if not order or order.vendor_id!=v.id: raise HTTPException(404,"Order not found")
    if not order.campus_delivery or order.status in {"cancelled","rejected"}: raise HTTPException(409,"This order is not eligible for a campus delivery notice")
    if order.delivery_stage==data.stage: raise HTTPException(409,"This arrival notice has already been sent")
    if order.status not in ACTIVE_FOR_ARRIVAL: raise HTTPException(409,"Accept the order before sending an arrival notice")
    order.delivery_stage=data.stage
    gate="college main gate" if data.stage=="main_gate" else "hostel gate"
    destination=f" for {order.delivery_location}" if order.delivery_location else ""
    notify(db,order.student_id,"order_delivery_arrival",f"Order #{order.id} has reached the {gate}{destination}. Please collect it.")
    db.add(m.AuditLog(actor_id=u.id,event_type="delivery_arrival_notified",entity_type="order",entity_id=order.id,details=data.stage))
    db.commit(); return {"id":order.id,"delivery_stage":order.delivery_stage}

@app.post("/api/orders/{order_id}/cancel")
def cancel_student_order(order_id:int,u:m.User=Depends(allow("student")),db:Session=Depends(get_db)):
    order=db.get(m.Order,order_id)
    if not order or order.student_id!=u.id: raise HTTPException(404,"Order not found")
    if order.status!="pending": raise HTTPException(409,"Only pending order requests can be cancelled")
    for item in order.items:
        p=db.get(m.Product,item.product_id); p.stock+=item.quantity; p.available=item.was_available
    order.status="cancelled"; notify(db,db.get(m.Vendor,order.vendor_id).user_id,"order_cancelled",f"Order #{order.id} was cancelled by the student.")
    db.add(m.AuditLog(actor_id=u.id,event_type="student_order_cancelled",entity_type="order",entity_id=order.id,details="Cancelled while pending")); db.commit()
    return {"id":order.id,"status":order.status}

@app.get("/api/notifications")
def notifications(u:m.User=Depends(current_user),db:Session=Depends(get_db)):
    rows=db.scalars(select(m.Notification).where(m.Notification.recipient_id==u.id).order_by(m.Notification.created_at.desc()).limit(100)).all()
    return {"unread_count":sum(not n.read for n in rows),"items":[{"id":n.id,"event_type":n.event_type,"message":n.message,"read":n.read,"created_at":n.created_at} for n in rows]}

@app.post("/api/notifications/{nid}/read")
def mark_read(nid:int,u:m.User=Depends(current_user),db:Session=Depends(get_db)):
    n=db.get(m.Notification,nid)
    if not n or n.recipient_id!=u.id: raise HTTPException(404,"Notification not found")
    n.read=True; db.commit(); return {"id":n.id,"read":True}

@app.get("/api/admin/applications")
def admin_applications(status:str|None=None,u:m.User=Depends(allow("admin")),db:Session=Depends(get_db)):
    stmt=select(m.VendorApplication).join(m.Vendor)
    if status: stmt=stmt.where(m.VendorApplication.status==status)
    rows=db.scalars(stmt.order_by(m.VendorApplication.submitted_at.desc())).all()
    result=[{"id":a.id,"vendor_id":a.vendor_id,"user_id":a.vendor.user_id,"business_name":a.vendor.business_name,"email":a.vendor.user.email,"phone":a.vendor.phone,"description":a.vendor.description,"minimum_order_amount":float(a.vendor.minimum_order_amount) if a.vendor.minimum_order_amount is not None else None,"delivery_terms_note":a.vendor.delivery_terms_note,"terms_confirmed":a.vendor.terms_confirmed,"business_address":a.business_address,"contact_person":a.contact_person,"agreement_reference":a.agreement_reference,"delivery_partners":a.delivery_partners,"agreement_valid":a.vendor.agreement_valid,"vendor_status":a.vendor.status,"status":a.status,"decision_remarks":a.decision_remarks,"submitted_at":a.submitted_at,"documents":[{"id":d.id,"filename":d.filename,"url":f"/api/admin/documents/{d.id}"} for d in db.scalars(select(m.VendorDocument).where(m.VendorDocument.application_id==a.id))]} for a in rows]
    if status in (None,"unapplied"):          # vendors who registered but have not sent their business details yet
        waiting=db.scalars(select(m.Vendor).join(m.User,m.Vendor.user_id==m.User.id).where(m.Vendor.status=="unapplied").order_by(m.User.created_at.desc())).all()
        result+=[{"id":-v.id,"vendor_id":v.id,"user_id":v.user_id,"business_name":v.business_name,"email":v.user.email,"phone":v.phone,"description":v.description,"minimum_order_amount":None,"delivery_terms_note":"","terms_confirmed":False,
                  "business_address":"","contact_person":"","agreement_reference":"","delivery_partners":None,"agreement_valid":None,"vendor_status":"unapplied","status":"unapplied","decision_remarks":"","submitted_at":v.user.created_at,"documents":[]} for v in waiting]
    return result

@app.get("/api/admin/documents/{doc_id}")
def admin_document(doc_id:int,u:m.User=Depends(allow("admin")),db:Session=Depends(get_db)):
    from fastapi.responses import Response
    doc=db.get(m.VendorDocument,doc_id)
    if not doc: raise HTTPException(404,"Document not found")
    stored=db.get(m.StoredFile,doc.stored_path)
    if not stored:
        legacy=Path(UPLOAD_DIR)/doc.stored_path          # files saved to disk before uploads moved into the database
        if not legacy.is_file(): raise HTTPException(404,"Document file unavailable")
        content,content_type=legacy.read_bytes(),doc.content_type
    else: content,content_type=stored.content,stored.content_type
    safe_name=re.sub(r'[^A-Za-z0-9._ -]',"_",doc.filename)       # no quotes or line breaks in the header
    return Response(content,media_type=content_type,headers={"Content-Disposition":f'attachment; filename="{safe_name}"'})

@app.post("/api/admin/applications/{aid}/decision")
def decide_application(aid:int,data:s.DecisionIn,u:m.User=Depends(allow("admin")),db:Session=Depends(get_db)):
    if data.decision not in {"approved","rejected"}: raise HTTPException(400,"Decision must be approved or rejected")
    a=db.get(m.VendorApplication,aid)
    if not a or a.status!="pending": raise HTTPException(404,"Pending application not found")
    v=a.vendor
    if data.decision=="approved" and data.agreement_valid is None: raise HTTPException(400,"Record agreement validity before approval")
    a.status=data.decision; a.decision_remarks=data.remarks.strip(); a.decision_at=m.now_utc(); v.status=data.decision
    if data.agreement_valid is not None: v.agreement_valid=data.agreement_valid; v.agreement_checked_at=m.now_utc()
    audit(db,u,v,"application_decision",data.decision,(data.remarks.strip()+{None:"",True:" Agreement recorded as valid.",False:" Agreement recorded as not valid."}[data.agreement_valid]).strip(),a.id); notify(db,v.user_id,"application_decision",f"Your vendor application was {data.decision}."); db.commit(); return {"application_id":a.id,"status":a.status,"agreement_valid":v.agreement_valid}

@app.post("/api/admin/vendors/{vid}/participation")
def participation(vid:int,data:s.StatusIn,u:m.User=Depends(allow("admin")),db:Session=Depends(get_db)):
    if data.status not in {"stopped","approved"}: raise HTTPException(400,"Status must be stopped or approved")
    v=db.get(m.Vendor,vid)
    if not v or v.status not in {"approved","stopped"}: raise HTTPException(409,"Vendor must have an approved application")
    v.status=data.status; action="vendor_stopped" if data.status=="stopped" else "vendor_restarted"
    if data.status=="approved": v.status="approved"
    audit(db,u,v,action,data.status); notify(db,v.user_id,action,f"Marketplace participation has been {data.status}."); db.commit(); return {"vendor_id":v.id,"status":v.status}

HISTORY_LABELS={("application_decision","approved"):"Approved",("application_decision","rejected"):"Rejected",("vendor_stopped","stopped"):"Participation stopped",("vendor_restarted","approved"):"Participation restarted"}

@app.get("/api/admin/history")
def admin_history(vendor_id:int|None=None,u:m.User=Depends(allow("admin")),db:Session=Depends(get_db)):
    """Every vendor decision (approved, rejected, stopped, restarted) with who made it, plus when each vendor applied."""
    names={v.id:v.business_name for v in db.scalars(select(m.Vendor))}
    admins={x.id:x.name for x in db.scalars(select(m.User).where(m.User.role=="admin"))}
    stmt=select(m.ApprovalHistory)
    if vendor_id is not None: stmt=stmt.where(m.ApprovalHistory.vendor_id==vendor_id)
    rows=[{"id":x.id,"admin_id":x.admin_id,"vendor_id":x.vendor_id,"vendor_name":names.get(x.vendor_id,f"Vendor #{x.vendor_id}"),"application_id":x.application_id,
           "action":x.action,"decision":x.decision,"label":HISTORY_LABELS.get((x.action,x.decision),x.action.replace("_"," ").capitalize()),
           "by":admins.get(x.admin_id,"University admin"),"remarks":x.remarks,"created_at":x.created_at} for x in db.scalars(stmt)]
    apps=select(m.VendorApplication).join(m.Vendor).where(m.Vendor.status!="listed")
    if vendor_id is not None: apps=apps.where(m.VendorApplication.vendor_id==vendor_id)
    for a in db.scalars(apps):
        rows.append({"id":-a.id,"admin_id":None,"vendor_id":a.vendor_id,"vendor_name":names.get(a.vendor_id,f"Vendor #{a.vendor_id}"),"application_id":a.id,"action":"application_submitted","decision":"submitted",
                     "label":"Application submitted","by":"Vendor","remarks":"","created_at":a.submitted_at})
    registered=select(m.Vendor).where(m.Vendor.status!="listed")
    if vendor_id is not None: registered=registered.where(m.Vendor.id==vendor_id)
    for v in db.scalars(registered):
        rows.append({"id":-1000000-v.id,"admin_id":None,"vendor_id":v.id,"vendor_name":names.get(v.id,f"Vendor #{v.id}"),"application_id":None,"action":"vendor_registered","decision":"registered",
                     "label":"Vendor registered","by":"Vendor","remarks":"","created_at":v.user.created_at})
    rows.sort(key=lambda r:(r["created_at"],r["id"]),reverse=True)
    return rows

@app.get("/api/admin/students")
def admin_students(u:m.User=Depends(allow("admin")),db:Session=Depends(get_db)):
    rows=db.scalars(select(m.User).where(m.User.role=="student",m.User.enabled.is_(True)).order_by(m.User.name)).all()
    return [{"id":x.id,"name":x.name,"email":x.email,"phone":x.phone,"created_at":x.created_at} for x in rows]

@app.post("/api/admin/students",status_code=201)
def admin_create_student(data:s.StudentCreateIn,u:m.User=Depends(allow("admin")),db:Session=Depends(get_db)):
    email=data.email.strip().lower()
    if db.scalar(select(m.User).where(m.User.email==email)): raise HTTPException(409,"An account with this email already exists")
    student=m.User(name=data.name.strip(),email=email,phone=data.phone.strip(),password_hash=hash_password(data.password),role="student",enabled=True)
    db.add(student);db.commit();db.refresh(student)
    return {"id":student.id,"name":student.name,"email":student.email,"phone":student.phone,"enabled":student.enabled}

@app.post("/api/admin/users/{user_id}/password")
def admin_set_password(user_id:int,data:s.AdminSetPasswordIn,u:m.User=Depends(allow("admin")),db:Session=Depends(get_db)):
    """An admin sets a new password for a student or vendor who has forgotten theirs (there is no e-mail reset)."""
    target=db.get(m.User,user_id)
    if not target or target.role not in ("student","vendor"): raise HTTPException(404,"Student or vendor account not found")
    if not target.enabled: raise HTTPException(409,"This account cannot sign in, so its password cannot be changed")
    target.password_hash=hash_password(data.new_password)
    db.add(m.AuditLog(actor_id=u.id,event_type="admin_password_reset",entity_type="user",entity_id=target.id,details=f"Admin set a new password for {target.role} account {target.email}"))
    db.commit()
    return {"ok":True,"message":f"Password changed for {target.email}"}

@app.delete("/api/admin/students/{student_id}")
def admin_remove_student(student_id:int,u:m.User=Depends(allow("admin")),db:Session=Depends(get_db)):
    student=db.get(m.User,student_id)
    if not student or student.role!="student": raise HTTPException(404,"Student account not found")
    student.enabled=False;db.commit()
    return {"id":student.id,"enabled":False,"message":"Student access removed"}

@app.get("/api/admin/metrics")
def admin_metrics(u:m.User=Depends(allow("admin")),db:Session=Depends(get_db)):
    def count(query): return db.scalar(query) or 0
    return {"students":count(select(func.count()).select_from(m.User).where(m.User.role=="student",m.User.enabled.is_(True))),"vendors":count(select(func.count()).select_from(m.Vendor)),"active_vendors":count(select(func.count()).select_from(m.Vendor).where(m.Vendor.status=="approved")),"unapplied_vendors":count(select(func.count()).select_from(m.Vendor).where(m.Vendor.status=="unapplied")),"pending_applications":count(select(func.count()).select_from(m.VendorApplication).where(m.VendorApplication.status=="pending")),"approved_applications":count(select(func.count()).select_from(m.VendorApplication).where(m.VendorApplication.status=="approved")),"rejected_applications":count(select(func.count()).select_from(m.VendorApplication).where(m.VendorApplication.status=="rejected")),"stopped_vendors":count(select(func.count()).select_from(m.Vendor).where(m.Vendor.status=="stopped")),"orders":count(select(func.count()).select_from(m.Order)),"sales":float(count(select(func.sum(m.Order.subtotal)).where(m.Order.status!="cancelled")))}

@app.get("/api/vendor/metrics")
def vendor_metrics(u:m.User=Depends(allow("vendor")),db:Session=Depends(get_db)):
    v=vendor_for(u,db)
    total=db.scalar(select(func.count()).select_from(m.Order).where(m.Order.vendor_id==v.id)) or 0
    pending=db.scalar(select(func.count()).select_from(m.Order).where(m.Order.vendor_id==v.id,m.Order.status.in_(ACTIVE_STATUSES))) or 0
    completed=db.scalar(select(func.count()).select_from(m.Order).where(m.Order.vendor_id==v.id,m.Order.status=="completed")) or 0
    sales=db.scalar(select(func.sum(m.Order.subtotal)).where(m.Order.vendor_id==v.id,m.Order.status!="cancelled")) or 0
    return {"orders":total,"pending_orders":pending,"completed_orders":completed,"sales":float(sales),"products":db.scalar(select(func.count()).select_from(m.Product).where(m.Product.vendor_id==v.id)) or 0,"status":v.status,"delivers_to_bmu":v.delivers_to_bmu,"delivery_points":json.loads(v.delivery_points_json or "[]")}

@app.get("/api/student/metrics")
def student_metrics(u:m.User=Depends(allow("student")),db:Session=Depends(get_db)):
    total=db.scalar(select(func.count()).select_from(m.Order).where(m.Order.student_id==u.id)) or 0
    pending=db.scalar(select(func.count()).select_from(m.Order).where(m.Order.student_id==u.id,m.Order.status.in_(ACTIVE_STATUSES))) or 0
    completed=db.scalar(select(func.count()).select_from(m.Order).where(m.Order.student_id==u.id,m.Order.status=="completed")) or 0
    recent=orders(u,db)[:5]
    return {"total_orders":total,"pending_orders":pending,"completed_orders":completed,"recent_orders":recent}

@app.get("/api/student/recommendations")
def student_recommendations(u:m.User=Depends(allow("student")),db:Session=Depends(get_db)):
    popular=select(m.OrderItem.product_id,func.sum(m.OrderItem.quantity).label("sold")).join(m.Order).where(m.Order.status!="cancelled").group_by(m.OrderItem.product_id).subquery()
    stmt=select(m.Product).join(m.Vendor).outerjoin(popular,popular.c.product_id==m.Product.id).where(m.Vendor.status=="approved",m.Product.menu_status=="published",m.Product.available.is_(True),m.Product.stock>0).order_by(func.coalesce(popular.c.sold,0).desc(),m.Product.id.desc()).limit(8)
    return [product_out(p,db) for p in db.scalars(stmt.options(*WITH_OPTIONS))]

@app.post("/api/vendor/product-images",status_code=201)
async def upload_product_image(file:UploadFile=File(...),u:m.User=Depends(allow("vendor")),db:Session=Depends(get_db)):
    # Approved participation is required before product media is published.
    active_vendor(vendor_for(u,db))
    ext=Path(file.filename or "").suffix.lower()
    signatures={".jpg":b"\xff\xd8\xff",".jpeg":b"\xff\xd8\xff",".png":b"\x89PNG\r\n\x1a\n",".webp":b"RIFF"}
    if ext not in signatures: raise HTTPException(415,"Use a JPG, PNG, or WebP food image")
    data=await file.read(5*1024*1024+1)
    if len(data)>5*1024*1024: raise HTTPException(413,"Food images must be 5 MB or smaller")
    if not data.startswith(signatures[ext]) or (ext==".webp" and data[8:12]!=b"WEBP"): raise HTTPException(415,"Image contents do not match the selected image type")
    name=f"{secrets.token_hex(16)}{ext}"; types={".jpg":"image/jpeg",".jpeg":"image/jpeg",".png":"image/png",".webp":"image/webp"}
    db.add(m.StoredFile(key=f"products/{name}",content_type=types[ext],content=data)); db.commit()
    return {"image_url":f"/api/public/product-images/{name}"}

@app.get("/api/public/product-images/{filename}")
def product_image(filename:str,db:Session=Depends(get_db)):
    import re

    from fastapi.responses import Response
    if not re.fullmatch(r"[a-f0-9]{32}\.(jpg|jpeg|png|webp)",filename): raise HTTPException(404,"Image not found")
    stored=db.get(m.StoredFile,f"products/{filename}")
    if not stored: raise HTTPException(404,"Image not found")
    return Response(stored.content,media_type=stored.content_type,headers={"Cache-Control":"public, max-age=86400"})

@app.get("/api/admin/listings")
def admin_listings(kind:str|None=None,u:m.User=Depends(allow("admin")),db:Session=Depends(get_db)):
    """kind=food lists food only; kind=tech lists laptop and phone services only; no kind lists everything."""
    stmt=select(m.Product).options(*WITH_OPTIONS)
    if kind in ("food","tech"): stmt=stmt.join(m.Category,m.Product.category_id==m.Category.id).where(m.Category.name.in_(FOOD_CATEGORIES if kind=="food" else TECH_CATEGORIES))
    rows=db.scalars(stmt.order_by(m.Product.id.desc()).limit(2000)).all()
    return [{**product_out(p,db),"vendor_status":db.get(m.Vendor,p.vendor_id).status} for p in rows]

@app.post("/api/admin/listings",status_code=201)
def admin_create_listing(data:s.AdminProductIn,u:m.User=Depends(allow("admin")),db:Session=Depends(get_db)):
    vendor=db.get(m.Vendor,data.vendor_id)
    if not vendor: raise HTTPException(404,"Vendor not found")
    category=db.get(m.Category,data.category_id)
    if not category or category.name not in ALLOWED_CATEGORIES: raise HTTPException(422,"Choose an approved category")
    if (vendor.status=="listed")!=(category.name in TECH_CATEGORIES): raise HTTPException(422,"Laptop and phone categories go with listed laptop and phone shops; food categories go with food vendors")
    values=data.model_dump(exclude={"vendor_id"})
    p=m.Product(vendor_id=vendor.id,menu_status="published",**values); db.add(p); db.flush()
    db.add(m.AuditLog(actor_id=u.id,event_type="admin_listing_created",entity_type="product",entity_id=p.id,details="status=published; available=False")); db.commit(); db.refresh(p)
    return {**product_out(p,db),"vendor_status":vendor.status}

@app.patch("/api/admin/listings/{pid}")
def admin_update_listing(pid:int,data:s.AdminListingUpdate,u:m.User=Depends(allow("admin")),db:Session=Depends(get_db)):
    p=db.get(m.Product,pid)
    if not p: raise HTTPException(404,"Listing not found")
    values=data.model_dump(exclude_unset=True,exclude={"available","menu_status","review_note"})
    if values.get("category_id") is not None:
        category=db.get(m.Category,values["category_id"])
        if not category or category.name not in ALLOWED_CATEGORIES: raise HTTPException(422,"Choose an approved category")
    for key,value in values.items(): setattr(p,key,value)
    if data.available is True and (p.price is None or (p.variants and not any(v.available for v in p.variants))): raise HTTPException(422,"A confirmed price and at least one available variant are required")
    if data.available is not None: p.available=data.available
    if data.menu_status is not None: p.menu_status=data.menu_status
    if p.menu_status=="published" and p.available is False: p.available=True
    if p.menu_status in {"review","paused","draft","removed"}: p.available=False
    db.add(m.AuditLog(actor_id=u.id,event_type="admin_listing_review",entity_type="product",entity_id=p.id,details=f"status={p.menu_status}; available={p.available}; note={data.review_note.strip()}")); db.commit()
    return {**product_out(p,db),"vendor_status":db.get(m.Vendor,p.vendor_id).status}

@app.put("/api/admin/listings/{pid}/variants")
def admin_replace_variants(pid:int,data:s.VariantListIn,u:m.User=Depends(allow("admin")),db:Session=Depends(get_db)):
    p=db.get(m.Product,pid)
    if not p: raise HTTPException(404,"Listing not found")
    seen=set()
    for row in data.variants:
        key=row.name.strip().casefold()
        if key in seen: raise HTTPException(422,"Variant names must be unique")
        seen.add(key)
        variant=db.get(m.ProductVariant,row.id) if row.id else None
        if variant and variant.product_id!=p.id: raise HTTPException(422,"A selected variant belongs to another listing")
        if variant is None:
            db.add(m.ProductVariant(product_id=p.id,name=row.name.strip(),price=row.price,dietary=row.dietary,preparation=row.preparation.strip(),portion=row.portion.strip(),available=row.available))
        else:
            for field in ("name","price","dietary","preparation","portion","available"): setattr(variant,field,getattr(row,field))
    for existing in p.variants:
        if existing.name.casefold() not in seen: existing.available=False
    if data.variants: p.price=min(row.price for row in data.variants)
    db.add(m.AuditLog(actor_id=u.id,event_type="admin_variants_updated",entity_type="product",entity_id=p.id,details=f"variants={len(data.variants)}")); db.commit()
    return {**product_out(p,db),"vendor_status":db.get(m.Vendor,p.vendor_id).status}

@app.put("/api/admin/listings/{pid}/addons")
def admin_replace_addons(pid:int,data:s.AddonListIn,u:m.User=Depends(allow("admin")),db:Session=Depends(get_db)):
    p=db.get(m.Product,pid)
    if not p: raise HTTPException(404,"Listing not found")
    seen=set()
    for row in data.addons:
        key=row.name.strip().casefold()
        if key in seen: raise HTTPException(422,"Add-on names must be unique")
        if row.available and row.price is None: raise HTTPException(422,"An add-on needs a confirmed price before it can be enabled")
        seen.add(key)
        addon=db.get(m.ProductAddon,row.id) if row.id else None
        if addon and addon.product_id!=p.id: raise HTTPException(422,"A selected add-on belongs to another listing")
        if addon is None: db.add(m.ProductAddon(product_id=p.id,name=row.name.strip(),price=row.price,available=row.available))
        else: addon.name=row.name.strip(); addon.price=row.price; addon.available=row.available
    for existing in p.addons:
        if existing.name.casefold() not in seen: existing.available=False
    db.add(m.AuditLog(actor_id=u.id,event_type="admin_addons_updated",entity_type="product",entity_id=p.id,details=f"addons={len(data.addons)}")); db.commit()
    return {**product_out(p,db),"vendor_status":db.get(m.Vendor,p.vendor_id).status}
