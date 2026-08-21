from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from the21os.api.system import check_db
from the21os.config import get_settings
from the21os.db.base import get_db

router = APIRouter(include_in_schema=False)

_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The21OS — AI Ads API</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@600;700&family=Plus+Jakarta+Sans:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg: #12172a;
    --card: color-mix(in oklch, #1c2440 60%, transparent);
    --border: color-mix(in oklch, #ffffff 12%, transparent);
    --fg: #f5f6fb;
    --muted: #9ea3c0;
    --ok: #34d399;
    --bad: #f87171;
    --accent-a: #4f7cff;
    --accent-b: #a855f7;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background:
      radial-gradient(60% 50% at 15% 10%, rgb(79 124 255 / 35%), transparent 60%),
      radial-gradient(50% 45% at 90% 20%, rgb(168 85 247 / 25%), transparent 60%),
      radial-gradient(55% 50% at 50% 100%, rgb(56 90 200 / 30%), transparent 65%),
      var(--bg);
    color: var(--fg);
    font-family: "Plus Jakarta Sans", ui-sans-serif, system-ui, sans-serif;
  }}
  .card {{
    width: min(420px, 90vw);
    padding: 32px;
    background: var(--card);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid var(--border);
    border-radius: 16px;
    text-align: center;
    box-shadow: 0 20px 60px rgb(0 0 0 / 35%);
  }}
  .brand {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 20px;
  }}
  .mark {{
    display: flex;
    align-items: center;
    justify-content: center;
    width: 26px;
    height: 26px;
    border-radius: 8px;
    background: linear-gradient(135deg, var(--accent-a), var(--accent-b));
    font-family: "Outfit", sans-serif;
    font-weight: 700;
    font-size: 11px;
  }}
  .brand span {{
    font-family: "Outfit", sans-serif;
    font-weight: 600;
    font-size: 14px;
    letter-spacing: -0.01em;
  }}
  .brand span em {{
    font-style: normal;
    color: var(--muted);
    font-weight: 400;
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
    font-family: "Outfit", sans-serif;
    font-size: 21px;
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
    <div class="brand"><span class="mark">21</span><span>The21OS <em>— AI Ads</em></span></div>
    <div class="status"><span class="dot"></span>{status_text}</div>
    <h1>API is running</h1>
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
        status_text="Operational" if db_ok else "Degraded",
        status_color="var(--ok)" if db_ok else "var(--bad)",
        dot_color="var(--ok)" if db_ok else "var(--bad)",
        env=get_settings().env,
        db_text="ok" if db_ok else "unreachable",
    )
