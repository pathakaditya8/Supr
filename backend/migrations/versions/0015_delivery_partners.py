"""Record how many delivery partners a vendor has when it applies."""
import sqlalchemy as sa
from alembic import op

revision = "0015_delivery_partners"
down_revision = "0014_vendor_phone_length"
branch_labels = None
depends_on = None

def upgrade():
    columns = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("vendor_applications")}
    if "delivery_partners" not in columns:
        with op.batch_alter_table("vendor_applications") as batch:
            batch.add_column(sa.Column("delivery_partners", sa.Integer(), nullable=True))

def downgrade():
    with op.batch_alter_table("vendor_applications") as batch:
        batch.drop_column("delivery_partners")
