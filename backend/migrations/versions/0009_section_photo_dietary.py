"""Section photos per diet, so vegetarian items in mixed sections never show meat."""
import sqlalchemy as sa
from alembic import op

revision = "0009_section_photo_dietary"
down_revision = "0008_menu_section_photos"
branch_labels = None
depends_on = None

def upgrade():
    cols = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("menu_section_photos")}
    with op.batch_alter_table("menu_section_photos") as batch:
        if "dietary" not in cols:
            batch.add_column(sa.Column("dietary", sa.String(length=24), nullable=False, server_default="any"))
        batch.drop_constraint("uq_section_photo", type_="unique")
        batch.create_unique_constraint("uq_section_photo_diet", ["vendor_id", "menu_section", "dietary"])

def downgrade():
    with op.batch_alter_table("menu_section_photos") as batch:
        batch.drop_constraint("uq_section_photo_diet", type_="unique")
        batch.create_unique_constraint("uq_section_photo", ["vendor_id", "menu_section"])
        batch.drop_column("dietary")
