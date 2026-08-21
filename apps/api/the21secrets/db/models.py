import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Enum, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from the21secrets.db.base import Base


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
