import yfinance as yf
import requests
from datetime import datetime

TOKEN = "8551177666:AAG7fn90_yBIlP0awiH1wznklewx5BHwpaU"
CHAT_ID = "2020923773"

TICKERS = ["AAPL", "ABT", "ABBV", "ACN", "ADBE", "AMD", "AIG", "ALL", "GOOGL", "AMZN", "AXP", "AMGN", "ADI", "BA", "BAC", "BK", "BAX", "BIIB", "BLK", "BMY", "BRK-B", "C", "CAT", "CHTR", "CVX", "CSCO", "CL", "CMCSA", "COF", "COP", "COST", "CVS", "DHR", "DOW", "DUK", "EMR", "EXC", "XOM", "META", "FDX", "GD", "GE", "GILD", "GS", "HAL", "HD", "HON", "HPQ", "IBM", "INTC", "INTU", "ISRG", "JPM", "KDP", "KMB", "KMI", "KO", "LLY", "LMT", "LOW", "MA", "MCD", "MDT", "MET", "MMM", "MO", "MS", "MSFT", "NEE", "NFLX", "NKE", "NVDA", "ORCL", "OXY", "PEP", "PFE", "PG", "PM", "PYPL", "QCOM", "RTX", "SBUX", "SLB", "SO", "SPG", "T", "TGT", "TMO", "TMUS", "TSLA", "TXN", "UNH", "UNP", "UPS", "USB", "V", "VZ", "WFC", "WMT"]

def analizar():
    hallazgos = []
    for t in TICKERS:
        try:
            s = yf.Ticker(t)
            i = s.info
            px = i.get('currentPrice', 1)
            eps = i.get('trailingEps', 0)
            deuda = i.get('debtToEquity', 0) / 100
            sector = i.get('sector', 'Otros')
            
            # Valor Intrínseco y Descuento
            vi = eps * (8.5 + 2 * 7.5)
            desc = (1 - (px / vi)) * 100

            if deuda < 1.5 and desc > 20:
                # Datos Históricos
                hist = s.history(period="max")
                ath = hist['High'].max()
                f_ath = hist['High'].idxmax()
                caida_ath = ((ath - px) / ath) * 100
                
                # Tiempo infravalorada (Estimado 1 año atrás)
                h_year = s.history(period="1y")
                # Filtramos días donde el precio estuvo bajo el 80% del valor intrínseco
                dias_infra = len(h_year[h_year['Close'] < (vi * 0.8)])

                tag = "🚨 *GANGA (>30%)*" if desc > 30 else "👀 *VIGILANCIA*"
                color = "🟢" if desc > 30 else "🟡"
                
                info = (f"{color} **{t}** ({sector})\n"
                        f"{tag}\n"
                        f"🔹 Desc: {desc:.1f}% | Px: ${px}\n"
                        f"📉 Vs Máximo: -{caida_ath:.1f}% ({f_ath.strftime('%m/%Y')})\n"
                        f"⏳ Tiempo en oferta: ~{dias_infra} días\n"
                        f"───────────────────")
                hallos.append(info)
        except: continue

    if hallazgos:
        msg = "📊 **REPORTE ANTIGRAVITY PREMIUM**\n\n" + "\n".join(hallazgos)
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                      data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})

if __name__ == "__main__":
    analizar()
