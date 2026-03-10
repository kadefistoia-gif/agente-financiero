import time, datetime, os, json, ssl
import yfinance as yf
import pandas as pd

ssl._create_default_https_context = ssl._create_unverified_context

PROGRESS_FILE = "progreso.json"
BATCH_SIZE = 10
GRAHAM_MULTIPLIER = 23.5

def get_sp100_yahoo():
    # Obtiene tickers dinámicos de Yahoo
    try:
        s = yf.Screener()
        s.set_predefined_body('ms_sp500') # S&P base
        df = s.response['quotes'][:100]
        return [q['symbol'] for q in df]
    except:
        return ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "BRK-B", "V", "JPM"]

def fetch_stock(ticker):
    try:
        stk = yf.Ticker(ticker)
        info = stk.info
        px = info.get("currentPrice") or info.get("regularMarketPrice") or 0
        eps = info.get("trailingEps") or 0
        sector = info.get("sector", "Otros")
        vi = eps * GRAHAM_MULTIPLIER if eps > 0 else 0
        pct = ((px - vi) / vi * 100) if vi > 0 and px > 0 else None
        return {"t": ticker, "s": sector, "p": px, "vi": vi, "pct": pct}
    except:
        return {"t": ticker, "s": "Otros", "p": 0, "vi": 0, "pct": None}

def main():
    tickers = get_sp100_yahoo()
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f: processed_data = json.load(f)
    else: processed_data = []

    idx = len(processed_data)
    if idx < len(tickers):
        for t in tickers[idx : idx + BATCH_SIZE]:
            processed_data.append(fetch_stock(t))
            time.sleep(1)
        with open(PROGRESS_FILE, "w") as f: json.dump(processed_data, f)

    if len(processed_data) >= 100:
        processed_data.sort(key=lambda x: (x['pct'] is None, x['pct'] if x['pct'] is not None else 999))

    sector_counts = pd.Series([x['s'] for x in processed_data]).value_counts()
    
    cards = ""
    for s in processed_data:
        pct_val = s['pct']
        color = "#444"
        if pct_val is not None:
            if pct_val <= -30: color = "#1a6b2a"
            elif pct_val >= 50: color = "#800000"
            elif pct_val >= 25: color = "#e63946"
            else: color = "#c8a020" if pct_val < 0 else "#d47d32"
        
        # Borde azul neón por sector repetido
        border = "3px solid #00d4ff; box-shadow: 0 0 10px #00d4ff;" if sector_counts.get(s['s'], 0) >= 2 else "1px solid rgba(255,255,255,0.1)"
        
        cards += f"""<div style="background:{color}; border:{border}; border-radius:10px; padding:15px; min-height:140px;">
            <div style="font-weight:bold; font-size:1.2rem;">{s['t']}</div>
            <div style="font-size:0.7rem; opacity:0.7;">{s['s']}</div>
            <div style="font-size:1.1rem; margin:5px 0;">${s['p']:.2f}</div>
            <div style="background:rgba(0,0,0,0.3); padding:4px; border-radius:5px; width:fit-content; font-size:0.8rem;">
                {f"{pct_val:+.1f}%" if pct_val is not None else "N/A"}
            </div>
        </div>"""

    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><meta http-equiv="refresh" content="95">
    <style>body{{background:#0e1117;color:white;font-family:sans-serif;padding:20px;}}
    .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;}}</style>
    </head><body><h1 style="text-align:center;">Radar Vivo: {len(processed_data)}/100</h1>
    <div class="grid">{cards}</div></body></html>"""
    
    with open("index.html", "w", encoding="utf-8") as f: f.write(html)

if __name__ == "__main__": main()
