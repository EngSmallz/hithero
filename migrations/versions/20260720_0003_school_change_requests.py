"""Add moderated school-change requests and public visibility state."""

import sqlalchemy as sa
from alembic import op


revision = "20260720_0003_school_change_requests"
down_revision = "20260720_0002_verified_registration_snapshot"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "teacher_list",
        sa.Column(
            "school_change_pending",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.create_table(
        "school_change_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("old_state", sa.String(), nullable=False),
        sa.Column("old_county", sa.String(), nullable=False),
        sa.Column("old_district", sa.String(), nullable=False),
        sa.Column("old_school", sa.String(), nullable=False),
        sa.Column("proposed_state", sa.String(), nullable=False),
        sa.Column("proposed_county", sa.String(), nullable=False),
        sa.Column("proposed_district", sa.String(), nullable=False),
        sa.Column("proposed_school", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("reviewed_by", sa.Integer(), nullable=True),
    )


def downgrade():
    op.drop_table("school_change_requests")
    op.drop_column("teacher_list", "school_change_pending")
