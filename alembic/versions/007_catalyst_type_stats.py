"""Create catalyst_type_stats table."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "007_catalyst_type_stats"
down_revision = "006_catalyst_taxonomy"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "catalyst_type_stats",
        sa.Column("catalyst_code", sa.String(length=100), nullable=False),
        sa.Column("first_seen", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=False),
        sa.Column("occurrence_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("accepted_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rejected_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "average_score",
            sa.Numeric(precision=10, scale=2),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "average_tradability",
            sa.Numeric(precision=10, scale=2),
            nullable=False,
            server_default="0",
        ),
        sa.PrimaryKeyConstraint("catalyst_code"),
    )
    op.create_index(
        "ix_catalyst_type_stats_occurrence_count",
        "catalyst_type_stats",
        ["occurrence_count"],
    )


def downgrade() -> None:
    op.drop_index("ix_catalyst_type_stats_occurrence_count", table_name="catalyst_type_stats")
    op.drop_table("catalyst_type_stats")
