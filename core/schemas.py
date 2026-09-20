from typing import Dict, List, Literal, Optional, Tuple
from pydantic import BaseModel, Field


class MacroSnapshot(BaseModel):
    """Macroeconomic and geopolitical metrics."""
    yield_10y: float
    yield_short: float
    yield_spread_10y_2y: float
    vix: float
    dxy: float
    crude_oil: float
    gold: float
    macro_regime: Literal["DEFENSIVE", "NEUTRAL", "EXPANSION"]
    volatility_kill_switch_active: bool
    top_headlines: List[str] = Field(default_factory=list)


class FundamentalAudit(BaseModel):
    """Fundamental health and solvency sieve metrics."""
    debt_to_equity: Optional[float] = None
    operating_cash_flow: Optional[float] = None
    roic: Optional[float] = None
    roe: Optional[float] = None
    altman_z_score: Optional[float] = None
    altman_zone: Literal["Safe (> 2.99)", "Grey (1.81 - 2.99)", "Distress (< 1.81)", "Data Unavailable"]
    piotroski_f_score: Optional[int] = None
    piotroski_grade: Literal["Strong (7-9)", "Moderate (4-6)", "Weak (0-3)", "Data Unavailable"]
    audit_notes: List[str] = Field(default_factory=list)


class TechnicalSnapshot(BaseModel):
    """Technical momentum, volatility, and microstructure metrics."""
    symbol: str
    current_price: float
    previous_close: float
    change_pct: float
    ema_20: float
    ema_50: float
    ema_200: float
    rsi_14: float
    macd: float
    macd_signal: float
    vwap: float
    atr_14: float
    volume: int
    adv_20d: int
    volume_surge_ratio: float
    estimated_spread_impact_pct: float
    dynamic_stop_1_5x: float
    dynamic_stop_2_0x: float


class SentimentSnapshot(BaseModel):
    """Crowdsourced and financial news sentiment."""
    sentiment_score: float = Field(description="Normalized between -1.0 and 1.0")
    sentiment_label: Literal["EXTREME_BEARISH", "BEARISH", "NEUTRAL", "BULLISH", "EXTREME_BULLISH"]
    retail_euphoria_flag: bool = Field(description="True if retail sentiment is overly bullish while RSI is overbought")
    recent_news: List[Dict[str, str]] = Field(default_factory=list)


class InstitutionalSnapshot(BaseModel):
    """Institutional / smart money metrics."""
    institutional_ownership_pct: Optional[float] = None
    insider_ownership_pct: Optional[float] = None
    short_float_pct: Optional[float] = None
    institutional_signal: str


class RiskAllocation(BaseModel):
    """Quantitative risk management and position sizing calculation."""
    account_size: float
    risk_pct_selected: float
    risk_capital_amount: float
    entry_price: float
    stop_loss_price: float
    per_share_risk: float
    position_size_shares: int
    total_allocated_capital: float
    portfolio_allocation_pct: float
    target_price_1: float
    risk_reward_ratio_1: float
    asymmetric_rr_passed: bool
    volatility_kill_switch_forced: bool
    risk_verdict: str


class AlphaShieldRecommendation(BaseModel):
    """Pydantic model for Gemini Pro structured trade decision."""
    ticker: str
    action: Literal["BUY", "SELL", "HOLD", "AVOID"]
    conviction_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Conviction level between 0.0 (zero conviction) and 1.0 (absolute conviction)"
    )
    risk_regime: Literal["DEFENSIVE", "NEUTRAL", "EXPANSION"]
    recommended_entry_range: Tuple[float, float] = Field(
        description="Low and high recommended entry boundary, e.g. (1220.0, 1235.0)"
    )
    hard_stop_loss: float = Field(
        description="Strict ATR-derived hard stop-loss level"
    )
    target_price_ladder: List[float] = Field(
        description="Target price ladder with 2 or 3 asymmetric exit tiers"
    )
    max_recommended_allocation_pct: float = Field(
        ge=0.0,
        le=100.0,
        description="Maximum suggested portfolio allocation percentage based on conviction and regime"
    )
    risk_reward_ratio: float = Field(
        description="Target 1 Risk-to-Reward ratio (e.g. 2.8 or 3.2)"
    )
    multi_factor_thesis: Dict[str, str] = Field(
        description="Breakdown of technical, fundamental, macro, and sentiment factors"
    )
    primary_kill_switches: List[str] = Field(
        description="Explicit conditions that instantly invalidate the trade thesis"
    )

