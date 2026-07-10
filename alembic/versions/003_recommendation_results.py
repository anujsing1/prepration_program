"""Adds recommendation_results table for performance tracking."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "recommendation_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("trade_date", sa.Date(), nullable=False),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("company_name", sa.String(200), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("final_score", sa.Float(), nullable=False),
        sa.Column("catalyst_type", sa.String(50), nullable=False),
        sa.Column("catalyst_score", sa.Float(), nullable=False),
        sa.Column("technical_score", sa.Float(), nullable=False),
        sa.Column("sentiment_score", sa.Float(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("direction", sa.String(20), nullable=False),
        sa.Column("direct_company_news", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("close_return_pct", sa.Float(), nullable=True),
        sa.Column("open_to_close_return_pct", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_recommendation_results_trade_date", "recommendation_results", ["trade_date"])
    op.create_index("ix_recommendation_results_symbol", "recommendation_results", ["symbol"])


def downgrade() -> None:
    op.drop_index("ix_recommendation_results_symbol", table_name="recommendation_results")
    op.drop_index("ix_recommendation_results_trade_date", table_name="recommendation_results")
    op.drop_table("recommendation_results")
