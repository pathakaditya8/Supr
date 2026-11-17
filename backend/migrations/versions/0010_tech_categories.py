"""Add laptop and phone repair / sales categories alongside the food categories.

Replaces the food-only CHECK constraint on categories with one that also allows the
four new categories, then inserts them.
"""
import sqlalchemy as sa
from alembic import op

revision = "0010_tech_categories"
down_revision = "0009_section_photo_dietary"
branch_labels = None
depends_on = None

FOOD = ["Meals and Main Course", "Snacks and Quick Bites", "Beverages", "Desserts and Sweets",
        "Bakery and Confectionery", "Fast Food", "Healthy Food", "Combos and Special Offers"]
TECH = ["Laptop Repair", "Laptops and Accessories", "Phone Repair", "Phones and Accessories"]

def _check(names):
    return "name IN (" + ",".join("'" + n + "'" for n in names) + ")"

def _swap_constraint(old, new, names):
    bind = op.get_bind()
    checks = {c.get("name") for c in sa.inspect(bind).get_check_constraints("categories")}
    if bind.dialect.name == "sqlite":
        # SQLite cannot alter a CHECK constraint: rebuild the small categories table.
        op.execute("PRAGMA foreign_keys=OFF")
        op.execute(f"CREATE TABLE categories_new (id INTEGER NOT NULL, name VARCHAR(80) NOT NULL, PRIMARY KEY (id), "
                   f"CONSTRAINT {new} CHECK ({_check(names)}), UNIQUE (name))")
        op.execute("INSERT INTO categories_new (id, name) SELECT id, name FROM categories")
        op.execute("DROP TABLE categories")
        op.execute("ALTER TABLE categories_new RENAME TO categories")
        op.execute("PRAGMA foreign_keys=ON")
    else:
        if old in checks: op.drop_constraint(old, "categories", type_="check")
        op.create_check_constraint(new, "categories", _check(names))

def upgrade():
    _swap_constraint("ck_categories_food_only", "ck_categories_allowed", FOOD + TECH)
    bind = op.get_bind()
    existing = {row[0] for row in bind.execute(sa.text("SELECT name FROM categories"))}
    for name in TECH:
        if name not in existing:
            bind.execute(sa.text("INSERT INTO categories(name) VALUES (:name)"), {"name": name})

def downgrade():
    op.get_bind().execute(sa.text("DELETE FROM categories WHERE name IN :names").bindparams(sa.bindparam("names", expanding=True)), {"names": TECH})
    _swap_constraint("ck_categories_allowed", "ck_categories_food_only", FOOD)
