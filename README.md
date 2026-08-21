# The21Secrets AI Ads OS

Private, self-hosted Meta Ads + Google Analytics control platform for The21Secrets, built for Claude to
operate through hard-coded safety guardrails. Not a SaaS product — single admin user, single business.

See [`docs/research/architecture-decision.md`](docs/research/architecture-decision.md) for the full system
design and [`docs/research/stack-decision.md`](docs/research/stack-decision.md) for why each piece of the
stack was chosen. [`docs/research/repository-audit.md`](docs/research/repository-audit.md) documents what
was reused, forked, or rejected from the community Meta/GA4 MCP ecosystem, and why.

## Status

**Phase 1 — Project foundation.** Auth, database, and the app shell are real and working. Meta Ads, GA4,
and the MCP tool layer do not exist yet — every dashboard page for those either shows honest "not connected
yet" empty state or is absent, never fake data. See the phase list in
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

Backend `.env` needs: `DATABASE_URL`, `SESSION_SECRET`, `ADMIN_EMAIL`, `ADMIN_PASSWORD` (see
[`.env.example`](.env.example) at the repo root for the full set — the backend only reads the Phase 1
subset today).

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

One Coolify Service (Docker Compose) — see [`docker-compose.yml`](docker-compose.yml) and
[`.env.example`](.env.example). Full step-by-step Coolify setup is written once Phase 1 has something
worth deploying end-to-end; for now the compose file is Coolify-ready (health checks, non-root containers,
internal networking) if you want to stand it up early.

## Security

See [`SECURITY.md`](SECURITY.md).
