"""Initial database schema."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "articles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("source", sa.String(100), nullable=False),
        sa.Column("url", sa.String(1000), server_default=""),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("run_date", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "sentiment_analysis",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("run_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("symbol", sa.String(20), nullable=False, index=True),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("direction", sa.String(20), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("article_ids", postgresql.JSONB(), server_default="[]"),
    )
    op.create_table(
        "technical_analysis",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("run_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("symbol", sa.String(20), nullable=False, index=True),
        sa.Column("rsi", sa.Float(), nullable=False),
        sa.Column("ema20", sa.Float(), nullable=False),
        sa.Column("ema50", sa.Float(), nullable=False),
        sa.Column("vwap", sa.Float(), nullable=False),
        sa.Column("relative_volume", sa.Float(), nullable=False),
        sa.Column("atr", sa.Float(), nullable=False),
        sa.Column("price_momentum", sa.Float(), nullable=False),
        sa.Column("volume_momentum", sa.Float(), nullable=False),
        sa.Column("technical_score", sa.Float(), nullable=False),
    )
    op.create_table(
        "watchlists",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("run_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("strategy", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "watchlist_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("watchlist_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("watchlists.id")),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("final_score", sa.Float(), nullable=False),
        sa.Column("risk_level", sa.String(20), nullable=False),
        sa.Column("key_catalyst", sa.Text(), nullable=False),
        sa.Column("payload", postgresql.JSONB(), server_default="{}"),
    )
    op.create_table(
        "daily_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("run_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("watchlist_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("watchlists.id")),
        sa.Column("markdown", sa.Text(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("daily_reports")
    op.drop_table("watchlist_entries")
    op.drop_table("watchlists")
    op.drop_table("technical_analysis")
    op.drop_table("sentiment_analysis")
    op.drop_table("articles")
