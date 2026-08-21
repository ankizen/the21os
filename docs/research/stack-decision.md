# Stack Decision

For each layer: choice, why, alternative considered, why rejected. Based on [repository-audit.md](./repository-audit.md) and verified current docs (see [architecture-decision.md](./architecture-decision.md) for topology).

## Frontend

**Chosen: Next.js 15 (App Router) + React + TypeScript + Tailwind CSS + shadcn/ui + TanStack Query + TanStack Table + Recharts**

- Why: shadcn/ui gives copy-in-repo components (no black-box design-system dependency to fight for the "premium terminal" look in §5); TanStack Query/Table are the standard for dense, sortable, server-paginated tables which is most of this UI; Recharts covers the spend/ROAS/CPA time-series charts without a heavier viz library; Next.js has first-class Coolify build support (Nixpacks/Dockerfile detection) and SSR isn't needed here but the App Router's layout/streaming model still gives the cleanest file-per-route structure for ~10 dashboard pages.
- Alternative considered: plain Vite + React SPA. Rejected — no material benefit for a single-user internal app, and Next.js's built-in routing/layouts remove boilerplate we'd otherwise hand-roll.
- Alternative considered: Remix. Rejected — smaller ecosystem overlap with shadcn/ui and Coolify deploy examples; no functional advantage here.

## Backend

**Chosen: FastAPI + Pydantic v2 + SQLAlchemy 2.0 (async) + Alembic + PostgreSQL (asyncpg)**

- Why: matches the master prompt's own preference (§7) and is the natural home for the MCP server (same language as the official Meta/GA4 SDKs, avoids a Python↔Node boundary). Async SQLAlchemy + Alembic is the standard, well-understood migration story.
- Alternative considered: Django + DRF. Rejected — heavier, and its ORM's sync-by-default model fights the async Meta/GA4 clients we're wrapping.
- Alternative considered: Node/Express backend to match the frontend's language. Rejected — would force a second Meta/GA4 client implementation in JS when the best-audited reference repos and official SDKs are Python-first (`facebook-python-business-sdk`, `google-analytics-data`), and would still need a Python process for the MCP server regardless.

## Database

**Chosen: PostgreSQL only — for application data *and* audit log.**

- Why: the master prompt allows SQLite "for local dev or simple audit logs" but explicitly asks us to evaluate whether Postgres should hold production audit data too (§16). Running two database engines for one system (SQLite for audit, Postgres for everything else) is unnecessary split-brain for a single-user private app — one connection pool, one backup story, one migration tool. Dev environment uses the same Postgres via `docker-compose` rather than maintaining a second SQLite code path.
- Alternative considered: SQLite for audit log, Postgres for app data. Rejected — no operational benefit, doubles backup/migration surface for zero gain at this scale (single account, low write volume).

## MCP Server

**Chosen: official `mcp` Python SDK (`modelcontextprotocol/python-sdk`), bundled FastMCP/MCPServer decorator API — exact class name and pinned version resolved at Phase 1 setup time.**

- Why: it's the canonical, Anthropic-recognized SDK, actively maintained (pushed 2026-08-20), and already includes decorator-based tool registration plus a `TokenVerifier`/`AuthSettings` pattern for Bearer-token auth over Streamable HTTP (confirmed against `py.sdk.modelcontextprotocol.io/run/authorization`) — exactly what a single-user Bearer-token-protected server needs, with no extra dependency.
- **Open item, not guessed today**: the SDK has an in-flight breaking change — `FastMCP` renamed to `MCPServer`, old import path removed with no shim, somewhere around v2.0. At Phase 1 kickoff we check the actually-installed latest version and write against its real API rather than assuming either name now.
- Alternative considered: standalone `jlowin/fastmcp` (what `redhat-data-and-ai/template-mcp-server` uses). Rejected as the default — it's a fine package, but it's an extra third-party dependency on top of the official SDK for features (its OAuth module, proxying, OpenAPI generation) we don't need: this system uses one hard-coded Bearer token for a single admin user, not OAuth. Revisit only if the official SDK's bundled auth genuinely can't do what we need.

## Meta Ads Client

