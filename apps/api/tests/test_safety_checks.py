import pytest

from the21secrets.db.models import SystemSettings
from the21secrets.safety.checks import (
    SafetyViolation,
    check_budget_ceiling,
    check_budget_increase,
    check_daily_spend_ceiling,
    requires_approval,
)


def _settings(**overrides) -> SystemSettings:
    defaults = dict(
        max_daily_spend_cents=150_000,
        max_campaign_budget_cents=200_000,
        max_budget_increase_pct=20,
        max_new_campaigns_per_day=2,
        max_ads_per_campaign=10,
        require_approval_over_cents=50_000,
    )
    defaults.update(overrides)
    return SystemSettings(**defaults)


def test_budget_within_ceiling_passes() -> None:
    check_budget_ceiling(100_000, _settings())  # does not raise


def test_budget_over_ceiling_raises() -> None:
    with pytest.raises(SafetyViolation):
        check_budget_ceiling(250_000, _settings())


def test_budget_increase_within_pct_passes() -> None:
    check_budget_increase(new_budget_cents=110_000, previous_budget_cents=100_000, settings=_settings())


def test_budget_increase_over_pct_raises() -> None:
    with pytest.raises(SafetyViolation):
        check_budget_increase(new_budget_cents=150_000, previous_budget_cents=100_000, settings=_settings())


def test_budget_decrease_never_raises_regardless_of_magnitude() -> None:
    # Cutting a budget in half is a 50% "change" but never a safety risk.
    check_budget_increase(new_budget_cents=50_000, previous_budget_cents=100_000, settings=_settings())


def test_daily_spend_under_ceiling_passes() -> None:
    check_daily_spend_ceiling(100_000, _settings())


def test_daily_spend_at_or_over_ceiling_raises() -> None:
    with pytest.raises(SafetyViolation):
        check_daily_spend_ceiling(150_000, _settings())
    with pytest.raises(SafetyViolation):
        check_daily_spend_ceiling(200_000, _settings())


def test_requires_approval_over_threshold() -> None:
    settings = _settings()
    assert requires_approval(60_000, settings) is True
    assert requires_approval(40_000, settings) is False


def test_requires_approval_none_budget_never_requires() -> None:
    # Pause/resume/duplicate have no budget_cents — never auto-gated by
    # amount alone (they still go through the mode branch itself).
    assert requires_approval(None, _settings()) is False
