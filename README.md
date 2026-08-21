# The21Secrets AI Ads OS

Private, self-hosted Meta Ads + Google Analytics control platform for The21Secrets, built for Claude to
operate through hard-coded safety guardrails. Not a SaaS product — single admin user, single business.

See [`docs/research/architecture-decision.md`](docs/research/architecture-decision.md) for the full system
design and [`docs/research/stack-decision.md`](docs/research/stack-decision.md) for why each piece of the
stack was chosen. [`docs/research/repository-audit.md`](docs/research/repository-audit.md) documents what
was reused, forked, or rejected from the community Meta/GA4 MCP ecosystem, and why.

## Status

**Phase 4 — Creatives.** Phases 1–3 (auth, read-only Meta data, gated writes) plus image upload, creative
creation, and — now that a creative can actually exist — ad creation, completing what Phase 3 deferred.
Full chain (image upload → creative → ad, all `PAUSED`) is live-verified against the real account. Video
upload is implemented against the SDK's documented file-upload path but isn't live-verified the same way —
there's no test video in this environment, see [`SECURITY.md`](SECURITY.md). Deployed and live at
`app.ankithing.com` / `api.ankithing.com`, still defaulting to `DRY_RUN`. GA4 and the MCP tool layer don't
exist yet, and creative performance/fatigue-detection is Phase 7 (optimization) scope — those stay honest
"not connected"/"not built" states, never fake data. See the phase list in
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

Backend `.env` needs: `DATABASE_URL`, `SESSION_SECRET`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`, and (from Phase 2)
`META_APP_ID` / `META_APP_SECRET` / `META_ACCESS_TOKEN` / `META_DEFAULT_AD_ACCOUNT_ID` — see
[`.env.example`](.env.example) for the full set and [`META_SETUP.md`](META_SETUP.md) for how to get the
Meta values.

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
