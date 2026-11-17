"""Add phone contact field for student accounts."""
import sqlalchemy as sa
from alembic import op

revision = "0006_student_accounts"
down_revision = "0005_menu_sections_source_notes"
branch_labels = None
depends_on = None

def upgrade():
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("users")}
    if "phone" not in columns:
        with op.batch_alter_table("users") as batch:
            batch.add_column(sa.Column("phone", sa.String(length=32), nullable=False, server_default=""))

def downgrade():
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("users")}
    if "phone" in columns:
        with op.batch_alter_table("users") as batch:
            batch.drop_column("phone")
