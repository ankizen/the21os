import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Enum, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from the21os.db.base import Base


class OperationalMode(str, enum.Enum):
    DRY_RUN = "DRY_RUN"
    READ_ONLY = "READ_ONLY"
    SUPERVISED = "SUPERVISED"
    AUTONOMOUS = "AUTONOMOUS"


class User(Base):
    """The single admin user. Multiple rows are supported by the schema but
    this system is designed for exactly one — see architecture-decision.md."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    totp_secret: Mapped[str | None] = mapped_column(String(64), default=None)
    totp_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)


class SystemSettings(Base):
    """Singleton row (id always 1) holding operational mode + hard safety
    ceilings. Enforced in code by the safety layer (added in a later phase),
    never trusted from a prompt — see master prompt SS17-18."""

    __tablename__ = "system_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    operational_mode: Mapped[OperationalMode] = mapped_column(
        Enum(OperationalMode), default=OperationalMode.DRY_RUN
    )
    # Overrides the ANTHROPIC_API_KEY env var when set — lets a short-lived
    # key be rotated from the Integrations page without a redeploy.
    anthropic_api_key: Mapped[str | None] = mapped_column(String(255), default=None)
    max_daily_spend_cents: Mapped[int] = mapped_column(Integer, default=150_000)
    max_campaign_budget_cents: Mapped[int] = mapped_column(Integer, default=200_000)
    max_budget_increase_pct: Mapped[int] = mapped_column(Integer, default=20)
    max_new_campaigns_per_day: Mapped[int] = mapped_column(Integer, default=2)
    max_ads_per_campaign: Mapped[int] = mapped_column(Integer, default=10)
    require_approval_over_cents: Mapped[int] = mapped_column(Integer, default=50_000)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class AuditLog(Base):
    """Append-only record of every meaningful action, per master prompt SS20.
    `params_json`/`before_json`/`after_json` must already be secret-redacted
    by the caller (see audit/redact.py) before being written here."""

    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    request_id: Mapped[str] = mapped_column(String(64), index=True)
    actor: Mapped[str] = mapped_column(String(255))
    source: Mapped[str] = mapped_column(String(64))
    action: Mapped[str] = mapped_column(String(128), index=True)
    entity: Mapped[str | None] = mapped_column(String(64), default=None)
    entity_id: Mapped[str | None] = mapped_column(String(128), default=None)
    params_json: Mapped[dict | None] = mapped_column(JSON, default=None)
    before_json: Mapped[dict | None] = mapped_column(JSON, default=None)
    after_json: Mapped[dict | None] = mapped_column(JSON, default=None)
    decision_reason: Mapped[str | None] = mapped_column(String(512), default=None)
    success: Mapped[bool] = mapped_column(Boolean)


class ApprovalStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class ApprovalRequest(Base):
    """A write action queued for human sign-off — created whenever the
    safety pipeline decides a write needs approval (SUPERVISED mode, or
    AUTONOMOUS mode over the require_approval_over threshold). Approving
    replays `params_json` through the same executor that would have run
    immediately, so it's audited identically either way."""

    __tablename__ = "approval_requests"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    action: Mapped[str] = mapped_column(String(128))
    entity: Mapped[str | None] = mapped_column(String(64), default=None)
    entity_id: Mapped[str | None] = mapped_column(String(128), default=None)
    summary: Mapped[str] = mapped_column(String(512))
    params_json: Mapped[dict] = mapped_column(JSON)
    before_json: Mapped[dict | None] = mapped_column(JSON, default=None)
    status: Mapped[ApprovalStatus] = mapped_column(
        Enum(ApprovalStatus), default=ApprovalStatus.PENDING, index=True
    )
    requested_by: Mapped[str] = mapped_column(String(255))
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    decided_by: Mapped[str | None] = mapped_column(String(255), default=None)


class WordPressConnection(Base):
    """Singleton row (id always 1) holding the WordPress/WooCommerce
    connection — editable from the Integrations page so credentials can be
    set/rotated without a redeploy, same pattern as SystemSettings.anthropic_api_key.
    app_password is a WordPress Application Password (not the real login
    password); woo_consumer_key/secret are WooCommerce REST API keys."""

    __tablename__ = "wordpress_connection"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    site_url: Mapped[str | None] = mapped_column(String(512), default=None)
    app_username: Mapped[str | None] = mapped_column(String(255), default=None)
    app_password: Mapped[str | None] = mapped_column(String(255), default=None)
    woo_consumer_key: Mapped[str | None] = mapped_column(String(255), default=None)
    woo_consumer_secret: Mapped[str | None] = mapped_column(String(255), default=None)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ClaudeUsage(Base):
    """Per-request Claude API usage, for cost observability (master prompt
    SS31). cost_cents is computed at write time from a hardcoded per-model
    rate table (command_center/pricing.py) since the API itself only
    returns token counts, never a dollar figure."""

    __tablename__ = "claude_usage"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    actor: Mapped[str] = mapped_column(String(255))
    task_type: Mapped[str] = mapped_column(String(64))
    model: Mapped[str] = mapped_column(String(64))
    input_tokens: Mapped[int] = mapped_column(Integer)
    output_tokens: Mapped[int] = mapped_column(Integer)
    cost_cents: Mapped[int] = mapped_column(Integer)
