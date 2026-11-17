"""Initial schema marker retained for existing demo databases.

The first prototype generated this revision from live ORM metadata. Keeping
this revision a no-op makes future fresh installs use the explicit baseline
in 0002 and avoids relying on mutable model code for old migrations.
"""

revision="0001_initial"
down_revision=None
branch_labels=None
depends_on=None

def upgrade(): pass
def downgrade(): pass
