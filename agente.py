import time
import datetime
import os
import requests
import pandas as pd
import yfinance as yf

# ── TELEGRAM ────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

GRAHAM_MULTIPLIER = 23.5


def send_telegram(message: str) -> None:
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram credentials not set – skipping.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(
            url,
            json={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"},
            timeout=10,
        )
        r.raise_for_status()
        print("Telegram alert sent.")
    except Exception as e:
        print(f"Telegram error: {e}")


# ── EXTRACCIÓN DINÁMICA DE TICKERS ──────────────────────────────────────────
def get_sp100_tickers() -> list[str]:
    url = "https://en.wikipedia.org/wiki/S%26P_100"
    print("Fetching S&P 100 tickers from Wikipedia…")
    try:
        tables = pd.read_html(url, attrs={"id": "constituents"})
        df = tables[0]
        # La columna puede llamarse 'Symbol' o 'Ticker'
        col = "Symbol" if "Symbol" in df.columns else df.columns[0]
        tickers = (
            df[col]
            .astype(str)
            .str.strip()
            .str.replace(".", "-", regex=False)   # BRK.B → BRK-B
            .tolist()
        )
        print(f"  {len(tickers)} tickers found.")
        return tickers
    except Exception as e:
        print(f"Error fetching tickers: {e}")
        # Fallback mínimo para que el workflow no muera vacío
        return [
            "AAPL","MSFT","GOOGL","AMZN","NVDA","TSLA","META",
            "AVGO","ADBE","NFLX","INTC","PYPL","BRK-B","WMT","V",
        ]


# ── FETCH INDIVIDUAL ─────────────────────────────────────────────────────────
def fetch_stock(ticker: str) -> dict:
    base = {
        "ticker": ticker, "name": ticker,
        "price": 0, "eps": 0, "vi": 0,
        "ath": 0, "days_since_ath": 0, "pct_vs_vi": None,
    }
    try:
        stk  = yf.Ticker(ticker)
        info = stk.info

        price = (
            info.get("currentPrice")
            or info.get("regularMarketPrice")
            or info.get("previousClose")
            or 0
        )
        eps  = info.get("trailingEps") or 0
        name = info.get("shortName") or ticker
        vi   = eps * GRAHAM_MULTIPLIER if eps > 0 else 0

        hist = stk.history(period="52wk")
        if not hist.empty:
            ath_val  = float(hist["High"].max())
            ath_date = hist["High"].idxmax()
            if hasattr(ath_date, "date"):
                ath_date = ath_date.date()
            days_ath = (datetime.date.today() - ath_date).days
        else:
            ath_val  = price
            days_ath = 0

        pct = (price - vi) / vi * 100 if vi > 0 and price > 0 else None

        return {
            "ticker": ticker, "name": name,
            "price": price, "eps": eps, "vi": vi,
            "ath": ath_val, "days_since_ath": days_ath, "pct_vs_vi": pct,
        }
    except Exception as e:
        print(f"  [SKIP] {ticker}: {e}")
        return base


# ── COLOR & LABEL ────────────────────────────────────────────────────────────
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
        return "Sin datos / EPS neg."
    if pct <= -30:
        return f"🟢 GANGA  {pct:+.1f}%"
    if pct >= 50:
        return f"💀 BURBUJA  {pct:+.1f}%"
    if pct >= 25:
        return f"🔴 Sobreval.  {pct:+.1f}%"
    if pct < 0:
        return f"🔵 Descuento  {pct:+.1f}%"
    return f"🟡 Prima  {pct:+.1f}%"


# ── PLANTILLAS HTML ──────────────────────────────────────────────────────────
CARD = """<div class="card" style="background:{color}" title="{name}">
  <div class="ticker">{ticker}</div>
  <div class="price">${price:.2f}</div>
  <div class="badge">{label}</div>
  <div class="meta">ATH <b>${ath:.2f}</b><br><span class="muted">{days} días atrás</span></div>
  <div class="vi">VI Graham: <b>${vi:.2f}</b></div>
</div>"""

PAGE = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>S&amp;P 100 · Radar Heatmap</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#0e1117;color:#e8eaf0;font-family:'Segoe UI',system-ui,sans-serif;padding:2rem 1.5rem}}
header{{text-align:center;margin-bottom:1.8rem}}
header h1{{font-size:1.9rem;font-weight:800;color:#fff;letter-spacing:.04em}}
header p{{font-size:.82rem;color:#8892a4;margin-top:.3rem}}
.legend{{display:flex;flex-wrap:wrap;justify-content:center;gap:.6rem;margin-bottom:1.8rem;font-size:.76rem}}
.legend span{{padding:.25rem .7rem;border-radius:999px;font-weight:700}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:.9rem;max-width:1400px;margin:0 auto}}
.card{{border-radius:12px;padding:.95rem .8rem;display:flex;flex-direction:column;gap:.35rem;min-height:158px;
       border:1px solid rgba(255,255,255,.07);cursor:default;
       transition:transform .18s,box-shadow .18s,filter .18s}}
.card:hover{{transform:translateY(-6px) scale(1.05);box-shadow:0 14px 36px rgba(0,0,0,.6);filter:brightness(1.2);z-index:10}}
.ticker{{font-size:1.1rem;font-weight:800;color:#fff;letter-spacing:.03em}}
.price{{font-size:.92rem;font-weight:600;color:rgba(255,255,255,.9)}}
.badge{{font-size:.7rem;font-weight:700;background:rgba(0,0,0,.3);border-radius:6px;
        padding:.18rem .4rem;color:#fff;word-break:break-word}}
.meta{{font-size:.7rem;color:rgba(255,255,255,.72);line-height:1.5;margin-top:auto}}
.vi{{font-size:.7rem;color:rgba(255,255,255,.58)}}
.muted{{color:rgba(255,255,255,.45)}}
footer{{text-align:center;margin-top:2.5rem;font-size:.73rem;color:#4a5568}}
</style>
</head>
<body>
<header>
  <h1>📡 S&amp;P 100 · Radar Heatmap</h1>
  <p>Actualizado
