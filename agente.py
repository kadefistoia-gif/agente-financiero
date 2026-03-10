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
        return [t.replace('.', '-') for t in df['Symbol'].tolist()]
    except:
        return ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "BRK-B", "V", "WMT", "DIS", "PYPL"]

TICKERS = sorted(get_sp100_tickers()) # Orden alfabético para que no se pierdan
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
GRAHAM_MULTIPLIER = 23.5

def fetch_stock_data(ticker):
    try:
        stk = yf.Ticker(ticker)
        i = stk.info
        px = i.get("currentPrice") or i.get("regularMarketPrice") or 0
        eps = i.get("trailingEps") or 0
        vi = eps * GRAHAM_MULTIPLIER if eps > 0 else 0
        
        h = stk.history(period="52wk")
        ath = float(h["High"].max()) if not h.empty else px
        f_ath = h["High"].idxmax() if not h.empty else datetime.date.today()
        dias = (datetime.date.today() - (f_ath.date() if hasattr(f_ath, "date") else f_ath)).days
        
        pct = ((px / vi) - 1) * 100 if vi > 0 else None
        return {"t": ticker, "n": i.get("shortName", ticker), "p": px, "vi": vi, "ath": ath, "d": dias, "pct": pct}
    except:
        return {"t": ticker, "n": ticker, "p": 0, "vi": 0, "ath": 0, "d": 0, "pct": None}

def get_color(pct):
    if pct is None: return "#444"
    if pct <= -30: return "#1a6b2a" # Ganga
    if pct >= 50: return "#800000"  # Burbuja
    if pct >= 25: return "#e63946"  # Sobrevalorado
    return "#c8a020" if pct < 0 else "#d47d32"

# ── GENERACIÓN ──────────────────────────────────────────────────────────────
def main():
    print(f"Procesando {len(TICKERS)} empresas...")
    cards_html = ""
    
    for t in TICKERS:
        s = fetch_stock_data(t)
        color = get_color(s['pct'])
        label = f"{s['pct']:+.1f}%" if s['pct'] is not None else "N/A"
        
        cards_html += f"""
        <div style="background:{color}; border-radius:10px; padding:12px; color:white; min-width:140px;">
            <b style="font-size:1.2rem;">{s['t']}</b><br>
            <span style="font-size:1.1rem;">${s['p']:.2f}</span><br>
            <small style="background:rgba(0,0,0,0.2); padding:2px 5px; border-radius:4px;">{label}</small><br>
            <div style="font-size:0.7rem; margin-top:8px; opacity:0.8;">
                ATH: ${s['ath']:.2f} ({s['d']}d)<br>VI: ${s['vi']:.2f}
            </div>
        </div>"""
        time.sleep(0.2) # Respiro para Yahoo

    html = f"""<!DOCTYPE html><html><body style="background:#0e1117; font-family:sans-serif; padding:20px;">
        <h1 style="color:white; text-align:center;">📡 Radar S&P 100</h1>
        <div style="display:grid; grid-template-columns:repeat(auto-fill, minmax(150px, 1fr)); gap:10px;">
            {cards_html}
        </div></body></html>"""
    
    with open("index.html", "w", encoding="utf-8") as f: f.write(html)

if __name__ == "__main__": main()
