"""Preserve listing availability across order cancellation/restock."""
import sqlalchemy as sa
from alembic import op

revision="0003_order_availability"
down_revision="0002_food_only"
branch_labels=None
depends_on=None

def upgrade():
    bind=op.get_bind()
    columns={c["name"] for c in sa.inspect(bind).get_columns("order_items")}
    if "was_available" not in columns:
        op.add_column("order_items",sa.Column("was_available",sa.Boolean(),nullable=False,server_default=sa.true()))
    checks={c.get("name") for c in sa.inspect(bind).get_check_constraints("products")}
    missing={"ck_product_price":"price >= 0","ck_product_stock":"stock >= 0"}
    if any(name not in checks for name in missing):
        with op.batch_alter_table("products") as batch:
            for name,expression in missing.items():
                if name not in checks: batch.create_check_constraint(name,expression)

def downgrade():
    op.drop_column("order_items","was_available")
