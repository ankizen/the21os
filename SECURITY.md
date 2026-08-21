# Security

This system can spend real advertising money and read private analytics data. It's treated like a
financial-control system, not an internal admin panel. This document covers what's actually implemented
today.

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

## Safety layer (implemented, Phase 3)

Every Meta write — REST API today, MCP and the Command Center in later phases — goes through the exact
same pipeline (`safety/pipeline.py::run_write`), regardless of caller:

```
validate → hard ceilings (never bypassed by mode) → operational-mode branch → execute or queue → audit
```

- **Hard ceilings** (`safety/checks.py`), checked before the mode branch and never overridden by it: max
  campaign budget, max daily-budget-increase %, max new campaigns/day (counted from today's successful
  `campaign.create` audit entries), max daily account spend (checked live against Meta's insights for
  spend-increasing writes). A budget *decrease*, of any size, never trips the increase-% ceiling.
- **Operational mode** (`system_settings.operational_mode`, editable on the Rules page):
  `READ_ONLY` rejects every write · `DRY_RUN` (the default) validates and audits but never calls Meta ·
  `SUPERVISED` queues every write as an `ApprovalRequest` · `AUTONOMOUS` executes immediately unless the
  amount exceeds `require_approval_over`, in which case it's queued the same as SUPERVISED.
- **Approvals** (`/api/approvals`): queued writes are replayed byte-for-byte through the same executor that
  would have run them immediately when approved — approving isn't a different code path from auto-execute,
  just a later one.
- **All creates are PAUSED** — `meta/campaigns.py::create_campaign` hard-codes `status=PAUSED`; there's no
  parameter that lets a caller (including Claude) request `ACTIVE` on create.
- **Rollback** (`safety/rollback.py`) reuses `audit_log.before_json`/`after_json` rather than a separate
  table — only pause/resume and budget changes are reversible, and rollback is itself just another write
  through the same pipeline (reverting a budget cut back up can still hit the increase-% ceiling).
- **Not yet wired**: `meta/guards.py` blocks Advantage+ Shopping/App campaign creation (Meta disallows this
  entirely via API as of 2026-05-19), but `create_campaign`'s signature doesn't expose the field that would
  trigger it — the guard is real and tested, just structurally unreachable until a future phase exposes
  richer campaign parameters (e.g. to Claude via MCP).

Claude is never trusted to self-enforce a limit stated only in a prompt — every check above runs in Python,
not in a system prompt.

## What Claude never receives directly

Per the master build brief: Meta app secret, raw GA4 service-account JSON, database credentials, the
session-signing secret, and any server/SSH credentials are read by backend code only. Claude (via the
Command Center or MCP) receives tool results, never the credentials those tools used internally.

## Reporting

This is a private single-operator system with no external users — there is no public disclosure process.
