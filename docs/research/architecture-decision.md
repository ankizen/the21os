# Architecture Decision

## System Diagram

```
                              CLAUDE
              ┌─────────────────┴─────────────────┐
              │                                    │
   Claude API (Messages API,                Claude Code / Claude Desktop
   tool-use loop, called BY                 (STDIO, personal dev/debug
   our backend — Command Center)             access to the same tools)
              │                                    │
              ▼                                    ▼
   ┌───────────────────────────────────────────────────────┐
   │              THE21SECRETS BACKEND (FastAPI)            │
   │  ┌────────────┐  ┌────────────┐  ┌──────────────────┐ │
   │  │ REST API   │  │ MCP server │  │ Scheduler         │ │
   │  │ (dashboard,│  │ (mounted   │  │ (APScheduler,     │ │
   │  │ auth,      │  │ at /mcp,   │  │  in-process)       │ │
   │  │ audit,     │  │ Streamable │  │                    │ │
   │  │ config)    │  │ HTTP +     │  │                    │ │
   │  │            │  │ STDIO      │  │                    │ │
   │  │            │  │ entrypoint)│  │                    │ │
   │  └─────┬──────┘  └─────┬──────┘  └────────┬───────────┘ │
   │        └───────────────┼──────────────────┘             │
   │                        ▼                                │
   │           core/ · safety/ · audit/  (shared)             │
   │                        ▼                                │
   │              ┌─────────┴─────────┐                      │
   │              ▼                   ▼                      │
   │         meta/ module         ga4/ module                │
   │    facebook-business SDK   google-analytics-data/admin  │
   └───────────────┼───────────────────┼──────────────────────┘
                    ▼                   ▼
            Meta Marketing API    Google Analytics API
                    │
                    ▼
              PostgreSQL (app state + audit log)

   ┌───────────────────────────────────────────────────────┐
   │         THE21SECRETS FRONTEND (Next.js, separate       │
   │         container, calls the REST API only)            │
   └───────────────────────────────────────────────────────┘
```

## Key Decision: the Command Center does not route through the network MCP transport

The master prompt's own diagram (§2) shows `Claude → Control App → MCP → Meta/GA4`. The literal reading — the web dashboard's "Ask The21Secrets AI" box calling out to Claude, which calls back into our MCP server over HTTP — has a real problem: the Claude **API's** MCP connector (`mcp_toolset`) calls the MCP URL *from Anthropic's servers*, not from our backend. That would require our MCP endpoint to be publicly internet-reachable, which is a bigger attack surface than a system that can spend real ad money should have by default.

**Decision**: the MCP tool functions are the single source of truth for every Meta/GA4 operation, but they're plain async Python functions in `meta/`, `ga4/`, `optimization/`, decorated once for MCP registration. The Command Center's tool-use loop calls the Claude Messages API directly from our backend with a standard custom `tools` list (not the remote `mcp_toolset` connector) and dispatches tool-call results to those same functions **in-process** — no network hop, no public exposure required for the primary usage path. The MCP server (STDIO, and Streamable HTTP behind Bearer auth on the Coolify-internal network) exists for the secondary path: connecting Claude Code or Claude Desktop directly to the same tools for ad-hoc personal debugging, per the master prompt's requirement that Claude get access "through our own self-hosted tools/MCP implementation." If STDIO/direct Claude Desktop access is ever needed from outside the home network, the Streamable HTTP endpoint can be put behind Coolify's domain+TLS deliberately, as an explicit opt-in — not by default.

This keeps §2's architecture intact (MCP is real, it's the tool contract, Claude reasons over it) while keeping the actually-networked attack surface as small as the master prompt's own security priorities (§50: "Security is more important than convenience") demand.

## Container Topology (Coolify)

Per the Coolify verification research: a single `docker-compose.yml` deployed as **one Coolify Service** gets containers on an auto-shared Docker network for free — no manual network wiring needed, unlike separate standalone "Application" resources.

- **Container 1 — `frontend`**: Next.js, built standalone, calls `backend` over the internal network; only this one gets a public Coolify domain + TLS.
- **Container 2 — `backend`**: FastAPI, with the MCP server mounted as an ASGI sub-app at `/mcp` inside the same process (per the Coolify research: "embedding the MCP server as a library inside FastAPI is simpler and fully compatible with a single-resource deployment"). Gets a public domain only if/when the Streamable HTTP MCP path is deliberately opened up for remote Claude Desktop access; otherwise internal-only.
- **Database — Coolify one-click PostgreSQL resource** in the same project (not a third container in the compose file, so it gets Coolify's own backup tooling).
- **No Redis, no separate MCP container, no Kubernetes.** Matches §24/§43 directly.

This is Architecture choice **B (two containers)** from §24, resolved: frontend and backend+MCP combined into one backend process, plus the managed database.

## Module Layout (backend)

```
the21secrets/
    app/                # FastAPI app assembly, ASGI mount of MCP sub-app
    api/                # REST routers: dashboard, campaigns, actions, rules, integrations, system
    core/                # shared config, calculations (CPA/ROAS/CTR/CPC/CPM), formatters
    db/                  # SQLAlchemy models, Alembic migrations
    auth/                # session/password/TOTP
    safety/              # budget.py, rate_limiter.py, quota.py, approval queue
    audit/               # audit.py (JSONL-shaped rows in Postgres), rollback journal, secret redaction
    meta/                # client.py (wraps facebook-business SDK), campaigns.py, adsets.py, ads.py,
                          # creatives.py, insights.py, targeting.py, guards.py (ASC/AAC block, per armavita pattern)
    ga4/                 # client.py, reports.py, realtime.py, schema.py
    optimization/        # compare.py, winners_losers.py, fatigue.py — deterministic, no Claude calls
    mcp/                 # tool registration (decorates functions from meta/ga4/optimization),
                          # stdio_entry.py, http asgi app
    command_center/      # Claude Messages API tool-use loop for the dashboard's AI chat
    jobs/                # APScheduler job definitions
```

Every write path (Meta or GA4) goes through the same sequence regardless of caller (REST API, MCP tool, or Command Center tool-use loop), matching §17:

```
validate (Pydantic) → safety check (safety/) → authorization/mode check (DRY_RUN/READ_ONLY/SUPERVISED/AUTONOMOUS)
    → execute (meta/ or ga4/) → verify → audit (audit/)
```

## Operational Modes

`DRY_RUN → READ_ONLY → SUPERVISED → AUTONOMOUS`, stored as a system setting in Postgres, enforced in the shared safety-check function — not per-caller, so Claude (via any of the three entry points above) is bound by the same gate the dashboard UI shows. Even in `AUTONOMOUS`, the hard-coded ceilings (`MAX_DAILY_SPEND`, `MAX_NEW_CAMPAIGNS_PER_DAY`, etc.) still apply; the mode only controls whether human approval is required, never whether the ceilings apply.

## What This Explicitly Does Not Include

Per §43 and confirmed by nothing in the research contradicting it: no Kubernetes, no message bus, no Redis, no multi-tenant RBAC, no vector database, no agent swarm, no second AI model. One Claude, one Postgres, three runtime containers (frontend, backend, db-resource).
