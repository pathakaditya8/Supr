"""Store vendor drop-off choices and order gate arrival notices."""
import sqlalchemy as sa
from alembic import op

revision = "0007_delivery_locations"
down_revision = "0006_student_accounts"
branch_labels = None
depends_on = None

def upgrade():
    bind = op.get_bind()
    vendor_cols = {column["name"] for column in sa.inspect(bind).get_columns("vendors")}
    if "delivery_points_json" not in vendor_cols:
        with op.batch_alter_table("vendors") as batch:
            batch.add_column(sa.Column("delivery_points_json", sa.Text(), nullable=False, server_default="[]"))
    order_cols = {column["name"] for column in sa.inspect(bind).get_columns("orders")}
    with op.batch_alter_table("orders") as batch:
        if "delivery_location" not in order_cols:
            batch.add_column(sa.Column("delivery_location", sa.String(length=160), nullable=False, server_default=""))
        if "delivery_stage" not in order_cols:
            batch.add_column(sa.Column("delivery_stage", sa.String(length=24), nullable=False, server_default=""))

def downgrade():
    with op.batch_alter_table("orders") as batch:
        batch.drop_column("delivery_stage")
        batch.drop_column("delivery_location")
    with op.batch_alter_table("vendors") as batch:
        batch.drop_column("delivery_points_json")
