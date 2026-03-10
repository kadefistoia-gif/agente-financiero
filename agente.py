import yfinance as yf
import requests
from datetime import datetime

# ... (TICKERS Y TOKENS IGUAL QUE ANTES) ...

def generar_mapa():
    cards_html = ""
    for t in TICKERS:
        try:
            s = yf.Ticker(t); h = s.history(period="1y"); i = s.info
            px = i.get('currentPrice', 1); eps = i.get('trailingEps', 0)
            ath = h['High'].max(); f_ath = h['High'].idxmax()
            dias_ath = (datetime.now().date() - f_ath.date()).days
            vi = eps * (8.5 + 2 * 7.5) if eps > 0 else 0
            diff = ((px / vi) - 1) * 100 if vi > 0 else 0
            
            # Color y Estado
            color = "#444"
            if vi > 0:
                if diff < -30: color = "#008000"
                elif diff > 25: color = "#cc0000"

            # El secreto del Hover es el atributo 'title'
            tooltip = f"Precio: ${px:.2f} | VI: ${vi:.2f} | ATH hace {dias_ath} dias"
            
            cards_html += f'<div class="card" style="background:{color};" title="{tooltip}"><b>{t}</b><br>{diff:+.1f}%</div>'
        except: continue

    html = f"""<html><head><style>
        body {{ background:#0e1117; color:white; font-family:sans-serif; display:flex; flex-wrap:wrap; gap:10px; padding:20px; }}
        .card {{ border:1px solid #333; padding:20px; border-radius:8px; text-align:center; min-width:120px; cursor:help; }}
    </style></head><body>{cards_html}</body></html>"""
    
    with open("index.html", "w") as f: f.write(html)

if __name__ == "__main__": generar_mapa()
