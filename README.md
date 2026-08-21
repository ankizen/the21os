# The21Secrets AI Ads OS

Private, self-hosted Meta Ads + Google Analytics control platform for The21Secrets, built for Claude to
operate through hard-coded safety guardrails. Not a SaaS product — single admin user, single business.

See [`docs/research/architecture-decision.md`](docs/research/architecture-decision.md) for the full system
design and [`docs/research/stack-decision.md`](docs/research/stack-decision.md) for why each piece of the
stack was chosen. [`docs/research/repository-audit.md`](docs/research/repository-audit.md) documents what
was reused, forked, or rejected from the community Meta/GA4 MCP ecosystem, and why.

## Status

**Phase 5 — Google Analytics 4.** Phases 1–4 (auth, read/write Meta Ads with a real safety pipeline,
creatives) plus real GA4 reporting — landing pages, campaigns, traffic sources, key events, revenue — via
the official Data and Admin API clients, live-verified against the real property. The headline feature:
`core/correlation.py` joins Meta campaign spend/purchases with GA4 sessions/key events by campaign ID (this
account's UTM happens to use the literal Meta campaign ID, confirmed against real data — see
[`GA4_SETUP.md`](GA4_SETUP.md)), surfacing real Meta-vs-GA4 attribution gaps on the Compare page instead of
pretending the two sources agree. Deployed and live at `app.ankithing.com` / `api.ankithing.com`, still
defaulting to `DRY_RUN`. The MCP tool layer doesn't exist yet, and creative performance/fatigue-detection is
Phase 7 (optimization) scope — those stay honest "not connected"/"not built" states, never fake data. See
the phase list in
[`docs/research/architecture-decision.md`](docs/research/architecture-decision.md#module-layout-backend) for
what's next.

## Structure

```
apps/
  web/    Next.js 15+ dashboard (TypeScript, Tailwind, shadcn/ui, TanStack Query/Table, Recharts)
  api/    FastAPI backend (auth, database, safety settings, audit log; MCP server mounts here in Phase 6)
docs/
  research/   Phase 0 discovery: repo audit, stack decision, architecture decision
```

## Local development

Requires Node 22+, Python 3.12+, `uv`, and a local PostgreSQL instance (or run one via
`docker compose up db`).

**Backend**

```bash
cd apps/api
cp .env.example .env   # or hand-write one — see below for required vars
uv run alembic upgrade head
uv run uvicorn the21secrets.app:app --reload
```

Backend `.env` needs: `DATABASE_URL`, `SESSION_SECRET`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`, Meta credentials
(see [`META_SETUP.md`](META_SETUP.md)), and GA4 credentials (see [`GA4_SETUP.md`](GA4_SETUP.md)) — full
list in [`.env.example`](.env.example).

**Frontend**

```bash
cd apps/web
npm install
npm run dev
```

Frontend needs `NEXT_PUBLIC_API_URL` in `.env.local` (defaults to `http://localhost:8000`).

**Tests / lint**

```bash
cd apps/api && uv run pytest -q && uv run ruff check .
cd apps/web && npx tsc --noEmit && npx eslint .
```

## Deployment

Live on Coolify as a single docker-compose Service — see [`COOLIFY.md`](COOLIFY.md) for the actual setup
(project/environment names, domains, env vars) and how to redeploy or reproduce it.

## Security

See [`SECURITY.md`](SECURITY.md).
