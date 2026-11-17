"""Illustrative stock photos per dish type and diet, with photographer credit."""
import sqlalchemy as sa
from alembic import op

revision = "0012_dish_photos"
down_revision = "0011_vendor_images"
branch_labels = None
depends_on = None

def upgrade():
    if "dish_photos" in sa.inspect(op.get_bind()).get_table_names():
        return
    op.create_table("dish_photos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("key", sa.String(length=80), nullable=False, unique=True),
        sa.Column("query", sa.String(length=160), nullable=False, server_default=""),
        sa.Column("image_url", sa.String(length=800), nullable=False),
        sa.Column("photographer", sa.String(length=160), nullable=False),
        sa.Column("photographer_url", sa.String(length=500), nullable=False),
        sa.Column("photo_page_url", sa.String(length=500), nullable=False),
        sa.Column("source", sa.String(length=40), nullable=False, server_default="Unsplash"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True))

def downgrade():
    op.drop_table("dish_photos")
