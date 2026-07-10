"""Adds ranking audit columns and table."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "technical_analysis",
        sa.Column("previous_close", sa.Float(), server_default="0", nullable=False),
    )
    op.add_column(
        "technical_analysis",
        sa.Column("score_breakdown", postgresql.JSONB(), server_default="{}", nullable=False),
    )
    op.create_table(
        "ranking_audit",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("run_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("technical_score", sa.Float(), nullable=False),
        sa.Column("catalyst_score", sa.Float(), nullable=False),
        sa.Column("sentiment_score", sa.Float(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("freshness_score", sa.Float(), nullable=False),
        sa.Column("priority_score", sa.Float(), nullable=False),
        sa.Column("final_score", sa.Float(), nullable=False),
        sa.Column("score_breakdown", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_ranking_audit_run_date", "ranking_audit", ["run_date"])
    op.create_index("ix_ranking_audit_symbol", "ranking_audit", ["symbol"])


def downgrade() -> None:
    op.drop_index("ix_ranking_audit_symbol", table_name="ranking_audit")
    op.drop_index("ix_ranking_audit_run_date", table_name="ranking_audit")
    op.drop_table("ranking_audit")
    op.drop_column("technical_analysis", "score_breakdown")
    op.drop_column("technical_analysis", "previous_close")
