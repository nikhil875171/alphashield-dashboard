from typing import Tuple
import numpy as np
import pandas as pd
import yfinance as yf
from core.schemas import TechnicalSnapshot


def compute_technical_snapshot(
    symbol: str,
    period: str = "1y",
    interval: str = "1d"
) -> Tuple[TechnicalSnapshot, pd.DataFrame]:
    """
    Fetches OHLCV data, calculates quantitative momentum & microstructure indicators,
    and returns both the TechnicalSnapshot summary and the enriched DataFrame for plotting.
    """
    ticker = yf.Ticker(symbol)
    df = ticker.history(period=period, interval=interval)

    if df.empty or len(df) < 30:
        raise ValueError(f"Insufficient historical candle data retrieved for '{symbol}'.")

    # Clean DataFrame
    df = df.copy()
    if df.index.tz is not None:
        df.index = df.index.tz_localize(None)

    # 1. Exponential Moving Averages (20, 50, 200)
    df["EMA_20"] = df["Close"].ewm(span=20, adjust=False).mean()
    df["EMA_50"] = df["Close"].ewm(span=50, adjust=False).mean()
    df["EMA_200"] = df["Close"].ewm(span=min(200, len(df)), adjust=False).mean()

    # 2. RSI (14-period)
    delta = df["Close"].diff()
    gain = (delta.where(delta > 0, 0.0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(window=14).mean()
    rs = gain / (loss.replace(0, 0.00001))
    df["RSI_14"] = 100 - (100 / (1 + rs))

    # 3. MACD (12, 26, 9)
    ema_12 = df["Close"].ewm(span=12, adjust=False).mean()
    ema_26 = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"] = ema_12 - ema_26
    df["MACD_SIGNAL"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["MACD_HIST"] = df["MACD"] - df["MACD_SIGNAL"]

    # 4. Volume Weighted Average Price (VWAP)
    typical_price = (df["High"] + df["Low"] + df["Close"]) / 3.0
    cum_vol = df["Volume"].cumsum()
    cum_vp = (typical_price * df["Volume"]).cumsum()
    df["VWAP"] = cum_vp / cum_vol.replace(0, 1)

    # 5. Average True Range (ATR 14)
    high_low = df["High"] - df["Low"]
    high_close = (df["High"] - df["Close"].shift()).abs()
    low_close = (df["Low"] - df["Close"].shift()).abs()
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df["ATR_14"] = true_range.rolling(window=14).mean()
    # Backfill ATR for early periods if needed
    df["ATR_14"] = df["ATR_14"].bfill()

    # 6. Volume Microstructure & Spread Impact
    df["VOL_SMA_20"] = df["Volume"].rolling(window=20).mean().bfill()

    latest = df.iloc[-1]
    prev = df.iloc[-2]

    curr_price = float(latest["Close"])
    prev_close = float(prev["Close"])
    change_pct = round(((curr_price - prev_close) / prev_close) * 100.0, 2)
    atr = float(latest["ATR_14"]) if not np.isnan(latest["ATR_14"]) else (curr_price * 0.02)
    adv_20 = int(latest["VOL_SMA_20"]) if not np.isnan(latest["VOL_SMA_20"]) else int(latest["Volume"])
    vol_surge = round(float(latest["Volume"]) / max(adv_20, 1), 2)

    # Dynamic ATR Stops (Long side default: current - multiplier*ATR)
    stop_1_5 = round(max(curr_price - (1.5 * atr), 0.01), 2)
    stop_2_0 = round(max(curr_price - (2.0 * atr), 0.01), 2)

    # Estimated Bid-Ask Spread Impact: Low volume stocks suffer higher slippage
    # Proxy: 0.05% for highly liquid, scales up if ADV is low
    if adv_20 > 5_000_000:
        spread_impact = 0.05
    elif adv_20 > 1_000_000:
        spread_impact = 0.10
    elif adv_20 > 200_000:
        spread_impact = 0.25
    else:
        spread_impact = 0.60

    snapshot = TechnicalSnapshot(
        symbol=symbol,
        current_price=round(curr_price, 2),
        previous_close=round(prev_close, 2),
        change_pct=change_pct,
        ema_20=round(float(latest["EMA_20"]), 2),
        ema_50=round(float(latest["EMA_50"]), 2),
        ema_200=round(float(latest["EMA_200"]), 2),
        rsi_14=round(float(latest["RSI_14"]), 2),
        macd=round(float(latest["MACD"]), 2),
        macd_signal=round(float(latest["MACD_SIGNAL"]), 2),
        vwap=round(float(latest["VWAP"]), 2),
        atr_14=round(atr, 2),
        volume=int(latest["Volume"]),
        adv_20d=adv_20,
        volume_surge_ratio=vol_surge,
        estimated_spread_impact_pct=spread_impact,
        dynamic_stop_1_5x=stop_1_5,
        dynamic_stop_2_0x=stop_2_0,
    )

    return snapshot, df

