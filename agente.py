import time, datetime, os, requests, json
import pandas as pd
import yfinance as yf
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

# --- CONFIG ---
PROGRESS_FILE = "progreso.json"
BATCH_SIZE = 10
GRAHAM_MULTIPLIER = 23.5

def get_sp100_tickers():
    try:
        url = "https://en.wikipedia.org/wiki/S%26P_100"
        df = pd.read_html(url, attrs={"id": "constituents"})[0]
        # Guardamos ticker y sector para la lógica de bordes
        return df[['Symbol', 'Sector']].replace('.', '-', regex=True).to_dict('records')
    except:
        return [{"Symbol": "AAPL", "Sector": "Technology"}, {"Symbol": "MSFT", "Sector": "Technology"}]

def fetch_stock(ticker_data):
    symbol = ticker_data['Symbol']
    try:
        stk = yf.Ticker(symbol)
        info = stk.info
        price = info.get("currentPrice") or info.get("regularMarketPrice") or 0
        eps = info.get("trailingEps") or 0
        vi = eps * GRAHAM_MULTIPLIER if eps > 0 else 0
        pct = ((price - vi) / vi * 100) if vi > 0 else None
        
        return {
            "t": symbol, "s": ticker_data['Sector'], "p": price, 
            "vi": vi, "pct": pct, "n": info.get("shortName", symbol)
        }
    except:
        return {"t": symbol, "s": ticker_data['Sector'], "p": 0, "vi": 0, "pct": None, "n": symbol}

def get_color(pct):
    if pct is None: return "#444"
    if pct <= -30: return "#1a6b2a"
    if pct >= 50: return "#800000"
    if pct >= 25: return "#e63946"
    return "#c8a020" if pct < 0 else "#d47d32"

# --- LÓGICA DE PERSISTENCIA ---
def main():
    all_tickers = get_sp100_tickers()
    
    # Cargar progreso previo
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            processed_data = json.load(f)
    else:
        processed_data = []

    last_idx = len(processed_data)
    
    # Si ya terminamos las 100, ordenamos y reiniciamos
    if last_idx >= len(all_tickers):
        processed_data.sort(key=lambda x: (x['pct'] is None, x['pct'] if x['pct'] is not None else 999))
        os.remove(PROGRESS_FILE) # Para empezar de cero mañana
    else:
        # Procesar siguiente lote de 10
        next_batch = all_tickers[last_idx : last_idx + BATCH_SIZE]
        for item in next_batch:
            print(f"Procesando {item['Symbol']}...")
            processed_data.append(fetch_stock(item))
            time.sleep(0.5)
        
        with open(PROGRESS_FILE, "w") as f:
            json.dump(processed_data, f)

    # Contar sectores para el borde azul
    sector_counts = pd.Series([x['s'] for x in processed_data]).value_counts()
    
    # Generar HTML
    cards_html = ""
    for s in processed_data:
        color = get_color(s['pct'])
        # Borde azul si hay 2 o más del mismo sector
        border = "3px solid #007bff" if sector_counts[s['s']] >= 2 else "1px solid rgba(255,255,255,0.1)"
        
        cards_html += f"""
        <div class="card" style="background:{color}; border:{border};">
            <div style="font-weight:bold;">{s['t']}</div>
            <div style="font-size:0.8rem; opacity:0.8;">{s['s']}</div>
            <div style="font-size:1.2rem;">${s['p']:.2f}</div>
            <div style="font-size:0.7rem; background:rgba(0,0,0,0.3); padding:2px; border-radius:4px;">
                {f"{s['pct']:+.1f}%" if s['pct'] else "N/A"}
            </div>
        </div>"""

    updated = datetime.datetime.utcnow().strftime("%H:%M:%S UTC")
    
    # El meta refresh hace que la página se recargue sola cada 30 segundos
    html = f"""<!DOCTYPE html><html><head>
    <meta http-equiv="refresh" content="30">
    <style>
        body {{ background:#0e1117; color:white; font-family:sans-serif; display:grid; grid-template-columns:repeat(auto-fill, minmax(140px,1fr)); gap:10px; padding:20px; }}
        .card {{ border-radius:8px; padding:10px; transition:0.3s; }}
        h1 {{ grid-column: 1/-1; text-align:center; }}
    </style></head><body>
    <h1>📡 Radar Vivo: {len(processed_data)}/100 (Carga: {updated})</h1>
    {cards_html}
    </body></html>"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

if __name__ == "__main__":
    main()
