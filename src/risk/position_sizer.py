import math

def calculate_position_size(
    account_equity: float,
    risk_per_trade_pct: float,
    entry_price: float,
    stop_loss_price: float
) -> dict:
    """
    Calculates exact share position sizing based on fixed dollar risk (e.g. 1% of total equity).
    Formula: Shares = (Equity * Risk%) / |Entry - StopLoss|
    """
    if entry_price <= 0 or stop_loss_price <= 0:
        raise ValueError("Entry price and Stop Loss must be positive.")
    
    risk_per_share = abs(entry_price - stop_loss_price)
    if risk_per_share == 0:
        return {"quantity": 0, "total_cost": 0, "max_risk_amount": 0, "risk_per_share": 0}
        
    total_risk_capital = account_equity * (risk_per_trade_pct / 100.0)
    quantity = math.floor(total_risk_capital / risk_per_share)
    total_cost = quantity * entry_price
    
    return {
        "quantity": quantity,
        "entry_price": entry_price,
        "stop_loss_price": stop_loss_price,
        "risk_per_share": round(risk_per_share, 2),
        "total_cost": round(total_cost, 2),
        "max_risk_amount": round(quantity * risk_per_share, 2)
    }
