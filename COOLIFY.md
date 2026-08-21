# Coolify Deployment

What's actually live, and how to reproduce or redeploy it.

## Current setup

- **Instance**: a self-hosted Coolify instance, project **The21OS**, environment **production**.
- **Resource**: one Application, build pack **Docker Compose**, source `github.com/ankizen/the21os`
  branch `main`, compose file at repo root (`docker-compose.yml`).
- **Domains**: `web` service → `https://app.ankithing.com`, `api` service → `https://api.ankithing.com`,
  set via the app's `docker_compose_domains` config (per-service, not the whole-app `domains` field).
  Traefik handles TLS (Let's Encrypt) automatically once DNS points at the server.
- **Database**: PostgreSQL as a compose sibling (`db` service, named volume), not a separate Coolify-managed
  database resource — see the "Deviation from the original plan" note below.
- **Networking**: `web` and `api` use `expose:` (not `ports:`) — reachable from Traefik over the
  compose-internal network, not bound to the host's public interface directly.

## Environment variables

Set on the application (Coolify → the app → Environment Variables), not in the repo. Required set matches
[`.env.example`](.env.example): `ENV`, `POSTGRES_USER`/`POSTGRES_PASSWORD`/`POSTGRES_DB`, `SESSION_SECRET`,
`ADMIN_EMAIL`/`ADMIN_PASSWORD`, `CORS_ORIGINS`, `NEXT_PUBLIC_API_URL` (build-time — see the comment in
`docker-compose.yml`, changing it needs a rebuild, not just a restart), and from Phase 2:
`META_APP_ID`/`META_APP_SECRET`/`META_ACCESS_TOKEN`/`META_DEFAULT_AD_ACCOUNT_ID`/`META_API_VERSION`.

## Deploying

Auto-deploy on push to `main` isn't enabled yet (deploys were triggered manually via the Coolify API while
building this out). To deploy: Coolify → the app → **Deploy**, or `POST /api/v1/deploy?uuid=<app_uuid>`
with a Bearer token. Migrations run automatically — `apps/api/docker-entrypoint.sh` runs
`alembic upgrade head` before starting uvicorn on every container start.

## Reproducing from scratch

1. Coolify → **New Project** → name it.
2. Inside the project's environment → **New Resource → Application → Docker Compose**, point at the repo,
   branch `main`, compose location `/docker-compose.yml`.
3. Set the env vars above.
4. Set per-service domains for `web` and `api` (Coolify's "Docker Compose domains" config — the same
   `docker_compose_domains` API field, or the equivalent UI fields per compose service).
5. Deploy. First deploy also creates the `operationalmode` Postgres enum and all tables via the Alembic
   migration — no manual DB setup needed.
6. Point your DNS `A`/`CNAME` records at the Coolify server's IP for both domains before deploying, so
   Traefik's Let's Encrypt HTTP-01 challenge can complete on first request.

## Deviation from the original plan

[`docs/research/architecture-decision.md`](docs/research/architecture-decision.md) originally called for
Postgres as a separate Coolify-managed Database resource (for its own backup tooling), not a compose
sibling. In practice, a standalone Database resource sits on its own Docker network by default and needs
manual network-attachment to reach the compose app — real cross-resource wiring risk with no way to verify
it from outside the Coolify UI. Keeping `db` inside the same compose file was the pragmatic call: it's
already correctly networked (confirmed working), at the cost of losing Coolify's automatic DB backup
scheduling. Worth revisiting once there's a reason to (e.g. wanting scheduled backups without hand-rolling
`pg_dump`).
