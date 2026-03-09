import yfinance as yf
import requests
from datetime import datetime

TOKEN = "8551177666:AAG7fn90_yBIlP0awiH1wznklewx5BHwpaU"
CHAT_ID = "2020923773"

TICKERS = ["AAPL", "ABT", "ABBV", "ACN", "ADBE", "AMD", "AIG", "ALL", "GOOGL", "AMZN", "AXP", "AMGN", "ADI", "BA", "BAC", "BK", "BAX", "BIIB", "BLK", "BMY", "BRK-B", "C", "CAT", "CHTR", "CVX", "CSCO", "CL", "CMCSA", "COF", "COP", "COST", "CVS", "DHR", "DOW", "DUK", "EMR", "EXC", "XOM", "META", "FDX", "GD", "GE", "GILD", "GS", "HAL", "HD", "HON", "HPQ", "IBM", "INTC", "INTU", "ISRG", "JPM", "KDP", "KMB", "KMI", "KO", "LLY", "LMT", "LOW", "MA", "MCD", "MDT", "MET", "MMM", "MO", "MS", "MSFT", "NEE", "NFLX", "NKE", "NVDA", "ORCL", "OXY", "PEP", "PFE", "PG", "PM", "PYPL", "QCOM", "RTX", "SBUX", "SLB", "SO", "SPG", "T", "TGT", "TMO", "TMUS", "TSLA", "TXN", "UNH", "UNP", "UPS", "USB", "V", "VZ", "WFC", "WMT"]

def analizar():
    hallazgos = []
    print("Iniciando análisis profundo...")
    for t in TICKERS:
        try:
            s = yf.Ticker(t)
            i = s.info
            px = i.get('currentPrice', 1)
            eps = i.get('trailingEps', 0)
            deuda = i.get('debtToEquity', 0) / 100
            sector = i.get('sector', 'Otros')
            
            vi = eps * (8.5 + 2 * 7.5)
            desc = (1 - (px / vi)) * 100

            if deuda < 1.5 and desc > 20:
                # Datos de Máximos
                hist = s.history(period="max")
                ath = hist['High'].max()
                f_ath = hist['High'].idxmax().strftime('%m/%Y')
                caida_ath = ((ath - px) / ath) * 100
                
                # Tiempo en oferta (último año)
                h_year = s.history(period="1y")
                dias_infra = len(h_year[h_year['Close'] < (vi * 0.8)])

                tag = "🚨 *GANGA (>30%)*" if desc > 30 else "👀 *VIGILANCIA*"
                color = "🟢" if desc > 30 else "🟡"
                
                info = (f"{color} **{t}** | Sector: {sector}\n"
                        f"{tag}\n"
                        f"🔹 Descuento: {desc:.1f}%\n"
                        f"📉 Vs Máximo: -{caida_ath:.1f}% ({f_ath})\n"
                        f"⏳ Tiempo en oferta: ~{dias_infra} días\n"
                        f"───────────────────")
                hallazgos.append(info)
        except Exception as e:
            print(f"Error en {t}: {e}")
            continue

    if hallazgos:
        msg = "💎 **ANTIGRAVITY: OPORTUNIDADES TOP** 💎\n\n" + "\n".join(hallazgos)
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                      data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
    else:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                      data={"chat_id": CHAT_ID, "text": "✅ Análisis completado: No hay nuevas gangas hoy."})

if __name__ == "__main__":
    analizar()
