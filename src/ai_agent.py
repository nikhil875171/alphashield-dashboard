import os
from typing import Dict, List, Literal, Optional, Tuple
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from src.macro_engine import MacroRegimeState
from src.microstructure import MicrostructureValidation
from src.factor_model import FactorScoreSummary
from src.risk_engine import ExecutionRiskReport

load_dotenv()


class InstitutionalTradePlan(BaseModel):
    """Institutional Trade Plan schema for Gemini Pro."""
    ticker: str
    action: Literal["BUY", "SELL", "HOLD", "AVOID"]
    conviction_score: float = Field(ge=0.0, le=1.0)
    macro_regime: str
    factor_grades: Dict[str, float]  # Value, Quality, Momentum, Microstructure
    solvency_audit: Dict[str, float]  # Z-score, F-score, Sloan Accruals
    entry_price_range: Tuple[float, float]
    algorithmic_stop_loss: float
    target_ladder: List[float]
    calculated_shares: int
    risk_reward_ratio: float
    detected_traps_or_warnings: List[str]
    supply_chain_spillovers: List[str]
    execution_kill_switches: List[str]


def generate_institutional_trade_plan(
    ticker: str,
    macro: MacroRegimeState,
    micro: MicrostructureValidation,
    factors: FactorScoreSummary,
    traps: List[str],
    spillovers: Dict[str, List[str]],
    risk: ExecutionRiskReport,
    model_name: str = "gemini-flash-lite-latest"
) -> InstitutionalTradePlan:
    """
    Submits aggregated institutional quant telemetry to Gemini Pro and validates against InstitutionalTradePlan schema.
    Provides automated model cascading and algorithmic fallback.
    """
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key or api_key.strip() == "YOUR_GEMINI_API_KEY_HERE":
        return _build_algorithmic_trade_plan(ticker, macro, micro, factors, traps, spillovers, risk)

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)

    prompt = f"""
    Act as the Chief Investment Officer (CIO) and Head of Quantitative Risk.
    Analyze the multi-asset transmission signals, order flow microstructure, and quantitative factor sieve below for {ticker}.
    Synthesize an institutional trade plan strictly adhering to our zero-ruin capital preservation policy.

    === 1. CROSS-ASSET & MACRO TRANSMISSION ===
    - Macro Regime: {macro.regime_label} (Liquidity Bias: {macro.liquidity_bias:+.2f})
    - Volatility Status: VIX={macro.vix} [{macro.vix_tier}] (Position Scale: {macro.position_scale_factor}x)
    - Yield Curve Spread: {macro.yield_spread}% [{macro.yield_curve_state}]
    - DXY RoC (20d): {macro.dxy_20d_roc}% | Crude Oil: ${macro.crude_oil} (Demand Destruction: {macro.crude_demand_destruction})
    - Copper/Gold Ratio: {macro.copper_gold_ratio} ({macro.industrial_momentum})
    - High-Yield Credit Spread Proxy: {macro.hy_credit_spread_proxy} ({macro.systemic_credit_risk})
    - Active Macro Headwinds: {'; '.join(macro.active_macro_headwinds) if macro.active_macro_headwinds else 'None'}

    === 2. CAPITAL PRESERVATION SIEVE & MULTI-FACTOR MODEL ===
    - Sieve Verdict: {factors.sieve_verdict}
    - Altman Z-Score (Bankruptcy): {factors.altman_z_score} (Threshold: < 1.81 is Insolvent)
    - Piotroski F-Score (Health): {factors.piotroski_f_score}/9 (Threshold: >= 6 Long, <= 3 Reject)
    - Sloan Accrual Ratio: {factors.sloan_accrual_ratio * 100:.2f}% (Threshold: > 10% is Earnings Hazard)
    - Factor Grades: Value={factors.factor_grades.get('Value')}, Quality={factors.factor_grades.get('Quality')}, Momentum={factors.factor_grades.get('Momentum')}, Microstructure={factors.factor_grades.get('Microstructure')}
    - Sieve Rejections: {'; '.join(factors.sieve_rejection_reasons) if factors.sieve_rejection_reasons else 'None'}

    === 3. MICROSTRUCTURE & INSTITUTIONAL FLOW ===
    - Estimated Delivery %: {micro.delivery_pct}% (Valid: {micro.delivery_valid})
    - Institutional Confluence: {micro.institutional_confluence} ({micro.institutional_confluence_msg})
    - Options Flow: PCR={micro.put_call_ratio} [{micro.pcr_regime}]
    - Max Pain Strike: ₹{micro.max_pain_strike} | Call Resistance Wall: ₹{micro.call_resistance_wall} | Put Wall: ₹{micro.put_support_wall}
    - Estimated Bid-Ask Spread: {micro.estimated_bid_ask_spread_pct}% (Liquidity Valid: {micro.liquidity_passed})
    - Microstructure Warnings: {'; '.join(micro.microstructure_warnings) if micro.microstructure_warnings else 'None'}

    === 4. HEURISTIC TRAP & FAILURE MODE DETECTOR ===
    - Active Traps Detected: {'; '.join(traps) if traps else 'None (Clean Setup)'}

    === 5. SECTORAL SPILLOVER & SUPPLY CHAIN TREE ===
    - Theme: {', '.join(spillovers.get('theme', []))}
    - Upstream Beneficiaries: {', '.join(spillovers.get('upstream_positive', [])[:2])}
    - Downstream Beneficiaries: {', '.join(spillovers.get('downstream_positive', [])[:2])}
    - Negative Spillovers: {', '.join(spillovers.get('negative_spillovers', [])[:2])}

    === 6. MATHEMATICAL RISK & POSITION SIZING ===
    - Entry Price: ₹{risk.entry_price}
    - Algorithmic Hard Stop Loss (ATR Scaled): ₹{risk.algorithmic_stop_loss}
    - Calculated Position Size: {risk.calculated_shares:,} shares (Allocating ₹{risk.allocated_capital:,.2f} = {risk.portfolio_allocation_pct}% of equity)
    - Maximum Portfolio Equity at Risk: ₹{risk.max_equity_at_risk:,.2f} (Strictly 1.0% cap)
    - Asymmetric Risk-to-Reward Ratio: {risk.risk_reward_ratio}:1 (Passed >= 2.5: {risk.asymmetric_rr_passed})
    - Execution Verdict: {risk.execution_verdict}

    === STRICT INSTITUTIONAL MANDATES ===
    1. If factors.sieve_verdict != 'PASS', ACTION MUST BE 'AVOID'.
    2. If macro.regime_label == 'VOLATILITY_HALT', ACTION MUST BE 'AVOID' and calculated_shares must be 0.
    3. If any fatal trap (Exhaustion Trap or Cyclical Value Trap) is active, downgrade BUY to HOLD or AVOID.
    4. Provide entry_price_range as a tight tuple [low_entry, high_entry] around current spot price.
    5. List 2-4 concrete, falsifiable kill-switches that immediately invalidate the trade.
    """

    models_to_try = [model_name, "gemini-flash-lite-latest", "gemini-3.1-flash-lite", "gemini-flash-latest", "gemini-3.6-flash"]
    unique_models = []
    for m in models_to_try:
        if m and m not in unique_models:
            unique_models.append(m)

    for m in unique_models:
        try:
            response = client.models.generate_content(
                model=m,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_json_schema=InstitutionalTradePlan.model_json_schema(),
                    temperature=0.15,
                ),
            )
            return InstitutionalTradePlan.model_validate_json(response.text)
        except Exception:
            continue

    return _build_algorithmic_trade_plan(ticker, macro, micro, factors, traps, spillovers, risk)


