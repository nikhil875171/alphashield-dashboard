from dataclasses import dataclass, field
from typing import List, Literal
import concurrent.futures
import numpy as np
import pandas as pd
import yfinance as yf


@dataclass
class MacroRegimeState:
    """Institutional macro transmission and cross-asset state."""
    regime_label: Literal["EXPANSION", "STAGFLATION", "DEFENSIVE", "VOLATILITY_HALT"]
    liquidity_bias: float  # -1.0 (severe liquidity drain) to +1.0 (abundant liquidity)
    active_macro_headwinds: List[str] = field(default_factory=list)
    vix: float = 15.0
    vix_tier: str = "Standard Risk Budget (VIX < 20)"
    position_scale_factor: float = 1.0  # 1.0 (normal), 0.5 (high risk), 0.0 (halt)
    dxy: float = 103.5
    dxy_20d_roc: float = 0.0
    yield_10y: float = 4.30
    yield_2y: float = 4.10
    yield_spread: float = 0.20
    yield_curve_state: str = "Normal (Healthy)"
    crude_oil: float = 75.0
    crude_demand_destruction: bool = False
    copper_gold_ratio: float = 0.0016
    industrial_momentum: str = "Balanced"
    hy_credit_spread_proxy: float = 0.72  # HYG / LQD price ratio
    systemic_credit_risk: str = "Normal"
    benchmark_name: str = "S&P 500"
    benchmark_price: float = 5600.0
    benchmark_change_pct: float = 0.0
    market_mood_label: str = "Calm & Supportive"
    market_mood_color: str = "green"
    market_mood_desc: str = "Overall market conditions are calm and favorable for investing."

    @property
    def macro_regime(self) -> str:
        return self.regime_label

    @property
    def yield_spread_10y_2y(self) -> float:
        return self.yield_spread

    @property
    def volatility_kill_switch_active(self) -> bool:
        return self.position_scale_factor == 0.0 or self.vix > 32.0


def _safe_fetch_series(symbol: str, period: str = "1mo") -> pd.Series:
    """Helper to safely fetch closing price series from yfinance with fallback."""
    try:
        t = yf.Ticker(symbol)
        h = t.history(period=period)
        if not h.empty and "Close" in h:
            s = h["Close"].dropna()
            if not s.empty:
                return s
    except Exception:
        pass
    return pd.Series(dtype=float)


