from the21os.command_center.pricing import estimate_cost_cents
from the21os.command_center.tools import TOOL_SCHEMAS, run_tool


def test_estimate_cost_cents_known_model() -> None:
    assert estimate_cost_cents("claude-sonnet-5", 1_000_000, 0) == 300
    assert estimate_cost_cents("claude-sonnet-5", 0, 1_000_000) == 1500


def test_estimate_cost_cents_unknown_model_falls_back_to_default_rate() -> None:
    assert estimate_cost_cents("some-future-model", 1_000_000, 1_000_000) == 300 + 1500


def test_tool_schemas_are_all_dispatchable() -> None:
    # Every declared tool must have a matching executor, or Claude could
    # request a tool call that silently 404s at dispatch time.
    from the21os.command_center.tools import _DISPATCH

    schema_names = {t["name"] for t in TOOL_SCHEMAS}
    assert schema_names == set(_DISPATCH.keys())


async def test_run_tool_unknown_name_returns_error_not_exception() -> None:
    result = await run_tool("not_a_real_tool", {}, ctx=None)
    assert "error" in result
