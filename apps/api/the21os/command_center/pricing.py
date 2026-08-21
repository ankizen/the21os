"""Per-model $/token rates for estimating Claude API cost. The Messages API
only returns token counts, never a dollar figure, so cost has to be
computed here from published list pricing — update this table if Anthropic
changes pricing or a new model is added."""

# model -> (cents per 1M input tokens, cents per 1M output tokens)
_RATES_PER_MTOK_CENTS: dict[str, tuple[int, int]] = {
    "claude-sonnet-5": (300, 1500),
    "claude-opus-5": (1500, 7500),
    "claude-fable-5": (100, 500),
    "claude-haiku-4-5-20251001": (100, 500),
}
_DEFAULT_RATE = (300, 1500)


def estimate_cost_cents(model: str, input_tokens: int, output_tokens: int) -> int:
    in_rate, out_rate = _RATES_PER_MTOK_CENTS.get(model, _DEFAULT_RATE)
    return round((input_tokens * in_rate + output_tokens * out_rate) / 1_000_000)
