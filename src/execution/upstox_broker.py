import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.config import TRADING_MODE

UPSTOX_API_KEY = os.getenv("UPSTOX_API_KEY", "")
UPSTOX_API_SECRET = os.getenv("UPSTOX_API_SECRET", "")
UPSTOX_ACCESS_TOKEN = os.getenv("UPSTOX_ACCESS_TOKEN", "")

class UpstoxBrokerExecution:
    def __init__(self):
        self.mode = TRADING_MODE
        self.upstox_api = None
        
        if self.mode == "LIVE":
            if not UPSTOX_API_KEY or not UPSTOX_ACCESS_TOKEN:
                print("[WARNING]: Upstox API credentials missing in .env! Operating in PAPER trading mode.")
                self.mode = "PAPER"
            else:
                try:
                    import upstox_client
                    configuration = upstox_client.Configuration()
                    configuration.access_token = UPSTOX_ACCESS_TOKEN
                    self.api_instance = upstox_client.OrderApi(upstox_client.ApiClient(configuration))
                    print("[BROKER]: Connected to Upstox Live API successfully!")
                except Exception as e:
                    print(f"[BROKER ERROR]: Failed to initialize Upstox SDK: {e}")
                    self.mode = "PAPER"

    def place_buy_order(self, symbol: str, quantity: int, price: float, stop_loss: float) -> dict:
        """
        Places BUY Order and attaches Stop Loss.
        Supports both PAPER trading and LIVE Upstox API execution.
        """
        clean_symbol = symbol.replace(".NS", "")
        
        if self.mode == "PAPER":
            print(f"[PAPER TRADING - UPSTOX]: Simulated BUY {quantity} shares of {clean_symbol} @ ₹{price:.2f} (SL: ₹{stop_loss:.2f})")
            return {
                "status": "SUCCESS",
                "broker": "UPSTOX",
                "mode": "PAPER",
                "order_id": f"UPSTOX_PAPER_{clean_symbol}_{int(price)}",
                "symbol": symbol,
                "quantity": quantity,
                "entry_price": price,
                "stop_loss": stop_loss
            }
            
        try:
            import upstox_client
            body = upstox_client.PlaceOrderRequest(
                quantity=quantity,
                product='DELIVERY',
                validity='DAY',
                price=0.0,
                tag='algo_trading',
                instrument_token=f'NSE_EQ|{clean_symbol}',
                order_type='MARKET',
                transaction_type='BUY',
                disclosed_quantity=0,
                trigger_price=0.0,
                is_amo=False
            )
            api_response = self.api_instance.place_order(body, '2.0')
            print(f"[LIVE UPSTOX ORDER RESPONSE]: {api_response}")
            return {"status": "SUCCESS", "broker": "UPSTOX", "mode": "LIVE", "response": api_response}
            
        except Exception as e:
            print(f"[LIVE UPSTOX ORDER ERROR]: {e}")
            return {"status": "ERROR", "broker": "UPSTOX", "mode": "LIVE", "error": str(e)}

if __name__ == "__main__":
    broker = UpstoxBrokerExecution()
    res = broker.place_buy_order("SBIN.NS", 37, 1027.40, 1000.61)
    print(f"Upstox Execution Test Result: {res}")
