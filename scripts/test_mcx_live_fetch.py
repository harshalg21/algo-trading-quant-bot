import yfinance as yf

tickers_to_test = [
    "SILVERMIC.NS",
    "SILVERMIC.MCX",
    "SILVERMIC26AUG.MCX",
    "SILVERMIC26AUG.NS",
    "MCX:SILVERMIC",
    "SILVERMIC=F"
]

print("Testing MCX Live Tickers on Yahoo Finance...")
for t in tickers_to_test:
    try:
        df = yf.Ticker(t).history(period="5d")
        if not df.empty:
            print(f"✅ SUCCESS for '{t}': Last Price = ₹{df['Close'].iloc[-1]}")
        else:
            print(f"❌ Empty for '{t}'")
    except Exception as e:
        print(f"❌ Failed for '{t}': {e}")
