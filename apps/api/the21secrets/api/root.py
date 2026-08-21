from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from the21secrets.api.system import check_db
from the21secrets.config import get_settings
from the21secrets.db.base import get_db

router = APIRouter(include_in_schema=False)

_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The21Secrets AI Ads OS — API</title>
<style>
  :root {{
    --bg: #0a0a0a;
    --card: #171717;
    --border: rgba(255,255,255,0.1);
    --fg: #fafafa;
    --muted: #a1a1a1;
    --ok: #10b981;
    --bad: #ef4444;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--bg);
    color: var(--fg);
    font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  }}
  .card {{
    width: min(420px, 90vw);
    padding: 32px;
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    text-align: center;
  }}
  .dot {{
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 999px;
    background: {dot_color};
    margin-right: 8px;
  }}
  .status {{
    display: inline-flex;
    align-items: center;
    font-size: 13px;
    font-weight: 500;
    color: {status_color};
    margin-bottom: 16px;
  }}
  h1 {{
    font-size: 20px;
    font-weight: 600;
    letter-spacing: -0.01em;
    margin: 0 0 8px;
  }}
  p {{
    font-size: 14px;
    color: var(--muted);
    margin: 0;
    line-height: 1.5;
  }}
  .meta {{
    margin-top: 20px;
    padding-top: 16px;
    border-top: 1px solid var(--border);
    font-size: 12px;
    color: var(--muted);
    font-family: ui-monospace, "SF Mono", Menlo, monospace;
    display: flex;
    justify-content: space-between;
  }}
</style>
</head>
<body>
  <div class="card">
    <div class="status"><span class="dot"></span>{status_text}</div>
    <h1>The21Secrets AI Ads OS</h1>
    <p>Private Meta Ads + Google Analytics control platform.</p>
    <div class="meta">
      <span>env: {env}</span>
      <span>db: {db_text}</span>
    </div>
  </div>
</body>
</html>"""


@router.get("/", response_class=HTMLResponse)
async def root(db: AsyncSession = Depends(get_db)) -> str:
    db_ok = await check_db(db)
    return _PAGE.format(
        status_text="API is online" if db_ok else "API is degraded",
        status_color="var(--ok)" if db_ok else "var(--bad)",
        dot_color="var(--ok)" if db_ok else "var(--bad)",
        env=get_settings().env,
        db_text="ok" if db_ok else "unreachable",
    )
