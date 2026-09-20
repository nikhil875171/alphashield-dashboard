import os
from typing import Dict, List, Literal, Optional, Tuple
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from src.macro_engine import MacroRegimeState
from src.microstructure import MicrostructureValidation
from src.factor_model import FactorScoreSummary
from src.risk_engine import ExecutionRiskReport
from src.thematic_engine import ThematicProfile, audit_thematic_profile
from src.supply_chain_graph import SupplierRippleResult, get_supplier_ripple_effect
from src.ancillary_screener import AncillaryMetrics, screen_ancillary_supplier

load_dotenv()


class FullInstitutionalTradePlan(BaseModel):
    """Unified Institutional Trade Plan schema enforcing macro, thematic, and supply chain intelligence."""
    ticker: str
    company_name: str = "Enterprise Issuer"
    market_exchange: Literal["US", "INDIA"]
    currency_symbol: Literal["$", "₹"]
    action: Literal["BUY", "ACCUMULATE", "HOLD", "AVOID"]
    plain_english_bottom_line: str = Field(description="Max 25-word jargon-free summary for beginners")
    primary_risk_warning: str = Field(description="The #1 danger to watch out for in plain English")
    conviction_score: float = Field(ge=0.0, le=1.0)
    time_horizon: Literal["1_YEAR", "3_YEARS", "5_YEARS", "10_YEARS", "20_YEARS"]
    thematic_pillar: str = Field(description="e.g., AI Edge, Power Grid, Nuclear Baseload, Water Scarcity, Humanoid Robotics")
    is_anchor_or_ancillary: Literal["ANCHOR_OEM", "TIER_1", "TIER_2", "TIER_3"]
    connected_anchors: List[str] = Field(description="List of anchor OEMs driving demand to this company")
    operating_leverage_score: float = Field(ge=0.0, le=5.0)
    customer_concentration_pct: float = Field(description="Percentage of revenue tied to primary anchor OEM")
    scarcity_transmission_vector: Literal["WATER", "CLEAN_AIR", "ORE_DEPLETION", "POWER_GRID", "NONE"]
    macro_regime_label: str = "EXPANSION"
    solvency_status: Literal["PRISTINE", "STABLE", "DEBT_BURDENED", "INSOLVENT_DISTRESS"]
    altman_z_score: float
    piotroski_f_score: int
    sloan_accrual_pct: float
    recommended_entry_range: Tuple[float, float]
    algorithmic_stop_loss: float
    target_price_ladder: List[float]
    calculated_shares_to_buy: int
    risk_reward_ratio: float = 2.5
    detected_traps_or_warnings: List[str]
    execution_kill_switches: List[str]

    def __init__(self, **data):
        # Support legacy argument names seamlessly
        if "market" in data and "market_exchange" not in data:
            data["market_exchange"] = data["market"]
        if "currency" in data and "currency_symbol" not in data:
            data["currency_symbol"] = data["currency"]
        if "plain_english_verdict" in data and "plain_english_bottom_line" not in data:
            data["plain_english_bottom_line"] = data["plain_english_verdict"]
        if "primary_danger" in data and "primary_risk_warning" not in data:
            data["primary_risk_warning"] = data["primary_danger"]
        if "thematic_horizon" in data and "time_horizon" not in data:
            data["time_horizon"] = data["thematic_horizon"]
        if "thematic_driver" in data and "thematic_pillar" not in data:
            data["thematic_pillar"] = data["thematic_driver"]
        if "supply_chain_role" in data and "is_anchor_or_ancillary" not in data:
            data["is_anchor_or_ancillary"] = data["supply_chain_role"]
        if "anchor_oem_dependencies" in data and "connected_anchors" not in data:
            data["connected_anchors"] = data["anchor_oem_dependencies"]
        if "operating_leverage_multiplier" in data and "operating_leverage_score" not in data:
            data["operating_leverage_score"] = data["operating_leverage_multiplier"]
        if "resource_scarcity_exposure" in data and "scarcity_transmission_vector" not in data:
            data["scarcity_transmission_vector"] = data["resource_scarcity_exposure"]
        if "sloan_accrual_ratio" in data and "sloan_accrual_pct" not in data:
            data["sloan_accrual_pct"] = data["sloan_accrual_ratio"]
        if "entry_price_range" in data and "recommended_entry_range" not in data:
            data["recommended_entry_range"] = data["entry_price_range"]
        if "target_ladder" in data and "target_price_ladder" not in data:
            data["target_price_ladder"] = data["target_ladder"]
        if "calculated_shares" in data and "calculated_shares_to_buy" not in data:
            data["calculated_shares_to_buy"] = data["calculated_shares"]
        if "detected_traps" in data and "detected_traps_or_warnings" not in data:
            data["detected_traps_or_warnings"] = data["detected_traps"]
        if "company_name" not in data:
            data["company_name"] = data.get("ticker", "Enterprise Issuer")
        if "macro_regime_label" not in data:
            data["macro_regime_label"] = "EXPANSION"
        if "risk_reward_ratio" not in data:
            data["risk_reward_ratio"] = 2.5
        super().__init__(**data)

    # Backwards compatibility properties
    @property
    def plain_english_verdict(self) -> str:
        return self.plain_english_bottom_line

    @plain_english_verdict.setter
    def plain_english_verdict(self, val: str):
        self.plain_english_bottom_line = val

    @property
    def primary_danger(self) -> str:
        return self.primary_risk_warning

    @primary_danger.setter
    def primary_danger(self, val: str):
        self.primary_risk_warning = val

    @property
    def market(self) -> str:
        return self.market_exchange

    @property
    def currency(self) -> str:
        return self.currency_symbol

    @property
    def thematic_horizon(self) -> str:
        return self.time_horizon

    @property
    def thematic_driver(self) -> str:
        return self.thematic_pillar

    @property
    def supply_chain_role(self) -> str:
        return self.is_anchor_or_ancillary

    @property
    def anchor_oem_dependencies(self) -> List[str]:
        return self.connected_anchors

    @property
    def operating_leverage_multiplier(self) -> float:
        return self.operating_leverage_score

    @property
    def resource_scarcity_exposure(self) -> str:
        return self.scarcity_transmission_vector

    @property
    def sloan_accrual_ratio(self) -> float:
        return self.sloan_accrual_pct

    @property
    def entry_price_range(self) -> Tuple[float, float]:
        return self.recommended_entry_range

    @property
    def target_ladder(self) -> List[float]:
        return self.target_price_ladder

    @property
    def calculated_shares(self) -> int:
        return self.calculated_shares_to_buy

    @calculated_shares.setter
    def calculated_shares(self, val: int):
        self.calculated_shares_to_buy = val

    @property
    def detected_traps(self) -> List[str]:
        return self.detected_traps_or_warnings

    @property
    def max_capital_at_risk(self) -> float:
        return round(self.calculated_shares_to_buy * abs(self.recommended_entry_range[0] - self.algorithmic_stop_loss), 2)

    @property
    def macro_regime(self) -> str:
        return self.macro_regime_label