def compute_macro_transmission(is_indian_market: bool = False) -> MacroRegimeState:
    """
    Evaluates cross-asset transmission dynamics across:
    1. US Dollar Index (DXY RoC)
    2. Yield Curve (10Y-2Y inversion and re-steepening)
    3. Crude Oil shocks and demand destruction (> $95/bbl)
    4. Doctor Copper vs. Gold ratio (expansion vs risk aversion)
    5. High-Yield Credit Spreads (HYG / LQD ratio)
    6. 4-tier Volatility (VIX) scaling
    """
    vix_symbol = "^INDIAVIX" if is_indian_market else "^VIX"
    benchmark_symbol = "^NSEI" if is_indian_market else "^GSPC"
    benchmark_name = "Nifty 50" if is_indian_market else "S&P 500"

    # Parallelize data retrieval for sub-second execution
    with concurrent.futures.ThreadPoolExecutor(max_workers=9) as executor:
        f_vix = executor.submit(_safe_fetch_series, vix_symbol, "1mo")
        f_bench = executor.submit(_safe_fetch_series, benchmark_symbol, "5d")
        f_dxy = executor.submit(_safe_fetch_series, "DX-Y.NYB", "2mo")
        f_10y = executor.submit(_safe_fetch_series, "^TNX", "1mo")
        f_2y = executor.submit(_safe_fetch_series, "2YY=F", "1mo")  # 2Y Treasury Futures
        f_crude = executor.submit(_safe_fetch_series, "CL=F", "1mo")
        f_copper = executor.submit(_safe_fetch_series, "HG=F", "1mo")  # Copper Futures
        f_gold = executor.submit(_safe_fetch_series, "GC=F", "1mo")    # Gold Futures
        f_hyg = executor.submit(_safe_fetch_series, "HYG", "1mo")     # High Yield Bond ETF
        f_lqd = executor.submit(_safe_fetch_series, "LQD", "1mo")     # Investment Grade ETF

        s_vix = f_vix.result()
        s_bench = f_bench.result()
        s_dxy = f_dxy.result()
        s_10y = f_10y.result()
        s_2y = f_2y.result()
        s_crude = f_crude.result()
        s_copper = f_copper.result()
        s_gold = f_gold.result()
        s_hyg = f_hyg.result()
        s_lqd = f_lqd.result()

    # Benchmark Price & 1-day Change
    if not s_bench.empty:
        bench_price = round(float(s_bench.iloc[-1]), 2)
        if len(s_bench) >= 2:
            prev_bench = float(s_bench.iloc[-2])
            bench_chg = round(((bench_price - prev_bench) / max(prev_bench, 1.0)) * 100.0, 2)
        else:
            bench_chg = 0.0
    else:
        bench_price = 24500.0 if is_indian_market else 5600.0
        bench_chg = 0.0

    headwinds: List[str] = []

    # 1. Volatility (VIX) 4-Tier Scaling
    vix_val = round(float(s_vix.iloc[-1]), 2) if not s_vix.empty else 14.50
    if vix_val > 32.0:
        vix_tier = "VOLATILITY HALT: Systemic Panic (VIX > 32)"
        position_scale = 0.0
        headwinds.append(f"Acute Volatility Panic: VIX at {vix_val} forces complete entry restriction.")
    elif vix_val > 25.0:
        vix_tier = "HIGH RISK: Severe Market Stress (25 < VIX <= 32)"
        position_scale = 0.50
        headwinds.append(f"Elevated Macro Volatility: VIX at {vix_val} automatically halves risk budget (-50%).")
    elif vix_val >= 20.0:
        vix_tier = "MODERATE ALERT: Cautious Sizing (20 <= VIX <= 25)"
        position_scale = 0.85
        headwinds.append(f"Moderate Volatility: VIX at {vix_val} requires tightened ATR stop multiples.")
    else:
        vix_tier = "EXPANSION: Standard Risk Budget (VIX < 20)"
        position_scale = 1.0

    # 2. US Dollar Index (DXY) 20-Day Rate of Change
    dxy_val = round(float(s_dxy.iloc[-1]), 2) if not s_dxy.empty else 103.50
    if len(s_dxy) >= 20:
        dxy_20d_roc = round(float((s_dxy.iloc[-1] - s_dxy.iloc[-20]) / s_dxy.iloc[-20] * 100.0), 2)
    elif len(s_dxy) >= 2:
        dxy_20d_roc = round(float((s_dxy.iloc[-1] - s_dxy.iloc[0]) / s_dxy.iloc[0] * 100.0), 2)
    else:
        dxy_20d_roc = 0.0

    if dxy_20d_roc > 2.0:
        headwinds.append(f"Rapid Dollar Surging: DXY +{dxy_20d_roc}% in 20 sessions triggers EM and commodity headwinds.")
    elif dxy_20d_roc < -2.0:
        # Dollar weakness provides tailwind for emerging markets
        pass

    # 3. Yield Curve (10Y minus 2Y Spread)
    y10 = round(float(s_10y.iloc[-1]), 2) if not s_10y.empty else 4.30
    y2 = round(float(s_2y.iloc[-1]), 2) if not s_2y.empty else 4.10
    spread = round(y10 - y2, 2)

    # Detect inversion vs rapid re-steepening
    if spread < 0.0:
        yield_state = "INVERTED: Recession Early Warning"
        headwinds.append(f"Yield Curve Inversion ({spread}%): Classic forward recessionary signal.")
    elif 0.0 <= spread <= 0.25 and len(s_10y) >= 10 and len(s_2y) >= 10:
        # Check if spread was recently inverted and is now rapidly steepening
        hist_spread = s_10y.iloc[-10] - s_2y.iloc[-10]
        if hist_spread < -0.20:
            yield_state = "RAPID RE-STEEPENING: Fed Panic-Cut / Crash Precursor"
            headwinds.append(f"Rapid Curve Re-Steepening ({spread}% from {round(hist_spread, 2)}%): Acute risk-off transition.")
        else:
            yield_state = "Flat / Neutral Consolidation"
    else:
        yield_state = "Normal (Healthy Slope)"

    # 4. Crude Oil & Demand Destruction Thresholds
    crude_val = round(float(s_crude.iloc[-1]), 2) if not s_crude.empty else 75.00
    demand_destruction = crude_val >= 95.0
    if demand_destruction:
        headwinds.append(f"Energy Shock: Crude at ${crude_val}/bbl enters demand destruction zone; compresses margins for net importers & industrials.")
    elif crude_val >= 85.0:
        headwinds.append(f"Elevated Crude (${crude_val}/bbl): Input margin pressure on transport, paints, and chemicals.")

    # 5. Doctor Copper vs. Gold Ratio
    copper_val = float(s_copper.iloc[-1]) if not s_copper.empty else 4.30
    gold_val = float(s_gold.iloc[-1]) if not s_gold.empty else 2650.0
    cg_ratio = round(copper_val / max(gold_val, 1.0), 6) if gold_val > 0 else 0.0016
    if cg_ratio > 0.0018:
        ind_momentum = "Cyclical Expansion (Copper Outperforming Gold)"
    elif cg_ratio < 0.0014:
        ind_momentum = "Defensive Risk-Aversion (Gold Outperforming Copper)"
        headwinds.append("Copper/Gold Ratio Weakness: Macro flight to safe havens indicates industrial deceleration.")
    else:
        ind_momentum = "Balanced Global Industrial Demand"

    # 6. High-Yield Credit Spreads (HYG / LQD Ratio)
    hyg_val = float(s_hyg.iloc[-1]) if not s_hyg.empty else 78.0
    lqd_val = float(s_lqd.iloc[-1]) if not s_lqd.empty else 108.0
    credit_ratio = round(hyg_val / max(lqd_val, 1.0), 3) if lqd_val > 0 else 0.72
    if credit_ratio < 0.69:
        credit_risk = "Elevated Default Risk (Widening Spreads)"
        headwinds.append("Credit Stress: High-yield bond underperformance indicates widening corporate default risk.")
    else:
        credit_risk = "Normal Corporate Credit Absorption"

    # Compute Aggregate Liquidity Bias (-1.0 to +1.0)
    # Penalties from headwinds
    bias = 0.40  # baseline modest positive
    if vix_val > 25:
        bias -= 0.50
    elif vix_val > 20:
        bias -= 0.20
    if dxy_20d_roc > 2.0:
        bias -= 0.25
    if spread < 0.0:
        bias -= 0.20
    if demand_destruction:
        bias -= 0.25
    if cg_ratio < 0.0014:
        bias -= 0.15
    if credit_ratio < 0.69:
        bias -= 0.20
    liquidity_bias = round(float(np.clip(bias, -1.0, 1.0)), 2)

    # Regime Determination
    if vix_val > 32.0:
        regime = "VOLATILITY_HALT"
    elif liquidity_bias < -0.30 or vix_val > 25.0:
        regime = "DEFENSIVE"
    elif crude_val > 88.0 and dxy_20d_roc > 1.5:
        regime = "STAGFLATION"
    else:
        regime = "EXPANSION"

    # Plain-English Market Mood for Beginners
    if vix_val > 25.0 or regime == "VOLATILITY_HALT":
        mood_label = "Stormy / High Fear"
        mood_color = "red"
        mood_desc = "High market turbulence and anxiety. Big institutions are cautious; prioritize protecting your money over taking big risks."
    elif vix_val >= 18.0 or spread < 0 or dxy_20d_roc > 2.0:
        mood_label = "Choppy / Caution Advised"
        mood_color = "yellow"
        mood_desc = "Market is choppy with mixed economic signals. Be selective; stick only to high-quality companies with proven earnings."
    else:
        mood_label = "Calm & Supportive"
        mood_color = "green"
        mood_desc = "Market waters are calm, interest volatility is low, and liquidity is flowing smoothly. Favorable climate for investing."

    return MacroRegimeState(
        regime_label=regime,
        liquidity_bias=liquidity_bias,
        active_macro_headwinds=headwinds,
        vix=vix_val,
        vix_tier=vix_tier,
        position_scale_factor=position_scale,
        dxy=dxy_val,
        dxy_20d_roc=dxy_20d_roc,
        yield_10y=y10,
        yield_2y=y2,
        yield_spread=spread,
        yield_curve_state=yield_state,
        crude_oil=crude_val,
        crude_demand_destruction=demand_destruction,
        copper_gold_ratio=cg_ratio,
        industrial_momentum=ind_momentum,
        hy_credit_spread_proxy=credit_ratio,
        systemic_credit_risk=credit_risk,
        benchmark_name=benchmark_name,
        benchmark_price=bench_price,
        benchmark_change_pct=bench_chg,
        market_mood_label=mood_label,
        market_mood_color=mood_color,
        market_mood_desc=mood_desc,
    )
