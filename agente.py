import yfinance as yf
import requests

# CREDENCIALES CONFIGURADAS
TOKEN = "8551177666:AAG7fn90_yBIlP0awiH1wznklewx5BHwpaU"
CHAT_ID = "2020923773"

# LISTA COMPLETA S&P 100
TICKERS = [
    "AAPL", "ABT", "ABBV", "ACN", "ADBE", "AMD", "AIG", "ALL", "GOOGL", "AMZN", 
    "AXP", "AMGN", "ADI", "BA", "BAC", "BK", "BAX", "BIIB", "BLK", "BMY", 
    "BRK-B", "C", "CAT", "CHTR", "CVX", "CSCO", "CL", "CMCSA", "COF", "COP", 
    "COST", "CVS", "DHR", "DOW", "DUK", "EMR", "EXC", "XOM", "META", "FDX", 
    "GD", "GE", "GILD", "GS", "HAL", "HD", "HON", "HPQ", "IBM", "INTC", 
    "INTU", "ISRG", "JPM", "KDP", "KMB", "KMI", "KO", "LLY", "LMT", "LOW", 
    "MA", "MCD", "MDT", "MET", "MMM", "MO", "MS", "MSFT", "NEE", "NFLX", 
    "NKE", "NVDA", "ORCL", "OXY", "PEP", "PFE", "PG", "PM", "PYPL", "QCOM", 
    "RTX", "SBUX", "SLB", "SO", "SPG", "T", "TGT", "TMO", "TMUS", "TSLA", 
    "TXN", "UNH", "UNP", "UPS", "USB", "V", "VZ", "WFC", "WMT"
]

def analizar():
    hallazgos = []
    for t in TICKERS:
        try:
            s = yf.Ticker(t)
            i = s.info
            px = i.get('currentPrice', 1)
            eps = i.get('trailingEps', 0)
            deuda = i.get('debtToEquity', 0) / 100
            
            # Valor Intrínseco (Crecimiento 7.5%)
            vi = eps * (8.5 + 2 * 7.5)
            desc = (1 - (px / vi)) * 100

            if deuda < 2 and desc > 20:
                tag = "🚨 *GANGA (>30%)*" if desc > 30 else "👀 *VIGILANCIA*"
                hallazgos.append(f"{tag}\n**{t}**: {desc:.1f}% desc. | Px: ${px}")
        except: continue

    if hallazgos:
        msg = "📊 **REPORTE ANTIGRAVITY**\n\n" + "\n\n".join(hallazgos)
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                      data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})

if __name__ == "__main__":
    analizar()
