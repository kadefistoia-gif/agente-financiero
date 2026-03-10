import yfinance as yf
import datetime
import os
import requests

# ── CONFIG ──────────────────────────────────────────────────────────────────
TICKERS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
    "TSLA", "META", "AVGO", "ADBE", "NFLX",
    "INTC", "PYPL", "BRK-B", "WMT", "V"
]

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

GRAHAM_MULTIPLIER = 8.5 + 2 * 7.5   # = 23.5


# ── TELEGRAM ────────────────────────────────────────────────────────────────
def send_telegram(message: str) -> None:
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram credentials not set – skipping notification.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        print("Telegram alert sent.")
    except Exception as exc:
        print(f"Telegram error: {exc}")


# ── DATA FETCHING ────────────────────────────────────────────────────────────
def fetch_stock_data(ticker: str) -> dict:
    try:
        stk = yf.Ticker(ticker)
        info = stk.info

        price = (
            info.get("currentPrice")
            or info.get("regularMarketPrice")
            or info.get("previousClose")
            or 0
        )

        eps = info.get("trailingEps") or 0
        name = info.get("shortName") or ticker

        if eps <= 0:
            vi = 0
        else:
            vi = eps * GRAHAM_MULTIPLIER

        hist = stk.history(period="52wk")
        if not hist.empty:
            ath_val = float(hist["High"].max())
            ath_date = hist["High"].idxmax()
            if hasattr(ath_date, "date"):
                ath_date = ath_date.date()
            days_since_ath = (datetime.date.today() - ath_date).days
        else:
            ath_val = price
            days_since_ath = 0

        if vi > 0 and price > 0:
            pct_vs_vi = (price - vi) / vi * 100
        else:
            pct_vs_vi = None

        return {
            "ticker": ticker,
            "name": name,
            "price": price,
            "eps": eps,
            "vi": vi,
            "ath": ath_val,
            "days_since_ath": days_since_ath,
            "pct_vs_vi": pct_vs_vi,
        }

    except Exception as exc:
        print(f"Error fetching {ticker}: {exc}")
        return {
            "ticker": ticker,
            "name": ticker,
            "price": 0,
            "eps": 0,
            "vi": 0,
            "ath": 0,
            "days_since_ath": 0,
            "pct_vs_vi": None,
        }


# ── COLOR LOGIC ─────────────────────────────────────────────────────────────
def get_color(pct) -> str:
    if pct is None:
        return "#444444"
    if pct <= -30:
        return "#1a6b2a"
    if pct >= 50:
        return "#800000"
    if pct >= 25:
        return "#e63946"
    if pct < 0:
        ratio = (-pct) / 30
        r = int(200 - ratio * 50)
        g = int(160 + ratio * 60)
        b = 50
    else:
        ratio = pct / 25
        r = int(200 + ratio * 40)
        g = int(160 - ratio * 120)
        b = 50
    return f"rgb({r},{g},{b})"


def get_label(pct) -> str:
    if pct is None:
        return "Sin Datos / EPS neg."
    if pct <= -30:
        return f"🟢 GANGA  {pct:+.1f}%"
    if pct >= 50:
        return f"💀 BURBUJA  {pct:+.1f}%"
    if pct >= 25:
        return f"🔴 Sobrevalorado  {pct:+.1f}%"
    if pct < 0:
        return f"🔵 Descuento  {pct:+.1f}%"
    return f"🟡 Prima  {pct:+.1f}%"


