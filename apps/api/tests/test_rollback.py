import uuid
from types import SimpleNamespace

import pytest

from the21secrets.safety import rollback as rollback_module
from the21secrets.safety.pipeline import WriteOutcome
from the21secrets.safety.rollback import NotReversible, rollback


class FakeDb:
    def __init__(self, entry: object) -> None:
        self._entry = entry

    async def get(self, _model, _id):
        return self._entry


def _entry(**overrides) -> SimpleNamespace:
    defaults = dict(
        id=uuid.uuid4(),
        success=True,
        entity="campaign",
        entity_id="123",
        action="campaign.pause",
        params_json={"campaign_id": "123"},
        before_json=None,
        after_json=None,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


@pytest.mark.parametrize(
    ("action", "expected_inverse"),
    [
        ("campaign.pause", "campaign.resume"),
        ("campaign.resume", "campaign.pause"),
        ("adset.pause", "adset.resume"),
        ("adset.resume", "adset.pause"),
        ("ad.pause", "ad.resume"),
        ("ad.resume", "ad.pause"),
    ],
)
async def test_pause_resume_routes_to_inverse_action(
    monkeypatch: pytest.MonkeyPatch, action: str, expected_inverse: str
) -> None:
    captured = {}

    async def fake_run_write(_db, req):
        captured["action"] = req.action
        captured["params"] = req.params
        return WriteOutcome(status="executed", result={})

    monkeypatch.setattr(rollback_module, "run_write", fake_run_write)
    entry = _entry(action=action)
    await rollback(FakeDb(entry), entry.id, actor="test@example.com", source="test")

    assert captured["action"] == expected_inverse
    assert captured["params"] == entry.params_json


async def test_budget_rollback_uses_before_json(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = {}

    async def fake_run_write(_db, req):
        captured["params"] = req.params
        captured["budget_cents"] = req.budget_cents
        return WriteOutcome(status="executed", result={})

    monkeypatch.setattr(rollback_module, "run_write", fake_run_write)
    entry = _entry(
        action="campaign.budget_update",
        before_json={"daily_budget": "10000"},
        after_json={"daily_budget": "15000"},
    )
    await rollback(FakeDb(entry), entry.id, actor="test@example.com", source="test")

    assert captured["params"]["daily_budget_cents"] == 10000
    assert captured["budget_cents"] == 10000


async def test_create_is_not_reversible() -> None:
    entry = _entry(action="campaign.create")
    with pytest.raises(NotReversible):
        await rollback(FakeDb(entry), entry.id, actor="test@example.com", source="test")


async def test_failed_action_is_not_reversible() -> None:
    entry = _entry(action="campaign.pause", success=False)
    with pytest.raises(NotReversible):
        await rollback(FakeDb(entry), entry.id, actor="test@example.com", source="test")


async def test_budget_rollback_without_before_json_is_not_reversible() -> None:
    entry = _entry(action="campaign.budget_update", before_json=None)
    with pytest.raises(NotReversible):
        await rollback(FakeDb(entry), entry.id, actor="test@example.com", source="test")
