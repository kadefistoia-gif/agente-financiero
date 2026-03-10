import yfinance as yf
import requests
from datetime import datetime

TOKEN = "8551177666:AAG7fn90_yBIlP0awiH1wznklewx5BHwpaU"
CHAT_ID = "2020923773"
# Lista extendida para que el mapa se vea lleno y profesional
TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "BRK-B", "V", "JNJ", "WMT", "JPM", "PG", "MA", "UNH"]

def obtener_datos():
    datos_finales = []
    for t in TICKERS:
        try:
            stock = yf.Ticker(t)
            hist = stock.history(period="1y") # Datos de 1 año para máximos y tiempos
            info = stock.info
            
            px = info.get('currentPrice', 1)
            eps = info.get('trailingEps', 0)
            mkt_cap = info.get('marketCap', 1)
            
            # Máximo 52 semanas y días desde entonces
            ath = hist['High'].max()
            fecha_ath = hist['High'].idxmax()
            dias_desde_ath = (datetime.now().date() - fecha_ath.date()).days
            
            # Valor Intrínseco (Graham) - Solo si EPS es positivo
            if eps > 0:
                vi = eps * (8.5 + 2 * 7.5)
                diff = ((px / vi) - 1) * 100 # % sobre/bajo valor
            else:
                vi, diff = 0, 0 # N/A para empresas en pérdidas
            
            datos_finales.append({
                "ticker": t, "px": px, "vi": vi, "diff": diff,
                "cap": mkt_cap, "ath": ath, "dias_ath": dias_desde_ath
            })
        except: continue
    return datos_finales

# Aquí es donde el motor guarda la información para el siguiente paso
if __name__ == "__main__":
    resultados = obtener_datos()
    print(f"Datos procesados de {len(resultados)} empresas.")
    # El siguiente paso será "dibujar" estos datos en el mapa interactivo.