# Backwards compatibility alias
InstitutionalTradePlan = FullInstitutionalTradePlan


def generate_institutional_trade_plan(
    ticker: str,
    macro: MacroRegimeState,
    micro: MicrostructureValidation,
    factors: FactorScoreSummary,
    traps: List[str],
    spillovers: Dict[str, List[str]],
    risk: ExecutionRiskReport,
    thematic: Optional[ThematicProfile] = None,
    ancillary: Optional[AncillaryMetrics] = None,
    ripple: Optional[SupplierRippleResult] = None,
    model_name: str = "gemini-flash-lite-latest",
) -> FullInstitutionalTradePlan:
    """
    Submits aggregated institutional quant, macro, and supply-chain telemetry to Gemini Pro
    and validates against FullInstitutionalTradePlan schema.
    Provides automated model cascading and algorithmic fallback.
    """
    # Ensure helper profiles exist
    if thematic is None:
        thematic = audit_thematic_profile(ticker)
    if ancillary is None:
        ancillary = screen_ancillary_supplier(ticker)
    if ripple is None:
        ripple = get_supplier_ripple_effect(ticker)

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key.strip() == "YOUR_GEMINI_API_KEY_HERE":
        return _build_algorithmic_trade_plan(ticker, macro, micro, factors, traps, spillovers, risk, thematic, ancillary, ripple)

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)

    is_indian = ticker.endswith(".NS") or ticker.endswith(".BO")
    market_str = "INDIA" if is_indian else "US"
    currency_str = "₹" if is_indian else "$"

    prompt = f"""
    Act as the Chief Investment Officer (CIO) and Head of Quantitative Risk.
    Analyze the multi-asset transmission signals, order flow microstructure, supply chain position, and factor sieve below for {ticker}.
    Synthesize an institutional trade plan strictly adhering to our zero-ruin capital preservation policy.

    === 1. CROSS-ASSET & MACRO TRANSMISSION ===
    - Macro Regime: {macro.regime_label} (Liquidity Bias: {macro.liquidity_bias:+.2f})
    - Volatility Status: VIX={macro.vix} [{macro.vix_tier}] (Position Scale: {macro.position_scale_factor}x)
    - Yield Curve Spread: {macro.yield_spread}% [{macro.yield_curve_state}]
    - Benchmark: {macro.benchmark_name} at {macro.benchmark_price} ({macro.benchmark_change_pct:+.2f}%)
    - Active Macro Headwinds: {'; '.join(macro.active_macro_headwinds) if macro.active_macro_headwinds else 'None'}

    === 2. CAPITAL PRESERVATION SIEVE & MULTI-FACTOR MODEL ===
    - Sieve Verdict: {factors.sieve_verdict}
    - Altman Z-Score: {factors.altman_z_score} (Distress < 1.81)
    - Piotroski F-Score: {factors.piotroski_f_score}/9
    - Sloan Accrual Ratio: {factors.sloan_accrual_ratio * 100:.2f}% (Threshold: > 10% is Earnings Hazard)

    === 3. SUPPLY CHAIN & THEMATIC HORIZON ===
    - Thematic Wave: {thematic.horizon_title} ({thematic.timeframe})
    - Supply Chain Role: {ripple.role} in {ripple.case_name}
    - Connected Anchor OEMs: {', '.join(ripple.connected_anchors)}
    - Operating Leverage: {ancillary.operating_leverage_multiplier}x ({ancillary.operating_leverage_grade})
    - Customer Concentration: {ancillary.customer_concentration_pct}%
    - Resource Scarcity Exposure: {thematic.resource_scarcity_exposure}

    === 4. MICROSTRUCTURE & RISK EXECUTION ===
    - Delivery Validation: {micro.delivery_valid} (Delivery: {micro.delivery_pct:.1f}%)
    - Entry Price: {currency_str}{risk.entry_price} | Hard Stop: {currency_str}{risk.algorithmic_stop_loss}
    - Targets: {[f"{currency_str}{t}" for t in risk.target_ladder]}
    - Risk/Reward: {risk.risk_reward_ratio:.2f}:1 (Gate: >= 2.5:1, Passed: {risk.asymmetric_rr_passed})
    - Maximum Shares to Allocate: {risk.calculated_shares}
    - Max Equity at Risk: {currency_str}{risk.max_equity_at_risk:.2f}

    Format response strictly as JSON compliant with the requested FullInstitutionalTradePlan schema.
    Provide a plain-English, beginner-friendly verdict under 25 words and a clear primary danger statement.
    """

    candidate_models = [model_name, "gemini-flash-lite-latest", "gemini-3.1-flash-lite", "gemini-flash-latest"]
    unique_models = []
    for m in candidate_models:
        if m and m not in unique_models:
            unique_models.append(m)

    for model in unique_models:
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=FullInstitutionalTradePlan,
                    temperature=0.1,
                ),
            )
            if response.parsed:
                return response.parsed
        except Exception:
            continue

    return _build_algorithmic_trade_plan(ticker, macro, micro, factors, traps, spillovers, risk, thematic, ancillary, ripple)


