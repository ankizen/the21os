# Google Analytics 4 Setup

How to get the three values the backend needs: `GOOGLE_PROJECT_ID`, `GA4_PROPERTY_ID`,
`GOOGLE_SERVICE_ACCOUNT_JSON`. Confirmed working against the GA4 Data API v1beta and Admin API v1beta.

## 1. Create a Google Cloud project (or use an existing one)

[console.cloud.google.com](https://console.cloud.google.com) → create/select a project. Note the
**Project ID** (not the display name) — that's `GOOGLE_PROJECT_ID`.

## 2. Enable the two APIs

**APIs & Services → Enable APIs** → enable both:

- **Google Analytics Data API**
- **Google Analytics Admin API**

## 3. Create a service account and key

1. **IAM & Admin → Service Accounts → Create Service Account**. No project-level role is needed — access
   is granted inside GA4 itself (step 4), not via GCP IAM.
2. On the new service account → **Keys → Add Key → Create new key → JSON**. This downloads the key file.

## 4. Grant the service account Viewer access in GA4

GA4 Admin (`analytics.google.com`) → the property → **Admin → Property Access Management → Add users** →
paste the service account's email (`...@<project-id>.iam.gserviceaccount.com`, from the JSON's
`client_email` field) → role **Viewer**. This is the actual access grant — the GCP project role in step 3
doesn't matter for reading GA4 data.

## 5. Find the property ID

GA4 Admin → **Admin → Property Settings** — the property ID is the number in the URL/settings page (e.g.
`542878901`), not the "G-XXXXXXX" measurement ID. That's `GA4_PROPERTY_ID`.

## 6. Compact the key into one env var

`GOOGLE_SERVICE_ACCOUNT_JSON` holds the **raw JSON content**, not a file path — simpler to inject as one
Coolify env var than mounting a secret file, and `google-auth` builds credentials straight from a parsed
dict. Compact the downloaded key to a single line first:

```bash
python -c "import json,sys; print(json.dumps(json.load(open(sys.argv[1])),separators=(',',':')))" key.json
```

Paste that single line as the env var value.

## Known things worth knowing

- **"Conversions" is called `keyEvents` in the Data API**, not `conversions` — Google renamed the concept
  in the product UI in 2024 and the API metric name follows it. Confirmed by querying this property's own
  metadata endpoint (`GetMetadata`) — `conversions` isn't in the valid metric list, `keyEvents` is. If a
  custom report ever needs a metric name, check `client.get_metadata(name="properties/<id>/metadata")`
  first rather than assuming the older name still works.
- **Sessions dimension `sessionCampaignName` reflects whatever UTM `utm_campaign` parameter is on the
  landing URL.** For this account specifically, that happens to be the literal Meta campaign ID — which is
  what makes `core/correlation.py`'s Meta↔GA4 join possible without inventing attribution. If UTMs on ads
  ever stop using the campaign ID as `utm_campaign`, that join silently returns fewer matches — worth
  checking Ads Manager's URL parameters template if Compare starts showing "no GA4 data" for real campaigns.
- **Quota**: 200,000 core tokens/property/day, 40,000/hour, 10 concurrent requests (standard tier — this
  property isn't on GA4 360). Most requests here cost a handful of tokens; not a practical concern at this
  system's polling frequency.
