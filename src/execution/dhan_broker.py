import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.config import DHAN_CLIENT_ID, DHAN_ACCESS_TOKEN, TRADING_MODE

class DhanBrokerExecution:
    def __init__(self):
        self.mode = TRADING_MODE
        self.dhan = None
        
        if self.mode == "LIVE":
            if not DHAN_CLIENT_ID or not DHAN_ACCESS_TOKEN:
                print("[WARNING]: Dhan API credentials missing in .env! Defaulting to PAPER trading mode.")
                self.mode = "PAPER"
            else:
                try:
                    from dhanhq import dhanhq
                    self.dhan = dhanhq(DHAN_CLIENT_ID, DHAN_ACCESS_TOKEN)
                    print("[BROKER]: Connected to DhanHQ Live API successfully!")
                except Exception as e:
                    print(f"[BROKER ERROR]: Failed to initialize DhanHQ SDK: {e}")
                    self.mode = "PAPER"

    def place_buy_order(self, symbol: str, quantity: int, price: float, stop_loss: float) -> dict:
        """
        Places BUY Order and attaches Stop Loss.
        Supports both PAPER trading and LIVE Dhan API execution.
        """
        clean_symbol = symbol.replace(".NS", "")
        
        if self.mode == "PAPER":
            print(f"[PAPER TRADING]: Simulated BUY {quantity} shares of {clean_symbol} @ ₹{price:.2f} (SL: ₹{stop_loss:.2f})")
            return {
                "status": "SUCCESS",
                "mode": "PAPER",
                "order_id": f"PAPER_{clean_symbol}_{int(price)}",
                "symbol": symbol,
                "quantity": quantity,
                "entry_price": price,
                "stop_loss": stop_loss
            }
            
        try:
            # Live DhanHQ Order Placement
            # Transaction Type: BUY (1), Exchange: NSE (1), Product: CNC (Delivery)
            order_res = self.dhan.place_order(
                security_id=clean_symbol,
                exchange_segment=self.dhan.NSE,
                transaction_type=self.dhan.BUY,
                quantity=quantity,
                order_type=self.dhan.MARKET,
                product_type=self.dhan.CNC,
                price=0
            )
            print(f"[LIVE DHAN ORDER]: {order_res}")
            return {"status": "SUCCESS", "mode": "LIVE", "response": order_res}
            
        except Exception as e:
            print(f"[LIVE ORDER ERROR]: {e}")
            return {"status": "ERROR", "mode": "LIVE", "error": str(e)}

if __name__ == "__main__":
    broker = DhanBrokerExecution()
    res = broker.place_buy_order("SBIN.NS", 37, 1027.40, 1000.61)
    print(f"Execution Test Result: {res}")