# ── HTML GENERATION ──────────────────────────────────────────────────────────
CARD_TEMPLATE = """
<div class="card" style="background:{color};" title="{name}">
  <div class="ticker">{ticker}</div>
  <div class="price">${price:.2f}</div>
  <div class="badge">{label}</div>
  <div class="meta">
    ATH&nbsp;<b>${ath:.2f}</b><br>
    <span class="muted">{days_ath} días atrás</span>
  </div>
  <div class="vi">VI Graham: <b>${vi:.2f}</b></div>
</div>
"""

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Radar de Acciones · Heatmap</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: #0e1117;
    color: #e8eaf0;
    font-family: 'Segoe UI', system-ui, sans-serif;
    min-height: 100vh;
    padding: 2rem 1.5rem;
  }}
  header {{ text-align: center; margin-bottom: 2rem; }}
  header h1 {{
    font-size: 1.8rem;
    font-weight: 700;
    letter-spacing: 0.05em;
    color: #ffffff;
  }}
  header p {{ font-size: 0.85rem; color: #8892a4; margin-top: 0.35rem; }}
  .legend {{
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 0.75rem;
    margin-bottom: 2rem;
    font-size: 0.78rem;
  }}
  .legend span {{
    padding: 0.3rem 0.75rem;
    border-radius: 999px;
    font-weight: 600;
  }}
  .grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 1rem;
    max-width: 1200px;
    margin: 0 auto;
  }}
  .card {{
    border-radius: 12px;
    padding: 1rem 0.85rem;
    cursor: default;
    transition: transform 0.18s ease, box-shadow 0.18s ease, filter 0.18s ease;
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
    min-height: 155px;
    border: 1px solid rgba(255,255,255,0.08);
  }}
  .card:hover {{
    transform: translateY(-6px) scale(1.04);
    box-shadow: 0 12px 32px rgba(0,0,0,0.55);
    filter: brightness(1.18);
    z-index: 10;
  }}
  .ticker {{
    font-size: 1.15rem;
    font-weight: 800;
    letter-spacing: 0.04em;
    color: #ffffff;
  }}
  .price {{ font-size: 0.95rem; font-weight: 600; color: rgba(255,255,255,0.9); }}
  .badge {{
    font-size: 0.72rem;
    font-weight: 700;
    background: rgba(0,0,0,0.3);
    border-radius: 6px;
    padding: 0.2rem 0.4rem;
    display: inline-block;
    color: #fff;
    word-break: break-word;
  }}
  .meta {{
    font-size: 0.72rem;
    color: rgba(255,255,255,0.75);
    line-height: 1.5;
    margin-top: auto;
  }}
  .vi {{ font-size: 0.72rem; color: rgba(255,255,255,0.65); }}
  .muted {{ color: rgba(255,255,255,0.5); }}
  footer {{
    text-align: center;
    margin-top: 3rem;
    font-size: 0.75rem;
    color: #4a5568;
  }}
</style>
</head>
<body>
<header>
  <h1>📡 Radar de Acciones · Heatmap</h1>
  <p>Actualizado: {updated} · Valor Intrínseco por fórmula de Graham (EPS × 23.5)</p>
</header>
<div class="legend">
  <span style="background:#1a6b2a;">🟢 Ganga ≤ −30% VI</span>
  <span style="background:#3a7bd5;">🔵 Descuento &lt; VI</span>
  <span style="background:#c8a020;">🟡 Prima leve</span>
  <span style="background:#e63946;">🔴 Sobreval. ≥ +25%</span>
  <span style="background:#800000;">💀 Burbuja ≥ +50%</span>
  <span style="background:#444;">⬜ Sin datos</span>
</div>
<div class="grid">
{cards}
</div>
<footer>
  Datos obtenidos vía yfinance · Solo con fines educativos, no constituye asesoría financiera.
</footer>
</body>
</html>
"""


# ── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    print("Fetching stock data…")
    stocks = [fetch_stock_data(t) for t in TICKERS]

    cards_html = ""
    gangas = []
    burbujas = []

    for s in stocks:
        pct = s["pct_vs_vi"]
        color = get_color(pct)
        label = get_label(pct)

        cards_html += CARD_TEMPLATE.format(
            color=color,
            name=s["name"],
            ticker=s["ticker"],
            price=s["price"],
            label=label,
            ath=s["ath"],
            days_ath=s["days_since_ath"],
            vi=s["vi"],
        )

        if pct is not None and pct <= -30:
            gangas.append(s["ticker"])
        if pct is not None and pct >= 50:
            burbujas.append(s["ticker"])

    updated = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    html = HTML_TEMPLATE.format(updated=updated, cards=cards_html)

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("index.html generated successfully.")

    if gangas or burbujas:
        msg_parts = [f"<b>📡 Radar de Acciones · {updated}</b>"]
        if gangas:
            msg_parts.append(f"🟢 <b>GANGAS</b> (≤ −30% VI): {', '.join(gangas)}")
        if burbujas:
            msg_parts.append(f"💀 <b>BURBUJAS</b> (≥ +50% VI): {', '.join(burbujas)}")
        send_telegram("\n".join(msg_parts))
    else:
        print("No extreme alerts to send via Telegram.")


if __name__ == "__main__":
    main()
