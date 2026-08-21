"""Client for the connected WordPress/WooCommerce site. Credentials live in
WordPressConnection (DB), editable from the Integrations page — same
rotate-without-redeploy pattern as SystemSettings.anthropic_api_key.

Application Passwords (WordPress core, since 5.6) authenticate the WP REST
API; WooCommerce's own Consumer Key/Secret authenticate its REST API — both
via HTTP Basic Auth over HTTPS, no OAuth dance needed since the site is
HTTPS-only."""

import httpx

from the21os.db.models import WordPressConnection

_TIMEOUT = 10.0


class WordPressNotConfigured(RuntimeError):
    """Raised when the site URL or a credential pair isn't set."""


def wp_auth(conn: WordPressConnection) -> httpx.BasicAuth:
    return httpx.BasicAuth(conn.app_username or "", conn.app_password or "")


def woo_auth(conn: WordPressConnection) -> httpx.BasicAuth:
    return httpx.BasicAuth(conn.woo_consumer_key or "", conn.woo_consumer_secret or "")


async def check_wp_connection(conn: WordPressConnection) -> dict:
    """Confirms the Application Password works — returns the WP user it authenticates as."""
    if not (conn.site_url and conn.app_username and conn.app_password):
        raise WordPressNotConfigured("Site URL / WordPress Application Password not set")
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.get(f"{conn.site_url}/wp-json/wp/v2/users/me", auth=wp_auth(conn))
        resp.raise_for_status()
        data = resp.json()
    return {"name": data.get("name"), "roles": data.get("roles", [])}


async def check_woo_connection(conn: WordPressConnection) -> dict:
    """Confirms the WooCommerce keys work — returns the store's total order count."""
    if not (conn.site_url and conn.woo_consumer_key and conn.woo_consumer_secret):
        raise WordPressNotConfigured("WooCommerce Consumer Key/Secret not set")
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.get(
            f"{conn.site_url}/wp-json/wc/v3/orders", params={"per_page": 1}, auth=woo_auth(conn)
        )
        resp.raise_for_status()
        total = resp.headers.get("X-WP-Total")
    return {"order_count": int(total) if total is not None else None}
