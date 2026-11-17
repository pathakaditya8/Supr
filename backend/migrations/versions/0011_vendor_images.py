"""Shop photo or logo for each vendor."""
import sqlalchemy as sa
from alembic import op

revision = "0011_vendor_images"
down_revision = "0010_tech_categories"
branch_labels = None
depends_on = None

def upgrade():
    cols = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("vendors")}
    if "image_url" not in cols:
        with op.batch_alter_table("vendors") as batch:
            batch.add_column(sa.Column("image_url", sa.String(length=500), nullable=False, server_default=""))

def downgrade():
    with op.batch_alter_table("vendors") as batch:
        batch.drop_column("image_url")
