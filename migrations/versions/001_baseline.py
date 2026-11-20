"""Baseline de Pulse."""

from alembic import op
from pathlib import Path

revision = "001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    source = Path(__file__).resolve().parents[1] / "baseline.sql"
    for statement in source.read_text(encoding="utf-8").split(";"):
        if statement.strip():
            op.execute(statement)


def downgrade() -> None:
    for table in ("comments", "post_tags", "posts", "tags", "categories", "users"):
        op.drop_table(table)
