"""Add catalyst quality score columns for backtest readiness."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: str | None = "003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "recommendation_results",
        sa.Column("magnitude_score", sa.Float(), nullable=True),
    )
    op.add_column(
        "recommendation_results",
        sa.Column("materiality_score", sa.Float(), nullable=True),
    )
    op.add_column(
        "recommendation_results",
        sa.Column("tradability_score", sa.Float(), nullable=True),
    )
    op.add_column(
        "recommendation_results",
        sa.Column("effective_catalyst_score", sa.Float(), nullable=True),
    )
    op.add_column(
        "recommendation_results",
        sa.Column("catalyst_magnitude", sa.String(length=20), nullable=True),
    )

    op.add_column("ranking_audit", sa.Column("catalyst_type", sa.String(length=50), nullable=True))
    op.add_column("ranking_audit", sa.Column("magnitude_score", sa.Float(), nullable=True))
    op.add_column("ranking_audit", sa.Column("materiality_score", sa.Float(), nullable=True))
    op.add_column("ranking_audit", sa.Column("tradability_score", sa.Float(), nullable=True))
    op.add_column(
        "ranking_audit",
        sa.Column("effective_catalyst_score", sa.Float(), nullable=True),
    )
    op.add_column(
        "ranking_audit",
        sa.Column("catalyst_magnitude", sa.String(length=20), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("ranking_audit", "catalyst_magnitude")
    op.drop_column("ranking_audit", "effective_catalyst_score")
    op.drop_column("ranking_audit", "tradability_score")
    op.drop_column("ranking_audit", "materiality_score")
    op.drop_column("ranking_audit", "magnitude_score")
    op.drop_column("ranking_audit", "catalyst_type")

    op.drop_column("recommendation_results", "catalyst_magnitude")
    op.drop_column("recommendation_results", "effective_catalyst_score")
    op.drop_column("recommendation_results", "tradability_score")
    op.drop_column("recommendation_results", "materiality_score")
    op.drop_column("recommendation_results", "magnitude_score")