def _build_algorithmic_trade_plan(
    ticker: str,
    macro: MacroRegimeState,
    micro: MicrostructureValidation,
    factors: FactorScoreSummary,
    traps: List[str],
    spillovers: Dict[str, List[str]],
    risk: ExecutionRiskReport
) -> InstitutionalTradePlan:
    """Algorithmic fallback rule engine producing an InstitutionalTradePlan without API dependency."""
    # Sieve & Trap rejection conditions
    all_warnings = list(traps) + list(micro.microstructure_warnings) + list(factors.sieve_rejection_reasons)
    
    # Kill switch formulation
    kill_switches = [
        f"Breach of algorithmic hard stop at ₹{risk.algorithmic_stop_loss}",
        "Volume drop below 50% of 20-day ADV on breakout candle",
        f"Macro regime shift to VOLATILITY_HALT (VIX > 32)"
    ]

    # Action determination
    if factors.sieve_verdict != "PASS" or macro.regime_label == "VOLATILITY_HALT":
        action = "AVOID"
        conviction = 0.85
    elif len(traps) > 0 or not micro.delivery_valid or not risk.asymmetric_rr_passed:
        action = "HOLD"
        conviction = 0.65
    elif (
        factors.composite_factor_score >= 60.0
        and risk.asymmetric_rr_passed
        and macro.regime_label in ["EXPANSION", "NEUTRAL"]
    ):
        action = "BUY"
        conviction = round(min(0.92, (factors.composite_factor_score / 100.0) + 0.15), 2)
    else:
        action = "HOLD"
        conviction = 0.50

    entry_low = round(risk.entry_price * 0.995, 2)
    entry_high = round(risk.entry_price * 1.005, 2)

    # Flatten spillovers
    spillover_summary = []
    if "upstream_positive" in spillovers:
        spillover_summary.extend(spillovers["upstream_positive"][:2])
    if "downstream_positive" in spillovers:
        spillover_summary.extend(spillovers["downstream_positive"][:2])
    if "negative_spillovers" in spillovers:
        spillover_summary.extend(spillovers["negative_spillovers"][:1])

    return InstitutionalTradePlan(
        ticker=ticker,
        action=action,
        conviction_score=conviction,
        macro_regime=macro.regime_label,
        factor_grades=factors.factor_grades,
        solvency_audit=factors.solvency_audit,
        entry_price_range=(entry_low, entry_high),
        algorithmic_stop_loss=risk.algorithmic_stop_loss,
        target_ladder=risk.target_ladder,
        calculated_shares=risk.calculated_shares if action == "BUY" else 0,
        risk_reward_ratio=risk.risk_reward_ratio,
        detected_traps_or_warnings=all_warnings if all_warnings else ["No active structural traps detected."],
        supply_chain_spillovers=spillover_summary if spillover_summary else ["Direct sector transmission."],
        execution_kill_switches=kill_switches,
    )

