import yfinance as yf
import requests
from datetime import datetime

TOKEN = "8551177666:AAG7fn90_yBIlP0awiH1wznklewx5BHwpaU"
CHAT_ID = "2020923773"
TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "AVGO", "ADBE", "NFLX", "INTC", "PYPL", "BRK-B", "WMT", "V"]

def generar_mapa():
    cards_html = ""
    hallazgos_telegram = []
    
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
            
            # Cálculo de Valor
            vi = eps * (8.5 + 2 * 7.5) if eps > 0 else 0
            diff = ((px / vi) - 1) * 100 if vi > 0 else 0
            
            # Colores según tus reglas
            color = "#444" 
            status = "Neutral"
            if vi > 0:
                if diff < -30: color, status = "#008000", "GANGA"
                elif diff < 0: color, status = "#2d6a4f", "BAJO VALOR"
                elif diff > 50: color, status = "#800000", "BURBUJA"
                elif diff > 25: color, status = "#cc0000", "SOBREVALORADA"
            
            # Tamaño por Market Cap
            size = max(100, min(250, cap / 10**10.5)) 

            cards_html += f"""
            <div class="card" style="background:{color}; width:{size}px; height:{size*0.7}px;" 
                 title="Precio: ${px:.2f} | VI: ${vi:.2f} | ATH: ${ath:.2f} | Días desde ATH: {dias_ath} | Estado: {status}">
                <div class="ticker">{t}</div>
                <div class="diff">{diff:+.1f}%</div>
            </div>
            """
            if diff < -30 or diff > 25:
                hallazgos_telegram.append(f"{t}: {diff:+.1f}% ({status})")
        except: continue

    html_final = f"""
    <html>
    <head>
        <style>
            body {{ background: #0e1117; color: white; font-family: 'Segoe UI', sans-serif; padding: 20px; }}
            .container {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; }}
            .card {{ border-radius: 8px; display: flex; flex-direction: column; justify-content: center; 
                     align-items: center; cursor: pointer; transition: 0.2s; border: 1px solid #333; }}
            .card:hover {{ transform: scale(1.05); filter: brightness(1.2); }}
            .ticker {{ font-weight: bold; font-size: 1.1em; }}
            .diff {{ font-size: 0.8em; opacity: 0.8; }}
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

    if hallazgos_telegram:
        msg = "🚀 **ALERTAS DEL RADAR**\n\n" + "\n".join(hallazgos_telegram)
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})

if __name__ == "__main__":
    generar_mapa()
