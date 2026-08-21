"""add approval_requests table

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-21
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels = None
depends_on = None

_approval_status = postgresql.ENUM(
    "PENDING", "APPROVED", "REJECTED", "EXPIRED", name="approvalstatus", create_type=False
)


def upgrade() -> None:
    _approval_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "approval_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("action", sa.String(128), nullable=False),
        sa.Column("entity", sa.String(64), nullable=True),
        sa.Column("entity_id", sa.String(128), nullable=True),
        sa.Column("summary", sa.String(512), nullable=False),
        sa.Column("params_json", postgresql.JSON, nullable=False),
        sa.Column("before_json", postgresql.JSON, nullable=True),
        sa.Column("status", _approval_status, nullable=False, server_default="PENDING"),
        sa.Column("requested_by", sa.String(255), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decided_by", sa.String(255), nullable=True),
    )
    op.create_index("ix_approval_requests_created_at", "approval_requests", ["created_at"])
    op.create_index("ix_approval_requests_status", "approval_requests", ["status"])


def downgrade() -> None:
    op.drop_table("approval_requests")
    _approval_status.drop(op.get_bind(), checkfirst=True)