**Chosen: official `facebook-business` SDK (v26.0.0) as the transport layer, with our own `meta/` module wrapping it — architecture patterns borrowed from `bertramdev/MetaAdsMCP` (tools/-by-domain split, dry-run mode, archive-not-delete, PAUSED-by-default), version-guard concept from `armavita-meta-ads-mcp` (hard-block Advantage+ Shopping/App create/update at the code layer, matching the now-fully-enforced May 2026 API restriction).**

- Why: see repository-audit.md — every community MCP server we found is either license-encumbered (BSL/AGPL), has an unresolved security-scanner finding (pipeboard), or has aspirational-not-real safety code (konquest). None is fit to run as a dependency; all are useful as reference only. The official SDK is the only piece we take directly.
- Alternative considered: raw Graph API HTTP calls (no SDK). Rejected — the official SDK already handles request signing, model marshalling, and pagination cursors; reimplementing that is pure waste per the master prompt's own rule (§12) against rewriting the whole Graph API layer without a specific reason.

## GA4 Client

**Chosen: official `google-analytics-data` + `google-analytics-admin` Python clients directly, with tool-naming/API-call conventions from `googleanalytics/google-analytics-mcp` (the canonical official reference) and the dual-auth (service-account JSON + ADC, auto-detected) pattern from `surendranb/google-analytics-mcp`.**

- Why: official reference confirms ADC is the modern-preferred path but service-account JSON is still fully supported (no deprecation found) — supporting both, auto-detected by credential shape, costs little and matches how Coolify secrets are typically injected (a JSON file path) versus a personal dev machine (`gcloud auth application-default login`).
- Alternative considered: forking `surendranb/google-analytics-mcp` wholesale as our GA4 server. Rejected — we're building one unified MCP server per the master prompt's Architecture E, not running a second standalone MCP process; its "skills" self-healing playbook idea is worth porting later as a doc/prompt asset, not as a second server.

## Authentication (dashboard)

**Chosen: email + password (bcrypt) login for a single seeded admin user, server-side session via short-lived JWT + httpOnly signed cookie, optional TOTP 2FA.**

- Why: this is a single-user private app (§22 explicitly rules out multi-tenant RBAC). Password + optional TOTP is the simplest option that's still genuinely secure for a system that can spend real ad money, without standing up an external OAuth provider or magic-link email infra for one person.
- Alternative considered: OAuth via Google. Rejected — adds an external dependency and redirect flow for zero benefit when there's exactly one user, who already controls the server's env vars.
- Alternative considered: passkeys only. Rejected — best long-term, but adds WebAuthn implementation complexity for a v1 that doesn't need it; can be added later without restructuring anything.

## Scheduler

**Chosen: APScheduler (`AsyncIOScheduler`) running in-process inside the FastAPI app.**

- Why: the master prompt explicitly rejects a "giant workflow engine" (§30) and Redis is explicitly "only if actually needed" (§24/§43). A single low-frequency polling job (check Meta/GA4 metrics, run anomaly detection) has no throughput requirement that justifies Celery+Redis; APScheduler with a Postgres-backed job store (already have Postgres) is enough and removes an entire infrastructure component.
- Alternative considered: Celery + Redis + beat. Rejected — solves a scaling problem we don't have.
- Alternative considered: Coolify's own cron/scheduled-command feature calling a script. Considered viable but rejected as primary mechanism because job state (last-run, in-flight anomaly detection results) needs to live in the same process/DB transaction as the rest of the app; kept as a documented fallback if in-process scheduling ever proves unreliable under Coolify restarts.

## Observability

**Chosen: structured JSON logs to stdout (consumed by Coolify's log viewer) + the Postgres audit log table for business-meaningful events. No external APM/tracing product.**

- Why: §35 explicitly says "avoid unnecessary observability products." stdout structured logging is what Coolify/Docker already capture natively; the audit log (§20) already covers every meaningful action with request IDs. Adding Sentry/Datadog/etc. for a single-user system is infrastructure the master prompt tells us not to add.
- Alternative considered: OpenTelemetry + a hosted backend. Rejected — real value only appears at a scale/team size this system doesn't have.

## Deployment

See [architecture-decision.md](./architecture-decision.md) for full container topology. Summary: **Coolify, one Docker Compose Service (Next.js + FastAPI-with-mounted-MCP as sibling containers on Coolify's auto-shared network) + one Coolify-managed PostgreSQL resource. No Redis, no Kubernetes, no fourth container.**
