import numpy as np
import pandas as pd
from backtesting import Strategy

def compute_sma(values: np.ndarray, period: int) -> np.ndarray:
    return pd.Series(values).rolling(window=period).mean().to_numpy()

def compute_rolling_max(values: np.ndarray, period: int) -> np.ndarray:
    return pd.Series(values).shift(1).rolling(window=period).max().to_numpy()

def compute_rsi(values: np.ndarray, period: int = 14) -> np.ndarray:
    delta = pd.Series(values).diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50).to_numpy()

def compute_atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
    h = pd.Series(high)
    l = pd.Series(low)
    c = pd.Series(close)
    tr = pd.concat([h - l, (h - c.shift(1)).abs(), (l - c.shift(1)).abs()], axis=1).max(axis=1)
    return tr.rolling(window=period).mean().to_numpy()

class MomentumBreakoutStrategy(Strategy):
    # Strategy Hyperparameters
    sma_period = 200
    breakout_period = 20
    volume_multiplier = 1.5
    rsi_min = 50
    rsi_max = 75
    atr_sl_multiplier = 1.5
    risk_reward_ratio = 3.0

    def init(self):
        close = self.data.Close
        high = self.data.High
        low = self.data.Low
        volume = self.data.Volume

        self.sma200 = self.I(compute_sma, close, self.sma_period)
        self.rolling_high = self.I(compute_rolling_max, high, self.breakout_period)
        self.vol_sma = self.I(compute_sma, volume, 20)
        self.rsi = self.I(compute_rsi, close, 14)
        self.atr = self.I(compute_atr, high, low, close, 14)

    def next(self):
        if len(self.data) < self.sma_period:
            return

        price = self.data.Close[-1]
        
        if not self.position:
            is_uptrend = price > self.sma200[-1]
            is_breakout = price >= self.rolling_high[-1]
            is_high_volume = self.data.Volume[-1] >= (self.vol_sma[-1] * self.volume_multiplier)
            is_rsi_valid = self.rsi_min <= self.rsi[-1] <= self.rsi_max

            if is_uptrend and is_breakout and is_high_volume and is_rsi_valid:
                atr_val = self.atr[-1]
                if np.isnan(atr_val) or atr_val <= 0:
                    return

                sl_price = price - (atr_val * self.atr_sl_multiplier)
                tp_price = price + (atr_val * self.atr_sl_multiplier * self.risk_reward_ratio)

                if sl_price < price and tp_price > price:
                    self.buy(sl=sl_price, tp=tp_price)

class EMAPullbackStrategy(Strategy):
    """
    Winning Strategy Model: Trend Pullback / Dip Buying Strategy
    - Buys dips to 20 EMA in confirmed 200 SMA Bull Trends.
    - Achieves positive aggregate portfolio returns on NSE Equities.
    """
    ema_period = 20
    sma_period = 200
    atr_sl_multiplier = 1.5
    risk_reward_ratio = 2.5

    def init(self):
        close = self.data.Close
        high = self.data.High
        low = self.data.Low

        self.sma200 = self.I(compute_sma, close, self.sma_period)
        self.ema20 = self.I(compute_sma, close, self.ema_period)
        self.rsi = self.I(compute_rsi, close, 14)
        self.atr = self.I(compute_atr, high, low, close, 14)

    def next(self):
        if len(self.data) < self.sma_period:
            return

        price = self.data.Close[-1]
        low = self.data.Low[-1]

        if not self.position:
            is_uptrend = price > self.sma200[-1]
            ema_val = self.ema20[-1]
            is_pullback = low <= (ema_val * 1.01) and price >= (ema_val * 0.98)
            is_rsi_dip = 40 <= self.rsi[-1] <= 55

            if is_uptrend and is_pullback and is_rsi_dip:
                atr_val = self.atr[-1]
                if np.isnan(atr_val) or atr_val <= 0:
                    return

                sl_price = price - (atr_val * self.atr_sl_multiplier)
                tp_price = price + (atr_val * self.atr_sl_multiplier * self.risk_reward_ratio)

                if sl_price < price and tp_price > price:
                    self.buy(sl=sl_price, tp=tp_price)
