import pandas as pd
import yfinance as yf
from pathlib import Path
from src.config import RAW_DATA_DIR, DEFAULT_STOCK_UNIVERSE

# Known symbol aliases or demerged ticker mappings on NSE
SYMBOL_ALIASES = {
    "TATAMOTORS.NS": "TMPV.NS",
    "TATAMOTORS": "TMPV.NS"
}

def fetch_stock_data(symbol: str, period: str = "2y", interval: str = "1d") -> pd.DataFrame:
    """
    Downloads historical stock data using yfinance and formats columns for backtesting.
    Standardized columns: ['Open', 'High', 'Low', 'Close', 'Volume']
    """
    target_symbol = SYMBOL_ALIASES.get(symbol.upper(), symbol)
    if target_symbol != symbol:
        print(f"Note: Mapping '{symbol}' to updated NSE ticker '{target_symbol}'")
        
    print(f"Fetching data for {target_symbol} ({period}, {interval})...")
    ticker = yf.Ticker(target_symbol)
    df = ticker.history(period=period, interval=interval)
    
    if df.empty:
        if "TATAMOTORS" in symbol.upper():
            raise ValueError(
                f"No price data found for {symbol}. "
                f"NSE Corporate Action Note: Tata Motors demerged into Commercial Vehicles (TMCV.NS) "
                f"and Passenger Vehicles (TMPV.NS)."
            )
        raise ValueError(f"No data returned for ticker {symbol}")
        
    df = df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
    df.dropna(inplace=True)
    
    # Save to RAW_DATA_DIR
    clean_symbol = symbol.replace(".NS", "").replace("^", "")
    file_path = RAW_DATA_DIR / f"{clean_symbol}_{interval}.csv"
    df.to_csv(file_path)
    print(f"Saved {len(df)} candles to {file_path}")
    
    return df

def fetch_universe_data(symbols: list = None, period: str = "2y"):
    if symbols is None:
        symbols = DEFAULT_STOCK_UNIVERSE
        
    for symbol in symbols:
        try:
            fetch_stock_data(symbol, period=period)
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")

if __name__ == "__main__":
    fetch_universe_data()
