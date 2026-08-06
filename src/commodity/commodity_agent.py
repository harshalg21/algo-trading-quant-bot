import sys
import requests
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

# Force UTF-8 for console output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.data.upstox_feed import UPSTOX_ACCESS_TOKEN, fetch_upstox_historical_candles, UPSTOX_MCX_INSTRUMENT_KEYS
from src.commodity.commodity_config import MCX_COMMODITY_UNIVERSE, COMMODITY_ACCOUNT_CAPITAL, MAX_COMMODITY_RISK_PCT, TOP_COMMODITY_SIGNALS_LIMIT
from src.commodity.global_macro_flow import fetch_global_commodity_macro_flows, evaluate_commodity_macro_sentiment
from src.strategies.momentum_breakout import compute_sma, compute_rsi, compute_atr

def get_usd_inr_exchange_rate() -> float:
    try:
        usdinr = yf.Ticker("INR=X").history(period="1d")
        if not usdinr.empty:
            return round(usdinr['Close'].iloc[-1], 2)
    except Exception:
        pass
    return 83.80

def convert_spot_to_mcx_futures_price(symbol: str, spot_price_usd: float, usd_inr: float) -> float:
    if symbol == "SI=F":
        mcx_price = spot_price_usd * 32.1507 * usd_inr * 2.50
        return round(mcx_price, -1)
    elif symbol == "GC=F":
        mcx_price = (spot_price_usd / 31.1035) * usd_inr * 1.14
        return round(mcx_price, -1)
    elif symbol == "CL=F":
        mcx_price = spot_price_usd * usd_inr
        return round(mcx_price, 1)
    elif symbol == "NG=F":
        mcx_price = spot_price_usd * usd_inr
        return round(mcx_price, 1)
    return spot_price_usd

def calculate_recommended_contract_expiry() -> str:
    now = datetime.now()
    if now.day >= 15:
        target_date = now + timedelta(days=25)
    else:
        target_date = now
    return target_date.strftime("%b %Y").upper() + " FUTURES"

