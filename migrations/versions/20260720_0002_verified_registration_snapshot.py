"""Store approved registration details for profile creation and school locking."""

import sqlalchemy as sa
from alembic import op


revision = "20260720_0002_verified_registration_snapshot"
down_revision = "20260711_0001_baseline"
branch_labels = None
depends_on = None


def upgrade():
    for name in (
        "registration_name",
        "registration_state",
        "registration_county",
        "registration_district",
        "registration_school",
    ):
        op.add_column(
            "registered_users",
            sa.Column(name, sa.String(), nullable=True),
        )


def downgrade():
    for name in (
        "registration_school",
        "registration_district",
        "registration_county",
        "registration_state",
        "registration_name",
    ):
        op.drop_column("registered_users", name)
