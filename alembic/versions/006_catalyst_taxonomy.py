"""Create catalyst taxonomy tables and seed initial data."""

from __future__ import annotations

import json
from pathlib import Path

import sqlalchemy as sa
from alembic import op

revision = "006_catalyst_taxonomy"
down_revision = "005_article_first_seen"
branch_labels = None
depends_on = None


def _seed_path() -> Path:
    return Path(__file__).resolve().parents[2] / "config" / "catalyst_taxonomy_seed.json"


def upgrade() -> None:
    op.create_table(
        "catalyst_taxonomy",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("catalyst_code", sa.String(length=100), nullable=False),
        sa.Column("catalyst_name", sa.String(length=255), nullable=False),
        sa.Column("parent_category", sa.String(length=100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("bullish_weight", sa.Numeric(precision=10, scale=2), nullable=False, server_default="0"),
        sa.Column("bearish_weight", sa.Numeric(precision=10, scale=2), nullable=False, server_default="0"),
        sa.Column("tradability_weight", sa.Numeric(precision=10, scale=2), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("catalyst_code"),
    )
    op.create_index("ix_catalyst_taxonomy_parent_category", "catalyst_taxonomy", ["parent_category"])
    op.create_index("ix_catalyst_taxonomy_is_active", "catalyst_taxonomy", ["is_active"])

    op.create_table(
        "catalyst_taxonomy_pending",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("proposed_code", sa.String(length=100), nullable=False),
        sa.Column("proposed_name", sa.String(length=255), nullable=False),
        sa.Column("parent_category", sa.String(length=100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("example_headline", sa.Text(), nullable=True),
        sa.Column("example_summary", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Numeric(precision=5, scale=4), nullable=False, server_default="0"),
        sa.Column("occurrence_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("first_seen", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="PENDING"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_catalyst_taxonomy_pending_proposed_code", "catalyst_taxonomy_pending", ["proposed_code"])
    op.create_index("ix_catalyst_taxonomy_pending_status", "catalyst_taxonomy_pending", ["status"])
    op.create_index(
        "ix_catalyst_taxonomy_pending_occurrence_count",
        "catalyst_taxonomy_pending",
        ["occurrence_count"],
    )

    seed_file = _seed_path()
    if not seed_file.exists():
        return

    payload = json.loads(seed_file.read_text(encoding="utf-8"))
    conn = op.get_bind()
    for entry in payload.get("entries", []):
        conn.execute(
            sa.text(
                """
                INSERT INTO catalyst_taxonomy (
                    id, catalyst_code, catalyst_name, parent_category, description,
                    bullish_weight, bearish_weight, tradability_weight, is_active
                ) VALUES (
                    gen_random_uuid(), :catalyst_code, :catalyst_name, :parent_category, :description,
                    :bullish_weight, :bearish_weight, :tradability_weight, :is_active
                )
                ON CONFLICT (catalyst_code) DO NOTHING
                """
            ),
            {
                "catalyst_code": entry["catalyst_code"],
                "catalyst_name": entry["catalyst_name"],
                "parent_category": entry.get("parent_category"),
                "description": entry.get("description"),
                "bullish_weight": entry.get("bullish_weight", 0),
                "bearish_weight": entry.get("bearish_weight", 0),
                "tradability_weight": entry.get("tradability_weight", 0),
                "is_active": entry.get("is_active", True),
            },
        )


def downgrade() -> None:
    op.drop_index("ix_catalyst_taxonomy_pending_occurrence_count", table_name="catalyst_taxonomy_pending")
    op.drop_index("ix_catalyst_taxonomy_pending_status", table_name="catalyst_taxonomy_pending")
    op.drop_index("ix_catalyst_taxonomy_pending_proposed_code", table_name="catalyst_taxonomy_pending")
    op.drop_table("catalyst_taxonomy_pending")
    op.drop_index("ix_catalyst_taxonomy_is_active", table_name="catalyst_taxonomy")
    op.drop_index("ix_catalyst_taxonomy_parent_category", table_name="catalyst_taxonomy")
    op.drop_table("catalyst_taxonomy")