def run_commodity_agent_analysis() -> list:
    print("="*75)
    print(f" ⛏️ DEDICATED MCX COMMODITY FUTURES AGENT (UPSTOX LIVE SYNC) ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
    print("="*75)

    usd_inr = get_usd_inr_exchange_rate()

    macro_flows = fetch_global_commodity_macro_flows()
    print(f"\n🌐 Global Commodity Macro Flows:")
    print(f" • US Dollar Index (DXY) : {macro_flows['dxy_close']} ({macro_flows['dxy_change_pct']:+.2f}%) -> {macro_flows['dxy_trend']}")
    print(f" • US 10Y Bond Yield     : {macro_flows['us10y_yield']}%")

    expiry_month = calculate_recommended_contract_expiry()
    candidate_signals = []

    for asset in MCX_COMMODITY_UNIVERSE:
        global_sym = asset['symbol']
        mcx_name = asset['name']
        mcx_ticker = asset['mcx_ticker']
        category = asset['category']
        approx_margin = asset['approx_margin_inr']

        try:
            used_upstox_feed = False
            if UPSTOX_ACCESS_TOKEN and mcx_ticker in UPSTOX_MCX_INSTRUMENT_KEYS:
                inst_key = UPSTOX_MCX_INSTRUMENT_KEYS[mcx_ticker]
                df = fetch_upstox_historical_candles(inst_key)
                if not df.empty:
                    used_upstox_feed = True
                    print(f"✅ Live Upstox Data Direct Stream for '{mcx_ticker}': Last Price = ₹{df['Close'].iloc[-1]:,.2f}")
                else:
                    df = yf.Ticker(global_sym).history(period="6mo", interval="1d")
            else:
                df = yf.Ticker(global_sym).history(period="6mo", interval="1d")

            if len(df) < 20:
                continue

            close = df['Close'].to_numpy()
            high = df['High'].to_numpy()
            low = df['Low'].to_numpy()

            sma200 = compute_sma(close, 200) if len(close) >= 200 else compute_sma(close, len(close)-1)
            ema20 = compute_sma(close, 20)
            rsi = compute_rsi(close, 14)
            atr = compute_atr(high, low, close, 14)

            price = close[-1]
            last_low = low[-1]
            is_uptrend = price > sma200[-1]
            ema_val = ema20[-1]
            is_above_ema = price >= ema_val
            is_pullback = last_low <= (ema_val * 1.02) and price >= (ema_val * 0.98)
            is_rsi_dip = 40 <= rsi[-1] <= 65

            macro_eval = evaluate_commodity_macro_sentiment(category, macro_flows['dxy_change_pct'])

            # 100% Dynamic Multi-Factor Quant Score Engine (No Hardcoding)
            quant_score = 30.0  # Base market participation score
            if is_uptrend: quant_score += 25.0      # Primary 200-day Trend Alignment
            if is_above_ema: quant_score += 15.0    # 20 EMA Short-term Momentum
            if is_pullback: quant_score += 15.0     # Low-risk Entry Pullback Dip
            if is_rsi_dip: quant_score += 10.0      # RSI Sweet Spot (40-65)
            quant_score += (macro_eval['score'] * 0.5)  # Macro Flow Contribution

            quant_score = round(max(35.0, min(95.0, quant_score)), 1)

            atr_val = atr[-1]
            
            if used_upstox_feed:
                mcx_entry = round(price, 2)
                mcx_sl = round(price - (atr_val * 1.5), 2)
                mcx_tp = round(price + (atr_val * 1.5 * 2.5), 2)
            else:
                spot_sl = price - (atr_val * 1.5)
                spot_tp = price + (atr_val * 1.5 * 2.5)
                mcx_entry = convert_spot_to_mcx_futures_price(global_sym, price, usd_inr)
                mcx_sl = convert_spot_to_mcx_futures_price(global_sym, spot_sl, usd_inr)
                mcx_tp = convert_spot_to_mcx_futures_price(global_sym, spot_tp, usd_inr)

            max_risk_inr = COMMODITY_ACCOUNT_CAPITAL * (MAX_COMMODITY_RISK_PCT / 100.0)
            risk_per_lot = abs(mcx_entry - mcx_sl)
            
            if risk_per_lot > 0:
                calc_lots = int(max_risk_inr / risk_per_lot)
                qty = max(1, min(calc_lots, int(COMMODITY_ACCOUNT_CAPITAL / approx_margin)))
            else:
                qty = 1

            total_margin_req = approx_margin * qty

            # Strict Professional Risk Gate: Only include high-probability setups (Quant Score >= 70.0)
            if quant_score >= 70.0:
                candidate_signals.append({
                    "mcx_name": mcx_name,
                    "mcx_ticker": mcx_ticker,
                    "category": category,
                    "expiry_month": expiry_month,
                    "mcx_entry_price": mcx_entry,
                    "mcx_stop_loss": mcx_sl,
                    "mcx_target": mcx_tp,
                    "quantity": qty,
                    "risk_amount": round(max_risk_inr, 2),
                    "approx_margin": round(total_margin_req, 2),
                    "quant_score": round(quant_score, 1),
                    "macro_reason": macro_eval['reason']
                })
            else:
                print(f"⏩ Filtering out {mcx_name} (Quant Score {quant_score:.1f} < 70.0 - Low Win Expectancy)")

        except Exception as e:
            print(f"Error analyzing {mcx_name}: {e}")

    candidate_signals.sort(key=lambda x: x['quant_score'], reverse=True)
    
    # Enforce Multi-Asset Category Diversification (Pick 1 Precious Metal + 1 Energy/Other)
    top_commodity_signals = []
    seen_categories = set()

    for sig in candidate_signals:
        cat = sig.get('category', 'PRECIOUS_METALS')
        if cat not in seen_categories or len(top_commodity_signals) < 1:
            seen_categories.add(cat)
            top_commodity_signals.append(sig)
        if len(top_commodity_signals) >= TOP_COMMODITY_SIGNALS_LIMIT:
            break

    if len(top_commodity_signals) < TOP_COMMODITY_SIGNALS_LIMIT and len(candidate_signals) > len(top_commodity_signals):
        for sig in candidate_signals:
            if sig not in top_commodity_signals:
                top_commodity_signals.append(sig)
                if len(top_commodity_signals) >= TOP_COMMODITY_SIGNALS_LIMIT:
                    break

    print(f"\nFiltered {len(candidate_signals)} candidate setup(s). Selected Top {len(top_commodity_signals)} Diversified Commodity Signal(s).")
    return top_commodity_signals

if __name__ == "__main__":
    run_commodity_agent_analysis()
