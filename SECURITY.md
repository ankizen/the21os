# Security

This system can (from Phase 2 onward) spend real advertising money and read private analytics data. It's
treated like a financial-control system, not an internal admin panel. This document covers what's actually
implemented today; the full safety-layer design for write operations (Phase 3+) is in
[`docs/research/architecture-decision.md`](docs/research/architecture-decision.md).

## Authentication (implemented)

- Single admin user, seeded from `ADMIN_EMAIL`/`ADMIN_PASSWORD` on first boot only — those env vars are
  ignored once the `users` table has a row. Change the password through the app from then on.
- Passwords hashed with Argon2id (`argon2-cffi`), never stored or logged in plaintext.
- Sessions are a signed, timestamped token (`itsdangerous`) in an `httponly`, `SameSite=Lax` cookie, `secure`
  in production. Not a JWT — no claims/audience complexity a single-issuer, single-audience system doesn't
  need. Tampering or expiry both fail closed (`read_session_token` returns `None`).
- Optional TOTP 2FA (`pyotp`), enabled/disabled by the authenticated user. Disabling requires re-entering the
  password.
- No OAuth provider, no multi-tenant RBAC — deliberately out of scope per the master build brief; see
  [`docs/research/stack-decision.md`](docs/research/stack-decision.md#authentication-dashboard).

## Secret handling (implemented)

- Every write into the audit log passes through `audit/redact.py`, which recursively blanks any dict key
  matching a secret-shaped pattern (`token`, `secret`, `password`, `api_key`, `authorization`, `cookie`,
  `totp`, `private_key`, case-insensitive) before it's persisted.
- No secrets are ever stored in the database itself beyond the user's own password hash and TOTP secret
  (both required for the app to authenticate its one user). Meta/GA4 credentials (Phase 2+) live in
  environment variables / Coolify secrets only, never in a database row.
- `.env` files are gitignored; `.env.example` documents every variable without real values.

## Safety layer (Phase 3+, ceilings modeled now)

The `system_settings` table already models the operational-mode gate and hard-coded ceilings
(`DRY_RUN → READ_ONLY → SUPERVISED → AUTONOMOUS`, max daily spend, max campaign budget, max budget increase
%, max new campaigns/day, max ads/campaign, approval threshold) that every future Meta/GA4 write must pass
through — editable now via the Rules page, enforced in code once there's anything to enforce against. Claude
is never trusted to self-enforce a limit stated only in a prompt; see
[`docs/research/architecture-decision.md`](docs/research/architecture-decision.md#operational-modes).

## What Claude never receives directly

Per the master build brief: Meta app secret, raw GA4 service-account JSON, database credentials, the
session-signing secret, and any server/SSH credentials are read by backend code only. Claude (via the
Command Center or MCP) receives tool results, never the credentials those tools used internally.

## Reporting

This is a private single-operator system with no external users — there is no public disclosure process.
