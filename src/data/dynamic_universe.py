import pandas as pd
import yfinance as yf
from src.config import DEFAULT_STOCK_UNIVERSE

NIFTY_200_CANDIDATES = [
    "RELIANCE.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS", "TCS.NS",
    "BHARTIARTL.NS", "LT.NS", "SBIN.NS", "M&M.NS", "AXISBANK.NS",
    "ITC.NS", "SUNPHARMA.NS", "TITAN.NS", "KOTAKBANK.NS", "HCLTECH.NS",
    "NTPC.NS", "BAJFINANCE.NS", "ONGC.NS", "ULTRACEMCO.NS", "MARUTI.NS",
    "TATACONSUM.NS", "ADANIENT.NS", "ADANIPORTS.NS", "COALINDIA.NS",
    "POWERGRID.NS", "TATASTEEL.NS", "HEROMOTOCO.NS", "EICHERMOT.NS",
    "TRENT.NS", "BEL.NS", "HAL.NS", "DLF.NS", "VBL.NS", "ZOMATO.NS"
]

def get_dynamic_top_universe(top_n: int = 20) -> list:
    """
    Scans candidates and returns the Top N outperforming stocks based on 6-Month Relative Momentum.
    Updates the active universe dynamically according to current market scenarios!
    """
    print(f"Scanning {len(NIFTY_200_CANDIDATES)} stocks to select Top {top_n} outperforming universe...")
    momentum_scores = []
    
    for symbol in NIFTY_200_CANDIDATES:
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="6mo")
            if len(df) >= 100:
                start_price = df['Close'].iloc[0]
                end_price = df['Close'].iloc[-1]
                ret_pct = ((end_price - start_price) / start_price) * 100.0
                momentum_scores.append((symbol, ret_pct))
        except Exception:
            pass

    # Sort descending by 6-month return
    momentum_scores.sort(key=lambda x: x[1], reverse=True)
    top_universe = [item[0] for item in momentum_scores[:top_n]]
    
    print(f"Top {top_n} Outperforming Stocks Selected Dynamically:")
    for rank, (sym, ret) in enumerate(momentum_scores[:top_n], 1):
        print(f"  {rank}. {sym:<15} (+{ret:.2f}% 6m momentum)")
        
    return top_universe

if __name__ == "__main__":
    leaders = get_dynamic_top_universe()
