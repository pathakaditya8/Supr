"""Keep uploaded documents and food photos in the database."""
import sqlalchemy as sa
from alembic import op

revision = "0013_stored_files"
down_revision = "0012_dish_photos"
branch_labels = None
depends_on = None

def upgrade():
    if "stored_files" in sa.inspect(op.get_bind()).get_table_names():
        return
    op.create_table("stored_files",
        sa.Column("key", sa.String(length=200), primary_key=True),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("content", sa.LargeBinary(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True))

def downgrade():
    op.drop_table("stored_files")