def _build_algorithmic_trade_plan(
    ticker: str,
    macro: MacroRegimeState,
    micro: MicrostructureValidation,
    factors: FactorScoreSummary,
    traps: List[str],
    spillovers: Dict[str, List[str]],
    risk: ExecutionRiskReport,
    thematic: ThematicProfile,
    ancillary: AncillaryMetrics,
    ripple: SupplierRippleResult,
) -> FullInstitutionalTradePlan:
    """Algorithmic fallback rule engine producing a FullInstitutionalTradePlan without external API dependency."""
    is_indian = ticker.endswith(".NS") or ticker.endswith(".BO")
    m_code: Literal["US", "INDIA"] = "INDIA" if is_indian else "US"
    curr_code: Literal["$", "₹"] = "₹" if is_indian else "$"

    # Solvency status determination
    if factors.altman_z_score >= 2.99 and factors.piotroski_f_score >= 7:
        solv: Literal["PRISTINE", "STABLE", "DEBT_BURDENED", "INSOLVENT_DISTRESS"] = "PRISTINE"
    elif factors.altman_z_score >= 1.81 and factors.piotroski_f_score >= 5:
        solv = "STABLE"
    elif factors.altman_z_score >= 1.81:
        solv = "DEBT_BURDENED"
    else:
        solv = "INSOLVENT_DISTRESS"

    # Action determination
    if factors.sieve_verdict != "PASS" or macro.regime_label == "VOLATILITY_HALT":
        action: Literal["BUY", "ACCUMULATE", "HOLD", "AVOID"] = "AVOID"
        conviction = 0.85
        verdict = f"High solvency or macro volatility hazard detected. Capital preservation rules strictly forbid entering {ticker} now."
        danger = f"Financial stress or volatility halt: {factors.sieve_rejection_reasons[0] if factors.sieve_rejection_reasons else 'VIX panic'}"
    elif len(traps) > 0 or not risk.asymmetric_rr_passed:
        action = "HOLD"
        conviction = 0.65
        verdict = f"{ticker} has solid fundamentals, but wait for a clean pullback into safe entry range before buying."
        danger = f"Active market trap or sub-2.5x odds: {traps[0] if traps else 'Upside does not justify downside'}"
    elif factors.composite_factor_score >= 65.0 and risk.asymmetric_rr_passed and micro.delivery_valid:
        action = "BUY"
        conviction = round(min(0.92, (factors.composite_factor_score / 100.0) + 0.15), 2)
        verdict = f"High-conviction buy: {ticker} passed all solvency sieves with strong institutional accumulation and {risk.risk_reward_ratio:.1f}x odds."
        danger = f"If price breaches algorithmic stop at {curr_code}{risk.algorithmic_stop_loss}, exit immediately without hesitation."
    else:
        action = "ACCUMULATE"
        conviction = 0.60
        verdict = f"Accumulate gradually in the entry zone; company benefits from the {thematic.horizon_title} secular wave."
        danger = f"Monitor the {thematic.resource_scarcity_exposure} supply bottleneck and maintain strict stop at {curr_code}{risk.algorithmic_stop_loss}."

    role_val: Literal["ANCHOR_OEM", "TIER_1", "TIER_2", "TIER_3"] = (
        ripple.role if ripple.role in ["ANCHOR_OEM", "TIER_1", "TIER_2", "TIER_3"] else "TIER_1"
    )

    kill_switches = [
        f"Breach of algorithmic hard stop at {curr_code}{risk.algorithmic_stop_loss}",
        "Volume drop below 50% of 20-day ADV on breakout candle",
        "Macro regime shift to VOLATILITY_HALT (VIX > 32)"
    ]

    return FullInstitutionalTradePlan(
        ticker=ticker,
        market=m_code,
        currency=curr_code,
        action=action,
        plain_english_verdict=verdict,
        primary_danger=danger,
        conviction_score=conviction,
        thematic_horizon=thematic.horizon_code,
        thematic_driver=thematic.thematic_driver,
        supply_chain_role=role_val,
        anchor_oem_dependencies=ripple.connected_anchors,
        operating_leverage_multiplier=ancillary.operating_leverage_multiplier,
        customer_concentration_pct=ancillary.customer_concentration_pct,
        resource_scarcity_exposure=thematic.resource_scarcity_exposure,
        solvency_status=solv,
        altman_z_score=factors.altman_z_score,
        piotroski_f_score=factors.piotroski_f_score,
        sloan_accrual_ratio=factors.sloan_accrual_ratio,
        entry_price_range=(round(risk.entry_price * 0.995, 2), round(risk.entry_price * 1.005, 2)),
        algorithmic_stop_loss=risk.algorithmic_stop_loss,
        target_ladder=risk.target_ladder,
        calculated_shares=risk.calculated_shares if action in ["BUY", "ACCUMULATE"] else 0,
        max_capital_at_risk=risk.max_equity_at_risk,
        execution_kill_switches=kill_switches,
        detected_traps=traps if traps else ["No active structural traps detected."],
    )
