"""initial schema: users, system_settings, audit_log

Revision ID: 0001
Revises:
Create Date: 2026-08-21
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels = None
depends_on = None

_operational_mode = postgresql.ENUM(
    "DRY_RUN", "READ_ONLY", "SUPERVISED", "AUTONOMOUS", name="operationalmode"
)


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("totp_secret", sa.String(64), nullable=True),
        sa.Column("totp_enabled", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    _operational_mode.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "system_settings",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("operational_mode", _operational_mode, nullable=False, server_default="DRY_RUN"),
        sa.Column("max_daily_spend_cents", sa.Integer, nullable=False, server_default="150000"),
        sa.Column("max_campaign_budget_cents", sa.Integer, nullable=False, server_default="200000"),
        sa.Column("max_budget_increase_pct", sa.Integer, nullable=False, server_default="20"),
        sa.Column("max_new_campaigns_per_day", sa.Integer, nullable=False, server_default="2"),
        sa.Column("max_ads_per_campaign", sa.Integer, nullable=False, server_default="10"),
        sa.Column("require_approval_over_cents", sa.Integer, nullable=False, server_default="50000"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("request_id", sa.String(64), nullable=False),
        sa.Column("actor", sa.String(255), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("action", sa.String(128), nullable=False),
        sa.Column("entity", sa.String(64), nullable=True),
        sa.Column("entity_id", sa.String(128), nullable=True),
        sa.Column("params_json", postgresql.JSON, nullable=True),
        sa.Column("before_json", postgresql.JSON, nullable=True),
        sa.Column("after_json", postgresql.JSON, nullable=True),
        sa.Column("decision_reason", sa.String(512), nullable=True),
        sa.Column("success", sa.Boolean, nullable=False),
    )
    op.create_index("ix_audit_log_created_at", "audit_log", ["created_at"])
    op.create_index("ix_audit_log_request_id", "audit_log", ["request_id"])
    op.create_index("ix_audit_log_action", "audit_log", ["action"])


def downgrade() -> None:
    op.drop_table("audit_log")
    op.drop_table("system_settings")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    _operational_mode.drop(op.get_bind(), checkfirst=True)
