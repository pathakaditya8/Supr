"""Add vendor menu variants and priced add-ons."""
import sqlalchemy as sa
from alembic import op

revision = "0004_menu_variants"
down_revision = "0003_order_availability"
branch_labels = None
depends_on = None

def upgrade():
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())
    if "product_variants" not in tables:
        op.create_table("product_variants",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
            sa.Column("name", sa.String(160), nullable=False), sa.Column("price", sa.Numeric(10,2), nullable=False),
            sa.Column("dietary", sa.String(24), nullable=False, server_default="unspecified"),
            sa.Column("preparation", sa.String(80), nullable=False, server_default=""), sa.Column("portion", sa.String(100), nullable=False, server_default=""),
            sa.Column("available", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.UniqueConstraint("product_id", "name", name="uq_variant_product_name"), sa.CheckConstraint("price >= 0", name="ck_variant_price"))
        op.create_index("ix_product_variants_product_id", "product_variants", ["product_id"])
    if "product_addons" not in tables:
        op.create_table("product_addons",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
            sa.Column("name", sa.String(120), nullable=False), sa.Column("price", sa.Numeric(10,2), nullable=True),
            sa.Column("available", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.UniqueConstraint("product_id", "name", name="uq_addon_product_name"), sa.CheckConstraint("price IS NULL OR price >= 0", name="ck_addon_price"))
        op.create_index("ix_product_addons_product_id", "product_addons", ["product_id"])
    cart_cols = {c["name"] for c in sa.inspect(bind).get_columns("cart_items")}
    if "variant_id" not in cart_cols:
        with op.batch_alter_table("cart_items") as batch:
            batch.drop_constraint("uq_cart_product", type_="unique")
            batch.add_column(sa.Column("variant_id", sa.Integer(), nullable=True))
            batch.add_column(sa.Column("addon_ids_json", sa.Text(), nullable=False, server_default="[]"))
            batch.add_column(sa.Column("selection_key", sa.String(500), nullable=False, server_default="base"))
            batch.create_foreign_key("fk_cart_variant", "product_variants", ["variant_id"], ["id"])
            batch.create_unique_constraint("uq_cart_product_selection", ["cart_id", "product_id", "variant_id", "selection_key"])
    order_cols = {c["name"] for c in sa.inspect(bind).get_columns("order_items")}
    with op.batch_alter_table("order_items") as batch:
        if "variant_name" not in order_cols: batch.add_column(sa.Column("variant_name", sa.String(160), nullable=False, server_default=""))
        if "addons_json" not in order_cols: batch.add_column(sa.Column("addons_json", sa.Text(), nullable=False, server_default="[]"))

def downgrade():
    with op.batch_alter_table("order_items") as batch:
        batch.drop_column("addons_json"); batch.drop_column("variant_name")
    with op.batch_alter_table("cart_items") as batch:
        batch.drop_constraint("uq_cart_product_selection", type_="unique"); batch.drop_constraint("fk_cart_variant", type_="foreignkey")
        batch.drop_column("selection_key"); batch.drop_column("addon_ids_json"); batch.drop_column("variant_id")
        batch.create_unique_constraint("uq_cart_product", ["cart_id", "product_id"])
    op.drop_table("product_addons"); op.drop_table("product_variants")
