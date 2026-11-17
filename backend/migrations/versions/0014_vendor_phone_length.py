"""Allow two phone numbers in a vendor's contact field (PostgreSQL enforces the length)."""
import sqlalchemy as sa
from alembic import op

revision = "0014_vendor_phone_length"
down_revision = "0013_stored_files"
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table("vendors") as batch:
        batch.alter_column("phone", existing_type=sa.String(length=32), type_=sa.String(length=64), existing_nullable=False)

def downgrade():
    with op.batch_alter_table("vendors") as batch:
        batch.alter_column("phone", existing_type=sa.String(length=64), type_=sa.String(length=32), existing_nullable=False)
