import yfinance as yf
import requests
from datetime import datetime

TOKEN = "8551177666:AAG7fn90_yBIlP0awiH1wznklewx5BHwpaU"
CHAT_ID = "2020923773"
TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "AVGO", "ADBE", "NFLX", "INTC", "PYPL", "BRK-B", "WMT", "V"]

def generar_radar():
    cards = ""
    for t in TICKERS:
        try:
            s = yf.Ticker(t); h = s.history(period="1y"); i = s.info
            px = i.get('currentPrice', 1); eps = i.get('trailingEps', 0)
            ath = h['High'].max(); f_ath = h['High'].idxmax()
            dias_ath = (datetime.now().date() - f_ath.date()).days
            
            vi = eps * (8.5 + 2 * 7.5) if eps > 0 else 0
            diff = ((px / vi) - 1) * 100 if vi > 0 else 0
            
            # Colores según tus reglas
            color = "#444"
            if vi > 0:
                if diff < -30: color = "#008000" # Ganga
                elif diff > 50: color = "#800000" # Burbuja
                elif diff > 25: color = "#cc0000" # Venta
            
            info_hover = f"Precio: ${px:.2f} | VI: ${vi:.2f} | ATH hace {dias_ath} dias"
            
            cards += f"""<div class='card' style='background:{color}' title='{info_hover}'>
                <b>{t}</b><br><small>{diff:+.1f}%</small>
            </div>"""
        except: continue

    html = f"""<html><head><style>
        body {{ background:#0e1117; color:white; font-family:sans-serif; padding:20px; display:flex; flex-wrap:wrap; gap:10px; }}
        .card {{ border:1px solid #333; padding:15px; border-radius:8px; width:120px; text-align:center; cursor:help; }}
    </style></head><body>{cards}</body></html>"""
    
    with open("radar.html", "w") as f: f.write(html)

if __name__ == "__main__": generar_radar()
