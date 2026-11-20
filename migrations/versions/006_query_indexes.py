"""Agrego índices para las consultas de posts y comentarios."""

from alembic import op

revision = "006_query_indexes"
down_revision = "005_realtime"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index("idx_posts_category_id", "posts", ["category_id"])
    op.create_index("idx_posts_author_id", "posts", ["author_id"])
    op.create_index("idx_comments_post_id", "comments", ["post_id"])
    op.create_index("idx_comments_user_id", "comments", ["user_id"])
    op.create_index("idx_post_tags_tag_id", "post_tags", ["tag_id"])
    op.execute("CREATE INDEX idx_posts_status_published_at ON posts(status, published_at DESC)")


def downgrade():
    for name in (
        "idx_posts_status_published_at",
        "idx_post_tags_tag_id",
        "idx_comments_user_id",
        "idx_comments_post_id",
        "idx_posts_author_id",
        "idx_posts_category_id",
    ):
        op.drop_index(name)
