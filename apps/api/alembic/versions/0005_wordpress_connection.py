"""add wordpress_connection table

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-21
"""

import sqlalchemy as sa

from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "wordpress_connection",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("site_url", sa.String(512), nullable=True),
        sa.Column("app_username", sa.String(255), nullable=True),
        sa.Column("app_password", sa.String(255), nullable=True),
        sa.Column("woo_consumer_key", sa.String(255), nullable=True),
        sa.Column("woo_consumer_secret", sa.String(255), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("wordpress_connection")
