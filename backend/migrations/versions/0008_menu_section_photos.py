"""Illustrative stock photos per vendor menu section, with photographer credit."""
import sqlalchemy as sa
from alembic import op

revision = "0008_menu_section_photos"
down_revision = "0007_delivery_locations"
branch_labels = None
depends_on = None

def upgrade():
    if "menu_section_photos" in sa.inspect(op.get_bind()).get_table_names():
        return
    op.create_table(
        "menu_section_photos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("vendor_id", sa.Integer(), sa.ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("menu_section", sa.String(length=100), nullable=False),
        sa.Column("image_url", sa.String(length=800), nullable=False),
        sa.Column("photographer", sa.String(length=160), nullable=False),
        sa.Column("photographer_url", sa.String(length=500), nullable=False),
        sa.Column("photo_page_url", sa.String(length=500), nullable=False),
        sa.Column("source", sa.String(length=40), nullable=False, server_default="Unsplash"),
        sa.Column("search_query", sa.String(length=160), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("vendor_id", "menu_section", name="uq_section_photo"),
    )

def downgrade():
    op.drop_table("menu_section_photos")
