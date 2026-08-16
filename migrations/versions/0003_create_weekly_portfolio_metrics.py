"""Create weekly_portfolio_metrics table in the primary database.

Moves aggregate usage counters off the separate local-only SQLite file
(previously /tmp/poopsense-portfolio-metrics.sqlite3, which doesn't survive
Railway restarts/redeploys and isn't backed up) and into the same Postgres
database everything else already uses in production.
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_portfolio_metrics"
down_revision = "0002_add_pet_type"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "weekly_portfolio_metrics",
        sa.Column("week_start", sa.String(length=10), primary_key=True),
        sa.Column("completed_screenings", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("vet_searches", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table("weekly_portfolio_metrics")
