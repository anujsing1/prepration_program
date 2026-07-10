"""Add first_seen_at to articles."""

from alembic import op
import sqlalchemy as sa


revision = "005_article_first_seen"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "articles",
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("articles", "first_seen_at")
