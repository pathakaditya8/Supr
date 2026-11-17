from datetime import UTC, datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, LargeBinary, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def now_utc(): return datetime.now(UTC)

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(32), default="")
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    vendor: Mapped["Vendor"] = relationship(back_populates="user", uselist=False)

class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (CheckConstraint("name IN ('Meals and Main Course','Snacks and Quick Bites','Beverages','Desserts and Sweets','Bakery and Confectionery','Fast Food','Healthy Food','Combos and Special Offers','Laptop Repair','Laptops and Accessories','Phone Repair','Phones and Accessories')", name="ck_categories_allowed"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)

class Vendor(Base):
    __tablename__ = "vendors"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    business_name: Mapped[str] = mapped_column(String(160))
    phone: Mapped[str] = mapped_column(String(64), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    delivers_to_bmu: Mapped[bool] = mapped_column(Boolean, default=False)
    agreement_valid: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    agreement_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    minimum_order_amount: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    delivery_terms_note: Mapped[str] = mapped_column(Text, default="")
    terms_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    delivery_points_json: Mapped[str] = mapped_column(Text, default="[]")
    image_url: Mapped[str] = mapped_column(String(500), default="")  # shop photo or logo, e.g. /vendors/dominos-logo.png
    user: Mapped[User] = relationship(back_populates="vendor")
    application: Mapped["VendorApplication"] = relationship(back_populates="vendor", uselist=False)

class VendorApplication(Base):
    __tablename__ = "vendor_applications"
    id: Mapped[int] = mapped_column(primary_key=True)
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"), unique=True)
    business_address: Mapped[str] = mapped_column(Text)
    contact_person: Mapped[str] = mapped_column(String(120))
    agreement_reference: Mapped[str] = mapped_column(String(160), default="")
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    decision_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decision_remarks: Mapped[str] = mapped_column(Text, default="")
    vendor: Mapped[Vendor] = relationship(back_populates="application")

class StoredFile(Base):
    """Uploaded documents and food photos, kept in the database so they survive hosts with temporary disks."""
    __tablename__ = "stored_files"
    key: Mapped[str] = mapped_column(String(200), primary_key=True)
    content_type: Mapped[str] = mapped_column(String(100))
    content: Mapped[bytes] = mapped_column(LargeBinary)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

class VendorDocument(Base):
    __tablename__ = "vendor_documents"
    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("vendor_applications.id"), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    stored_path: Mapped[str] = mapped_column(String(500))
    content_type: Mapped[str] = mapped_column(String(100))
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

class Product(Base):
    __tablename__ = "products"
    __table_args__ = (CheckConstraint("price IS NULL OR price >= 0",name="ck_product_price"), CheckConstraint("stock >= 0",name="ck_product_stock"), CheckConstraint("dietary IN ('vegetarian','non_vegetarian','vegan','unspecified')", name="ck_product_dietary"), CheckConstraint("spice_level IS NULL OR spice_level IN ('mild','medium','hot')", name="ck_product_spice"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"), index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), index=True)
    name: Mapped[str] = mapped_column(String(160), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    price: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    stock: Mapped[int] = mapped_column(Integer, default=0)
    available: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    image_url: Mapped[str] = mapped_column(String(500), default="")
    dietary: Mapped[str] = mapped_column(String(24), default="vegetarian")
    spice_level: Mapped[str | None] = mapped_column(String(12), nullable=True)
    allergens: Mapped[str] = mapped_column(String(500), default="")
    portion: Mapped[str] = mapped_column(String(100), default="")
    prep_time_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    menu_section: Mapped[str] = mapped_column(String(100), default="")
    menu_status: Mapped[str] = mapped_column(String(20), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    variants: Mapped[list["ProductVariant"]] = relationship(cascade="all, delete-orphan")
    addons: Mapped[list["ProductAddon"]] = relationship(cascade="all, delete-orphan")

class ProductVariant(Base):
    """A priced, selectable combination (e.g. Steam · Veg Momos)."""
    __tablename__ = "product_variants"
    __table_args__ = (UniqueConstraint("product_id", "name", name="uq_variant_product_name"), CheckConstraint("price >= 0", name="ck_variant_price"))
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    price: Mapped[float] = mapped_column(Numeric(10, 2))
    dietary: Mapped[str] = mapped_column(String(24), default="unspecified")
    preparation: Mapped[str] = mapped_column(String(80), default="")
    portion: Mapped[str] = mapped_column(String(100), default="")
    available: Mapped[bool] = mapped_column(Boolean, default=True)

class ProductAddon(Base):
    __tablename__ = "product_addons"
    __table_args__ = (UniqueConstraint("product_id", "name", name="uq_addon_product_name"), CheckConstraint("price IS NULL OR price >= 0", name="ck_addon_price"))
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    price: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    available: Mapped[bool] = mapped_column(Boolean, default=True)

class Cart(Base):
    __tablename__ = "carts"
    __table_args__ = (UniqueConstraint("student_id", name="uq_cart_student"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    vendor_id: Mapped[int | None] = mapped_column(ForeignKey("vendors.id"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)
    items: Mapped[list["CartItem"]] = relationship(cascade="all, delete-orphan")

class CartItem(Base):
    __tablename__ = "cart_items"
    __table_args__ = (UniqueConstraint("cart_id", "product_id", "variant_id", "selection_key", name="uq_cart_product_selection"), CheckConstraint("quantity > 0"))
    id: Mapped[int] = mapped_column(primary_key=True)
    cart_id: Mapped[int] = mapped_column(ForeignKey("carts.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    variant_id: Mapped[int | None] = mapped_column(ForeignKey("product_variants.id"), nullable=True)
    addon_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    selection_key: Mapped[str] = mapped_column(String(500), default="base")
    quantity: Mapped[int] = mapped_column(Integer)

class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"), index=True)
    status: Mapped[str] = mapped_column(String(24), default="pending", index=True)
    campus_delivery: Mapped[bool] = mapped_column(Boolean)
    delivery_location: Mapped[str] = mapped_column(String(160), default="")
    delivery_stage: Mapped[str] = mapped_column(String(24), default="")
    subtotal: Mapped[float] = mapped_column(Numeric(10, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    items: Mapped[list["OrderItem"]] = relationship(cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = "order_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    product_name: Mapped[str] = mapped_column(String(160))
    unit_price: Mapped[float] = mapped_column(Numeric(10, 2))
    quantity: Mapped[int] = mapped_column(Integer)
    was_available: Mapped[bool] = mapped_column(Boolean, default=True)
    variant_name: Mapped[str] = mapped_column(String(160), default="")
    addons_json: Mapped[str] = mapped_column(Text, default="[]")

class ApprovalHistory(Base):
    __tablename__ = "approval_history"
    id: Mapped[int] = mapped_column(primary_key=True)
    admin_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"), index=True)
    application_id: Mapped[int | None] = mapped_column(ForeignKey("vendor_applications.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(40))
    decision: Mapped[str] = mapped_column(String(24))
    remarks: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column(primary_key=True)
    recipient_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(40))
    message: Mapped[str] = mapped_column(String(500))
    read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(60))
    entity_type: Mapped[str] = mapped_column(String(40))
    entity_id: Mapped[int] = mapped_column(Integer)
    details: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

class MenuSectionPhoto(Base):
    """Illustrative stock photo shown for a vendor's menu section when an item has no photo of its own."""
    __tablename__ = "menu_section_photos"
    __table_args__ = (UniqueConstraint("vendor_id", "menu_section", "dietary", name="uq_section_photo_diet"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id", ondelete="CASCADE"), index=True)
    menu_section: Mapped[str] = mapped_column(String(100))
    # "vegetarian", "non_vegetarian" or "any": mixed sections get one photo per diet so a veg item never shows meat.
    dietary: Mapped[str] = mapped_column(String(24), default="any")
    image_url: Mapped[str] = mapped_column(String(800))
    photographer: Mapped[str] = mapped_column(String(160))
    photographer_url: Mapped[str] = mapped_column(String(500))
    photo_page_url: Mapped[str] = mapped_column(String(500))
    source: Mapped[str] = mapped_column(String(40), default="Unsplash")
    search_query: Mapped[str] = mapped_column(String(160), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class DishPhoto(Base):
    """Illustrative stock photo for a dish type and diet, e.g. "kathi-roll|vegetarian" (see app/dish_photos.py)."""
    __tablename__ = "dish_photos"
    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(80), unique=True)
    query: Mapped[str] = mapped_column(String(160), default="")
    image_url: Mapped[str] = mapped_column(String(800))
    photographer: Mapped[str] = mapped_column(String(160))
    photographer_url: Mapped[str] = mapped_column(String(500))
    photo_page_url: Mapped[str] = mapped_column(String(500))
    source: Mapped[str] = mapped_column(String(40), default="Unsplash")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
