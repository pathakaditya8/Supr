"""Enforce the food-only marketplace and add food listing details."""
import sqlalchemy as sa
from alembic import op
from app.database import Base
from app import models  # noqa: F401 - registers metadata

revision="0002_food_only"
down_revision="0001_initial"
branch_labels=None
depends_on=None

FOOD_CATEGORIES=["Meals and Main Course","Snacks and Quick Bites","Beverages","Desserts and Sweets","Bakery and Confectionery","Fast Food","Healthy Food","Combos and Special Offers"]

def upgrade():
    bind=op.get_bind()
    inspector=sa.inspect(bind)
    if not inspector.has_table("users"):
        Base.metadata.create_all(bind=bind)
        return

    # Migrate the prototype catalog: discard non-food demo listings and keep
    # the old Food & Beverages listings as Meals and Main Course.
    if inspector.has_table("categories") and inspector.has_table("products"):
        bind.execute(sa.text("DELETE FROM products WHERE category_id IN (SELECT id FROM categories WHERE name NOT IN :names)").bindparams(sa.bindparam("names", expanding=True)), {"names": FOOD_CATEGORIES+["Food & Beverages"]})
        bind.execute(sa.text("UPDATE categories SET name='Meals and Main Course' WHERE name='Food & Beverages'"))
        bind.execute(sa.text("DELETE FROM categories WHERE name NOT IN :names").bindparams(sa.bindparam("names", expanding=True)), {"names": FOOD_CATEGORIES})
        existing={row[0] for row in bind.execute(sa.text("SELECT name FROM categories"))}
        for name in FOOD_CATEGORIES:
            if name not in existing: bind.execute(sa.text("INSERT INTO categories(name) VALUES (:name)"), {"name":name})

    columns={c["name"] for c in sa.inspect(bind).get_columns("products")}
    additions=[
      sa.Column("dietary",sa.String(24),nullable=False,server_default="vegetarian"),
      sa.Column("spice_level",sa.String(12),nullable=True),
      sa.Column("allergens",sa.String(500),nullable=False,server_default=""),
      sa.Column("portion",sa.String(100),nullable=False,server_default=""),
      sa.Column("prep_time_minutes",sa.Integer(),nullable=True),
    ]
    for column in additions:
        if column.name not in columns: op.add_column("products",column)

    if inspector.has_table("order_items") and "was_available" not in {c["name"] for c in sa.inspect(bind).get_columns("order_items")}:
        op.add_column("order_items",sa.Column("was_available",sa.Boolean(),nullable=False,server_default=sa.true()))

    category_checks={c.get("name") for c in sa.inspect(bind).get_check_constraints("categories")}
    if "ck_categories_food_only" not in category_checks:
        with op.batch_alter_table("categories") as batch:
            batch.create_check_constraint("ck_categories_food_only","name IN ('Meals and Main Course','Snacks and Quick Bites','Beverages','Desserts and Sweets','Bakery and Confectionery','Fast Food','Healthy Food','Combos and Special Offers')")
    product_checks={c.get("name") for c in sa.inspect(bind).get_check_constraints("products")}
    if not {"ck_product_dietary","ck_product_spice","ck_product_price","ck_product_stock"}.issubset(product_checks):
        with op.batch_alter_table("products") as batch:
            if "ck_product_dietary" not in product_checks: batch.create_check_constraint("ck_product_dietary","dietary IN ('vegetarian','non_vegetarian','vegan','unspecified')")
            if "ck_product_spice" not in product_checks: batch.create_check_constraint("ck_product_spice","spice_level IS NULL OR spice_level IN ('mild','medium','hot')")
            if "ck_product_price" not in product_checks: batch.create_check_constraint("ck_product_price","price >= 0")
            if "ck_product_stock" not in product_checks: batch.create_check_constraint("ck_product_stock","stock >= 0")

def downgrade():
    raise RuntimeError("Food-only catalog migration is intentionally irreversible because it removes non-food listings.")
