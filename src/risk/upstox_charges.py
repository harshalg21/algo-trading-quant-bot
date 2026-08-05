def calculate_upstox_trade_charges(
    trade_type: str,
    buy_price: float,
    sell_price: float,
    quantity: int
) -> dict:
    """
    Calculates exact Upstox Brokerage & Regulatory Taxes for full round-trip (Buy + Sell):
    - Upstox Flat Brokerage: ₹20 per executed order (₹20 Buy + ₹20 Sell = ₹40)
    - CTT (Commodity Transaction Tax): 0.01% on sell side for MCX Futures
    - Exchange Turnover Charge: 0.0026% on total turnover
    - GST: 18% on (Brokerage + Exchange Charge)
    - Stamp Duty: 0.002% on buy side
    - SEBI Fee: ₹10 per Crore
    """
    turnover_buy = buy_price * quantity
    # If sell_price is not provided yet, estimate sell_price = target or entry
    est_sell = sell_price if sell_price and sell_price > 0 else (buy_price * 1.05)
    turnover_sell = est_sell * quantity
    total_turnover = turnover_buy + turnover_sell

    if "EQUITY" in trade_type.upper():
        brokerage = 0.0  # Upstox Equity Delivery Brokerage is ₹0
        stt = turnover_sell * 0.001  # STT 0.1% on Sell turnover
        stamp_duty = turnover_buy * 0.00015  # Stamp Duty 0.015% on Buy
    else:  # COMMODITY_FUTURES
        brokerage = 40.0  # ₹20 for Buy order + ₹20 for Sell order
        stt = turnover_sell * 0.0001  # CTT 0.01% on Sell turnover
        stamp_duty = turnover_buy * 0.00002  # Stamp Duty 0.002% on Buy

    exchange_charge = total_turnover * 0.000026
    sebi_fee = total_turnover * 0.000001
    gst = (brokerage + exchange_charge) * 0.18
    
    total_charges = brokerage + stt + exchange_charge + sebi_fee + stamp_duty + gst

    return {
        "brokerage": round(brokerage, 2),
        "stt_ctt": round(stt, 2),
        "exchange_charge": round(exchange_charge, 2),
        "stamp_duty": round(stamp_duty, 2),
        "gst": round(gst, 2),
        "total_charges": round(total_charges, 2)
    }

if __name__ == "__main__":
    chg = calculate_upstox_trade_charges("COMMODITY_FUTURES", 14340.0, 15150.0, 3)
    print("Exact Upstox 3-Lots Commodity Charges:", chg)
