import yfinance as yf
import requests
from datetime import datetime

TOKEN = "8551177666:AAG7fn90_yBIlP0awiH1wznklewx5BHwpaU"
CHAT_ID = "2020923773"
TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "AVGO", "ADBE", "NFLX", "INTC", "PYPL", "BRK-B", "WMT", "V"]

def generar_mapa():
    cards_html = ""
    
    for t in TICKERS:
        try:
            s = yf.Ticker(t)
            h = s.history(period="1y")
            if h.empty: continue
            
            i = s.info
            px = i.get('currentPrice', 0)
            eps = i.get('trailingEps', 0)
            cap = i.get('marketCap', 1)
            ath = h['High'].max()
            f_ath = h['High'].idxmax()
            dias_ath = (datetime.now().date() - f_ath.date()).days
            
            # Cálculo de Valor y Filtrado
            vi = eps * (8.5 + 2 * 7.5) if eps > 0 else 0
            if vi > 0:
                diff = ((px / vi) - 1) * 100
            else:
                diff = 0 # N/A

            # Colores
            color = "#444" 
            if vi > 0:
                if diff < -30: color = "#008000"
                elif diff < 0: color = "#2d6a4f"
                elif diff > 50: color = "#800000"
                elif diff > 25: color = "#cc0000"
            
            # Tamaño por Market Cap
            size_factor = cap / 10**11
            width = max(110, min(220, size_factor * 20))
            height = width * 0.7

            cards_html += f"""
            <div class="card" style="background:{color}; width:{width}px; height:{height}px;">
                <div class="ticker">{t}</div>
                <div class="diff">{diff:+.1f}%</div>
                <div class="ath-info">{dias_ath}d desde ATH</div>
            </div>
            """
        except: continue

    html_final = f"""
    <html>
    <head>
        <style>
            body {{ background: #0e1117; color: white; font-family: sans-serif; padding: 20px; }}
            .container {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; }}
            .card {{ border-radius: 8px; display: flex; flex-direction: column; justify-content: center; 
                     align-items: center; border: 1px solid #333; }}
            .ticker {{ font-weight: bold; font-size: 1.1em; }}
            .diff {{ font-size: 0.9em; }}
            .ath-info {{ font-size: 0.7em; opacity: 0.7; margin-top: 4px; }}
        </style>
    </head>
    <body>
        <h1>📊 Radar Antigravity Pro</h1>
        <div class="container">{cards_html}</div>
    </body>
    </html>
    """
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_final)

if __name__ == "__main__":
    generar_mapa()
