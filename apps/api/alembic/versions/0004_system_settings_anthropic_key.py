"""add anthropic_api_key to system_settings

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-21
"""

import sqlalchemy as sa

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("system_settings", sa.Column("anthropic_api_key", sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column("system_settings", "anthropic_api_key")
