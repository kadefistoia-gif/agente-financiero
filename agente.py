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
            px = i.get('currentPrice', 0); eps = i.get('trailingEps', 0)
            ath = h['High'].max(); f_ath = h['High'].idxmax()
            dias = (datetime.now().date() - f_ath.date()).days
            vi = eps * (8.5 + 2 * 7.5) if eps > 0 else 0
            diff = ((px / vi) - 1) * 100 if vi > 0 else 0
            
            color = "#444"
            if vi > 0:
                if diff < -30: color = "#008000"
                elif diff > 25: color = "#cc0000"

            cards += f"""<div class='card' style='background:{color}'>
                <div class='t'>{t}</div>
                <div class='d'>{diff:+.1f}%</div>
                <div class='a'>ATH: ${ath:.0f} ({dias}d)</div>
                <div class='v'>VI: ${vi:.0f}</div>
            </div>"""
        except: continue

    html = f"""<html><head><style>
        body {{ background:#0e1117; color:white; font-family:sans-serif; display:grid; 
                grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap:10px; padding:20px; }}
        .card {{ border:1px solid #333; padding:15px; border-radius:8px; text-align:center; }}
        .t {{ font-weight:bold; font-size:1.2em; }}
        .d {{ font-size:1.1em; margin:5px 0; }}
        .a, .v {{ font-size:0.75em; opacity:0.7; }}
    </style></head><body>{cards}</body></html>"""
    
    with open("index.html", "w") as f: f.write(html)

if __name__ == "__main__": generar_radar()
