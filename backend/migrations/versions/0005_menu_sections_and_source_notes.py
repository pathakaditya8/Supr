"""Keep vendor-specific menu sections and source review notes."""
import sqlalchemy as sa
from alembic import op

revision = "0005_menu_sections_source_notes"
down_revision = "0004_menu_variants"
branch_labels = None
depends_on = None

def upgrade():
    bind=op.get_bind()
    vendors={c["name"] for c in sa.inspect(bind).get_columns("vendors")}
    with op.batch_alter_table("vendors") as batch:
        if "minimum_order_amount" not in vendors: batch.add_column(sa.Column("minimum_order_amount",sa.Numeric(10,2),nullable=True))
        if "delivery_terms_note" not in vendors: batch.add_column(sa.Column("delivery_terms_note",sa.Text(),nullable=False,server_default=""))
        if "terms_confirmed" not in vendors: batch.add_column(sa.Column("terms_confirmed",sa.Boolean(),nullable=False,server_default=sa.false()))
    products={c["name"] for c in sa.inspect(bind).get_columns("products")}
    with op.batch_alter_table("products") as batch:
        if "menu_section" not in products: batch.add_column(sa.Column("menu_section",sa.String(100),nullable=False,server_default=""))
        if "menu_status" not in products: batch.add_column(sa.Column("menu_status",sa.String(20),nullable=False,server_default="draft"))
        if "price" in products:
            batch.alter_column("price",existing_type=sa.Numeric(10,2),nullable=True)

def downgrade():
    with op.batch_alter_table("products") as batch:
        batch.drop_column("menu_status"); batch.drop_column("menu_section")
    with op.batch_alter_table("vendors") as batch:
        batch.drop_column("terms_confirmed"); batch.drop_column("delivery_terms_note"); batch.drop_column("minimum_order_amount")
