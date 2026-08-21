# Meta Ads Setup

How to get the four values the backend needs: `META_APP_ID`, `META_APP_SECRET`, `META_ACCESS_TOKEN`,
`META_DEFAULT_AD_ACCOUNT_ID`. Confirmed working against Marketing API v26.0.

## 1. Create a Meta App

1. [developers.facebook.com/apps](https://developers.facebook.com/apps) → **Create App** → type **Business**.
2. Add the **Marketing API** product to the app.
3. App dashboard → **Settings → Basic**: copy the **App ID** (`META_APP_ID`) and **App Secret**
   (`META_APP_SECRET`).

## 2. Create a System User and token

Use a System User token, not a personal user token — it doesn't expire and isn't tied to a person's login
session.

1. [business.facebook.com/settings](https://business.facebook.com/settings) → **Users → System Users** →
   **Add** → name it (e.g. "the21os"), role **Admin**.
2. **Assign Assets** on that System User → **Ad Accounts** → select the ad account this app should
   control → grant **Manage campaigns** (or Admin) access.
3. **Generate New Token** on the System User → select the app from step 1 → scopes: at minimum
   `ads_read`, `ads_management`, `business_management`. Copy the token immediately — Meta shows it once.
   This is `META_ACCESS_TOKEN`.

## 3. Find the ad account ID

Business Settings → **Ad Accounts** → the account's ID is shown as a number (e.g. `983241564578166`).
The backend expects the `act_` prefix: `META_DEFAULT_AD_ACCOUNT_ID=act_983241564578166`.

## 4. Access tier

New Meta apps start in **Limited access** — heavily rate-limited, but sufficient for a single
account read-only integration during development. **Full access** requires App Review (500+ calls over
15 days, <15% error rate) and isn't needed to run this system privately against one account.

## Known API constraints (v25.0+, still true in v26.0)

- **Advantage+ Shopping and Advantage+ App campaigns cannot be created or updated via the Marketing API**
  at all — Meta blocked this entirely as of May 2026. Not a bug in this codebase; there's no workaround
  short of the Ads Manager UI. Relevant once Phase 3 (writes) adds campaign creation.
- Budget fields (`daily_budget`, `lifetime_budget`, account `amount_spent`) are in **minor units** (paise
  for INR) — divide by 100 for a display value. Insights fields (`spend`, `cpc`, `cpm`) are **not** — they're
  already decimal strings in the account's currency. The frontend's `formatMinorUnits()` vs `formatCurrency()`
  in `apps/web/src/lib/format.ts` encode this distinction; getting it backwards silently shows numbers 100x
  off in either direction.
