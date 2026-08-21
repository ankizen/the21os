"""Hard safety ceilings — never bypassed by operational mode. These run
before the mode branch in safety/pipeline.py; a rejection here is final
regardless of DRY_RUN/SUPERVISED/AUTONOMOUS."""

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from the21os.db.models import AuditLog, SystemSettings


class SafetyViolation(Exception):
    """A hard ceiling was exceeded — the write is rejected outright, no mode
    can override this."""


async def count_campaigns_created_today(db: AsyncSession) -> int:
    start_of_day = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    result = await db.execute(
        select(func.count()).where(
            AuditLog.action == "campaign.create",
            AuditLog.success.is_(True),
            AuditLog.created_at >= start_of_day,
        )
    )
    return result.scalar_one()


def check_budget_ceiling(budget_cents: int, settings: SystemSettings) -> None:
    if budget_cents > settings.max_campaign_budget_cents:
        raise SafetyViolation(
            f"Budget ₹{budget_cents / 100:.2f} exceeds the max campaign budget ceiling "
            f"of ₹{settings.max_campaign_budget_cents / 100:.2f} (see Rules)."
        )


def check_budget_increase(
    new_budget_cents: int, previous_budget_cents: int, settings: SystemSettings
) -> None:
    if new_budget_cents <= previous_budget_cents:
        return  # decreasing or unchanged budget is never a safety risk
    increase_pct = (new_budget_cents - previous_budget_cents) / previous_budget_cents * 100
    if increase_pct > settings.max_budget_increase_pct:
        raise SafetyViolation(
            f"Budget increase of {increase_pct:.1f}% exceeds the max allowed "
            f"{settings.max_budget_increase_pct}% per change (see Rules)."
        )


async def check_new_campaign_quota(db: AsyncSession, settings: SystemSettings) -> None:
    created_today = await count_campaigns_created_today(db)
    if created_today >= settings.max_new_campaigns_per_day:
        raise SafetyViolation(
            f"Already created {created_today} campaign(s) today — "
            f"at the daily limit of {settings.max_new_campaigns_per_day} (see Rules)."
        )


def check_daily_spend_ceiling(today_spend_cents: int, settings: SystemSettings) -> None:
    if today_spend_cents >= settings.max_daily_spend_cents:
        raise SafetyViolation(
            f"Today's spend (₹{today_spend_cents / 100:.2f}) has already reached the daily "
            f"ceiling of ₹{settings.max_daily_spend_cents / 100:.2f} — no spend-increasing "
            f"actions allowed until tomorrow (see Rules)."
        )


def check_max_ads_per_campaign(current_ad_count: int, settings: SystemSettings) -> None:
    if current_ad_count >= settings.max_ads_per_campaign:
        raise SafetyViolation(
            f"This campaign already has {current_ad_count} ad(s) — "
            f"at the limit of {settings.max_ads_per_campaign} per campaign (see Rules)."
        )


def requires_approval(budget_cents: int | None, settings: SystemSettings) -> bool:
    """Only meaningful in AUTONOMOUS mode — SUPERVISED always requires
    approval regardless of amount, and actions with no budget_cents (pause,
    resume, duplicate) have no amount to gate on."""
    if budget_cents is None:
        return False
    return budget_cents > settings.require_approval_over_cents
