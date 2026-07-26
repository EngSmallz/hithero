"""Record the reviewed production schema baseline.

This revision intentionally performs no DDL. It must be stamped only after the
production SQL Server schema has been exported and compared with the ORM model
inventory, as documented in migrations/README.md.
"""

revision = "20260711_0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
