import time, datetime, os, requests, json
import pandas as pd
import yfinance as yf
import ssl

# Bypass para evitar errores de conexión en servidores de GitHub
ssl._create_default_https_context = ssl._create_unverified_context

# --- CONFIGURACIÓN ---
PROGRESS_FILE = "progreso.json"
BATCH_SIZE = 10
GRAHAM_MULTIPLIER = 23.5

def get_sp100_tickers():
    try:
        url = "https://en.wikipedia.org/wiki/S%26P_100"
        df = pd.read_html(url, attrs={"id": "constituents"})[0]
        # Limpiamos tickers y sectores
        df['Symbol'] = df['Symbol'].str.replace('.', '-', regex=False)
        return df[['Symbol', 'Sector']].to_dict('records')
    except Exception as e:
        print(f"Error Wikipedia: {e}")
        return [{"Symbol": "AAPL", "Sector": "Technology"}, {"Symbol": "MSFT", "Sector": "Technology"}]

def fetch_stock(ticker_data):
    symbol = ticker_data['Symbol']
    sector = ticker_data['Sector']
    try:
        stk = yf.Ticker(symbol)
        info = stk.info
        px = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose") or 0
        eps = info.get("trailingEps") or 0
        vi = eps * GRAHAM_MULTIPLIER if eps > 0 else 0
        pct = ((px - vi) / vi * 100) if vi > 0 and px > 0 else None
        
        return {
            "t": symbol, "s": sector, "p": px, 
            "vi": vi, "pct": pct, "n": info.get("shortName", symbol)
        }
    except Exception as e:
        print(f"Error {symbol}: {e}")
        return {"t": symbol, "s": sector, "p": 0, "vi": 0, "pct": None, "n": symbol}

def get_color(pct):
    if pct is None: return "#444444"
    if pct <= -30: return "#1a6b2a" # Verde Ganga
    if pct >= 50: return "#800000"  # Rojo Burbuja
    if pct >= 25: return "#e63946"  # Rojo Sobrevalorado
    if pct < 0: return "#c8a020"    # Dorado Descuento
    return "#d47d32"                # Naranja Prima

def main():
    all_tickers = get_sp100_tickers()
    
    # Cargar datos acumulados
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            processed_data = json.load(f)
    else:
        processed_data = []

    current_count = len(processed_data)
    
    # Procesar el siguiente lote de 10 si no hemos llegado a 100
    if current_count < len(all_tickers):
        batch = all_tickers[current_count : current_count + BATCH_SIZE]
        for item in batch:
            print(f"Extrayendo: {item['Symbol']}")
            processed_data.append(fetch_stock(item))
            time.sleep(0.5)
        
        # Guardar progreso
        with open(PROGRESS_FILE, "w") as f:
            json.dump(processed_data, f)

    # Si ya completamos las 100, ordenamos (Mejores oportunidades arriba)
    display_data = list(processed_data)
    if len(display_data) >= 100:
        display_data.sort(key=lambda x: (x['pct'] is None, x['pct'] if x['pct'] is not None else 999))

    # Lógica de Bordes: Detectar sectores repetidos en la carga actual
    sector_series = pd.Series([x['s'] for x in display_data])
    sector_counts = sector_series.value_counts()
    
    cards_html = ""
    for s in display_data:
        color = get_color(s['pct'])
        # Borde Azul Neón si hay 2 o más del mismo sector cargados
        has_group = sector_counts.get(s['s'], 0) >= 2
        border = "3px solid #00d4ff; box-shadow: 0 0 15px rgba(0, 212, 255, 0.4);" if has_group else "1px solid rgba(255,255,255,0.1)"
        label = f"{s['pct']:+.1f}%" if s['pct'] is not None else "N/A"
        
        cards_html += f"""
        <div class="card" style="background:{color}; border:{border};">
            <div class="ticker">{s['t']}</div>
            <div class="sector">{s['s']}</div>
            <div class="price">${s['p']:.2f}</div>
            <div class="badge">{label}</div>
            <div class="vi">VI Graham: ${s['vi']:.2f}</div>
        </div>"""

    updated = datetime.datetime.utcnow().strftime("%H:%M:%S UTC")
    
    # HTML Final con auto-refresh sincronizado de 90s
    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="90">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>S&P 100 Live Radar</title>
    <style>
        body {{ background:#0e1117; color:white; font-family:'Segoe UI',sans-serif; padding:20px; margin:0; }}
        .grid {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(155px, 1fr)); gap:12px; max-width:1400px; margin:0 auto; }}
        .card {{ border-radius:12px; padding:15px; display:flex; flex-direction:column; gap:6px; transition:all 0.3s; position:relative; min-height:160px; }}
        .card:hover {{ transform:scale(1.03); filter:brightness(1.1); }}
        .ticker {{ font-weight:800; font-size:1.3rem; letter-spacing:1px; }}
        .sector {{ font-size:0.65rem; text-transform:uppercase; opacity:0.7; font-weight:600; }}
        .price {{ font-size:1.1rem; font-weight:500; }}
        .badge {{ background:rgba(0,0,0,0.4); padding:4px 8px; border-radius:6px; font-size:0.8rem; font-weight:bold; width:fit-content; }}
        .vi {{ font-size:0.7rem; opacity:0.5; margin-top:auto; border-top:1px solid rgba(255,255,255,0.1); padding-top:5px; }}
        h1 {{ text-align:center; margin-bottom:5px; font-size:1.8rem; }}
        .status {{ text-align:center; opacity:0.6; font-size:0.9rem; margin-bottom:25px; }}
    </style>
</head>
<body>
    <h1>📡 Radar Vivo S&P 100</h1>
    <div class="status">Progreso: {len(display_data)}/100 | Actualizado: {updated} (Auto-refresh 90s)</div>
    <div class="grid">
        {cards_html}
    </div>
</body>
</html>"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

if __name__ == "__main__":
    main()
