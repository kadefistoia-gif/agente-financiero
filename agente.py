import yfinance as yf
import datetime
import os
import requests
import time
import pandas as pd

# ── CONFIG ──────────────────────────────────────────────────────────────────
def get_sp100_tickers():
    try:
        url = "https://en.wikipedia.org/wiki/S%26P_100"
        df = pd.read_html(url)[2]
        # Limpiar tickers (cambiar . por - para yfinance como BRK.B -> BRK-B)
        return [t.replace('.', '-') for t in df['Symbol'].tolist()]
    except Exception as e:
        print(f"Error cargando S&P 100: {e}")
        return ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "BRK-B"]

TICKERS = get_sp100_tickers()
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
GRAHAM_MULTIPLIER = 23.5 # (8.5 + 2 * 7.5)

# ── FUNCIONES DE APOYO ──────────────────────────────────────────────────────
def send_telegram(message: str):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try: requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}, timeout=10)
    except: print("Error enviando Telegram")

def fetch_stock_data(ticker):
    try:
        stk = yf.Ticker(ticker)
        info = stk.info
        price = info.get("currentPrice") or info.get("regularMarketPrice") or 0
        eps = info.get("trailingEps") or 0
        vi = eps * GRAHAM_MULTIPLIER if eps > 0 else 0
        
        hist = stk.history(period="52wk")
        ath_val = float(hist["High"].max()) if not hist.empty else price
        ath_date = hist["High"].idxmax() if not hist.empty else datetime.date.today()
        days_ath = (datetime.date.today() - (ath_date.date() if hasattr(ath_date, "date") else ath_date)).days
        
        pct_vs_vi = ((price - vi) / vi * 100) if vi > 0 else None
        return {"ticker": ticker, "name": info.get("shortName", ticker), "price": price, "vi": vi, "ath": ath_val, "days": days_ath, "pct": pct_vs_vi}
    except:
        return {"ticker": ticker, "name": ticker, "price": 0, "vi": 0, "ath": 0, "days": 0, "pct": None}

def get_color(pct):
    if pct is None: return "#444444"
    if pct <= -30: return "#1a6b2a"
    if pct >= 50: return "#800000"
    if pct >= 25: return "#e63946"
    return f"rgb({int(200+pct*1.6)},{int(160-pct*3.2)},50)" if pct > 0 else f"rgb({int(200+pct*1.3)},{int(160-pct*2)},50)"

def get_label(pct):
    if pct is None: return "Sin Datos / EPS neg."
    if pct <= -30: return f"🟢 GANGA {pct:+.1f}%"
    if pct >= 50: return f"💀 BURBUJA {pct:+.1f}%"
    if pct >= 25: return f"🔴 Sobreval. {pct:+.1f}%"
    return f"🔵 Descuento {pct:+.1f}%" if pct < 0 else f"🟡 Prima {pct:+.1f}%"

# ── HTML TEMPLATE ───────────────────────────────────────────────────────────
HTML_BASE = """<!DOCTYPE html><html><head><meta charset="UTF-8"><style>
body {{ background:#0e1117; color:#e8eaf0; font-family:sans-serif; padding:2rem; }}
header {{ text-align:center; margin-bottom:2rem; }}
.legend {{ display:flex; flex-wrap:wrap; justify-content:center; gap:0.5rem; margin-bottom:2rem; font-size:0.8rem; }}
.legend span {{ padding:0.3rem 0.6rem; border-radius:10px; font-weight:bold; color:white; }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(160px, 1fr)); gap:1rem; }}
.card {{ border-radius:12px; padding:1rem; border:1px solid rgba(255,255,255,0.1); transition:0.2s; min-height:160px; }}
.card:hover {{ transform:scale(1.05); filter:brightness(1.2); }}
.t {{ font-size:1.2rem; font-weight:800; }}
.p {{ font-size:1rem; font-weight:600; margin:4px 0; }}
.b {{ font-size:0.7rem; background:rgba(0,0,0,0.3); padding:3px; border-radius:4px; font-weight:bold; }}
.m {{ font-size:0.7rem; margin-top:10px; opacity:0.8; }}
</style></head><body><header><h1>📡 Radar S&P 100</h1><p>Actualizado: {upd}</p></header>
<div class="legend">
<span style="background:#1a6b2a;">🟢 Ganga ≤-30%</span><span style="background:#e63946;">🔴 Sobreval ≥25%</span><span style="background:#800000;">💀 Burbuja ≥50%</span>
</div><div class="grid">{cards}</div></body></html>"""

# ── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    print(f"Escaneando {len(TICKERS)} tickers...")
    results = []
    for t in TICKERS:
        results.append(fetch_stock_data(t))
        time.sleep(0.4)
    
    # Ordenar por oportunidad (Gangas primero)
    results.sort(key=lambda x: (x['pct'] is None, x['pct'] if x['pct'] is not None else 999))
    
    cards_html = ""
    gangas = []
    for s in results:
        cards_html += f"""<div class="card" style="background:{get_color(s['pct'])}" title="{s['name']}">
            <div class="t">{s['ticker']}</div><div class="p">${s['price']:.2f}</div>
            <div class="b">{get_label(s['pct'])}</div>
            <div class="m">ATH: <b>${s['ath']:.2f}</b><br>{s['days']} d tras ATH</div>
            <div style="font-size:0.7rem">VI: ${s['vi']:.2f}</div></div>"""
        if s['pct'] and s['pct'] <= -30: gangas.append(s['ticker'])

    updated = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(HTML_BASE.format(upd=updated, cards=cards_html))
    
    if gangas: send_telegram(f"<b>📡 Radar · GANGAS DETECTADAS:</b>\n{', '.join(gangas)}")

if __name__ == "__main__": main()
