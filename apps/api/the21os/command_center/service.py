"""The Command Center's Claude tool-use loop — calls the Messages API
directly from our backend with an in-process tool dispatch, per the
architecture decision in docs/research/architecture-decision.md ("the
Command Center does not route through the network MCP transport"). Every
write tool call still goes through safety.pipeline.run_write, so the
mode/ceiling gate is identical to the REST API and MCP paths — Claude
cannot bypass it by asking nicely."""

import json

from anthropic import AsyncAnthropic
from sqlalchemy.ext.asyncio import AsyncSession

from the21os.command_center.pricing import estimate_cost_cents
from the21os.command_center.tools import TOOL_SCHEMAS, ToolContext, run_tool
from the21os.config import get_settings
from the21os.db.models import ClaudeUsage, SystemSettings, User

SYSTEM_PROMPT = (
    "You are the AI Command Center for The21OS, a private Meta Ads + GA4 + WooCommerce "
    "control platform for a single business (The21Secrets). You have tools to read live "
    "Meta Ads, GA4, and WooCommerce order data, and to propose/execute write actions "
    "(pause/resume, budget changes, campaign/ad/creative creation). Every write tool is "
    "gated by a safety pipeline outside your control: hard spend/budget ceilings always "
    "apply, and depending on the current operational mode "
    "(DRY_RUN/READ_ONLY/SUPERVISED/AUTONOMOUS) a write may be simulated, queued "
    "for human approval, or rejected instead of executed immediately — always "
    "report the tool result's actual `status` back to the user rather than "
    "assuming a write happened. Meta's and GA4's purchase/revenue numbers are "
    "pixel/tag-based and can be inflated, delayed, or missed (iOS tracking limits, "
    "cookie blocking, attribution windows); woo_orders_summary's real completed-order "
    "revenue from WooCommerce is the most trustworthy source when they disagree — say so "
    "explicitly if you're using it to override a budget/pause recommendation. Do "
    "arithmetic and comparisons using the numbers the tools return; never invent numbers. "
    "Be concise and concrete — cite real campaign/ad names and figures, not generic advice."
)

_MAX_TOOL_ITERATIONS = 8
_MAX_TOKENS = 4096


async def _client(db: AsyncSession) -> AsyncAnthropic:
    """A key saved in SystemSettings (via the Integrations page) overrides
    the ANTHROPIC_API_KEY env var — lets a short-lived key be rotated
    without a redeploy."""
    row = await db.get(SystemSettings, 1)
    api_key = (row.anthropic_api_key if row else None) or get_settings().anthropic_api_key
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not configured — set it on the Integrations page or in the environment."
        )
    return AsyncAnthropic(api_key=api_key)


async def _log_usage(db: AsyncSession, user: User, model: str, input_tokens: int, output_tokens: int) -> None:
    db.add(
        ClaudeUsage(
            actor=user.email,
            task_type="command_center",
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_cents=estimate_cost_cents(model, input_tokens, output_tokens),
        )
    )
    await db.commit()


async def ask(db: AsyncSession, user: User, messages: list[dict]) -> dict:
    """Runs the tool-use loop to completion and returns the final assistant
    text plus a trace of every tool call made, for the chat UI to render —
    never a raw JSON dump (master prompt SS28). `messages` is the full
    conversation so far in Anthropic Messages API shape; the caller
    (frontend) is responsible for keeping it across turns since this system
    has no persistent chat history store."""
    settings = get_settings()
    client = await _client(db)
    ctx = ToolContext(db=db, user=user)
    conversation = list(messages)
    trace: list[dict] = []

    for _ in range(_MAX_TOOL_ITERATIONS):
        response = await client.messages.create(
            model=settings.anthropic_model,
            max_tokens=_MAX_TOKENS,
            system=SYSTEM_PROMPT,
            tools=TOOL_SCHEMAS,
            messages=conversation,
        )
        await _log_usage(db, user, response.model, response.usage.input_tokens, response.usage.output_tokens)

        assistant_content = [block.model_dump() for block in response.content]
        conversation.append({"role": "assistant", "content": assistant_content})

        tool_uses = [b for b in response.content if b.type == "tool_use"]
        if not tool_uses:
            text = "".join(b.text for b in response.content if b.type == "text")
            return {"reply": text, "trace": trace, "messages": conversation}

        tool_results = []
        for block in tool_uses:
            result = await run_tool(block.name, block.input, ctx)
            trace.append({"tool": block.name, "input": block.input, "result": result})
            tool_results.append(
                {"type": "tool_result", "tool_use_id": block.id, "content": json.dumps(result, default=str)}
            )
        conversation.append({"role": "user", "content": tool_results})

    return {
        "reply": "Stopped after too many tool calls in a row — try a narrower question.",
        "trace": trace,
        "messages": conversation,
    }
