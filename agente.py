import yfinance as yf
import requests

TOKEN = "8551177666:AAG7fn90_yBIlP0awiH1wznklewx5BHwpaU"
CHAT_ID = "2020923773"
TICKERS = ["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA", "NVDA", "ADBE", "UPS", "USB", "VZ", "WFC"]

def analizar():
    hallazgos = []
    html_cards = "" # Para la web
    
    for t in TICKERS:
        try:
            s = yf.Ticker(t)
            i = s.info
            px = i.get('currentPrice', 1)
            eps = i.get('trailingEps', 0)
            vi = eps * (8.5 + 2 * 7.5)
            desc = (1 - (px / vi)) * 100
            
            # Color para la web: Verde si es ganga, Gris si no
            color_web = "#2ecc71" if desc > 30 else "#bdc3c7"
            
            if desc > 20:
                hallazgos.append(f"💎 {t}: {desc:.1f}% desc.")
            
            # Crear cuadrito para la web
            html_cards += f'<div style="background:{color_web}; padding:20px; margin:10px; border-radius:10px; display:inline-block; width:150px; text-align:center; font-family:sans-serif;"><b>{t}</b><br>{desc:.1f}%</div>'
        except: continue

    # 1. Guardar la Web
    with open("index.html", "w") as f:
        f.write(f"<html><body style='background:#f0f2f5;'><h1>Mi Radar de Ofertas</h1>{html_cards}</body></html>")

    # 2. Enviar Telegram
    if hallazgos:
        msg = "📊 **ACTUALIZACIÓN RADAR**\n\n" + "\n".join(hallazgos)
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})

if __name__ == "__main__":
    analizar()
