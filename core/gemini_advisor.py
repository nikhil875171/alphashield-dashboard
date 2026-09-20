import os
from typing import Optional
from dotenv import load_dotenv
from core.schemas import (
    AlphaShieldRecommendation,
    FundamentalAudit,
    InstitutionalSnapshot,
    MacroSnapshot,
    RiskAllocation,
    SentimentSnapshot,
    TechnicalSnapshot,
)

load_dotenv()


def evaluate_alpha_shield(
    tech: TechnicalSnapshot,
    fund: FundamentalAudit,
    macro: MacroSnapshot,
    sent: SentimentSnapshot,
    inst: InstitutionalSnapshot,
    risk: RiskAllocation,
    model_name: str = "gemini-flash-latest"
) -> AlphaShieldRecommendation:
    """
    Submits aggregated multi-factor telemetry to Gemini with a strict Pydantic JSON schema.
    Provides automatic fallback to gemini-flash-latest and algorithmic rule engine on failure.
    """

    api_key = os.getenv("GEMINI_API_KEY")

    # If no API key or default placeholder, provide an algorithmic rule-based fallback
    if not api_key or api_key.strip() == "YOUR_GEMINI_API_KEY_HERE":
        return _generate_algorithmic_fallback(tech, fund, macro, sent, inst, risk)

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)

    prompt = f"""
    Act as the Chief Risk Officer and Senior Portfolio Manager of an elite multi-strategy hedge fund.
    Analyze this comprehensive quantitative dossier for {tech.symbol} and issue an institutional trading mandate.

    === 1. TECHNICAL MICROSTRUCTURE & MOMENTUM ===
    - Current Price: ₹/{tech.current_price} (Day Change: {tech.change_pct}%)
    - EMAs: 20-EMA=₹/{tech.ema_20}, 50-EMA=₹/{tech.ema_50}, 200-EMA=₹/{tech.ema_200}
    - Trend Alignment: {'BULLISH (Price > 20 > 50 > 200)' if tech.current_price > tech.ema_20 > tech.ema_50 else 'BEARISH/CONSOLIDATING'}
    - Momentum: RSI(14)={tech.rsi_14}, MACD={tech.macd} (Signal={tech.macd_signal})
    - VWAP: ₹/{tech.vwap} (Delta: {round(tech.current_price - tech.vwap, 2)})
    - Volatility: ATR(14)=₹/{tech.atr_14}
    - Liquidity & Volume: ADV(20)={tech.adv_20d:,}, Volume Surge={tech.volume_surge_ratio}x, Slippage Impact={tech.estimated_spread_impact_pct}%

    === 2. FUNDAMENTAL HEALTH & SOLVENCY SIEVE ===
    - Altman Z-Score: {fund.altman_z_score} [{fund.altman_zone}]
    - Piotroski F-Score: {fund.piotroski_f_score}/9 [{fund.piotroski_grade}]
    - Debt-to-Equity: {fund.debt_to_equity}x | ROE: {fund.roe}% | ROIC: {fund.roic}%
    - Operating Cash Flow: ₹/{fund.operating_cash_flow if fund.operating_cash_flow else 'N/A'}
    - Audit Warnings: {'; '.join(fund.audit_notes) if fund.audit_notes else 'None'}

    === 3. MACROECONOMIC & GEOPOLITICAL REGIME ===
    - Macro Regime: {macro.macro_regime}
    - Volatility Kill-Switch Active: {macro.volatility_kill_switch_active}
    - US 10Y Yield: {macro.yield_10y}% | 10Y-2Y Spread: {macro.yield_spread_10y_2y}%
    - Fear Index (VIX): {macro.vix} | DXY: {macro.dxy}
    - Commodities: Crude Oil=${macro.crude_oil}, Gold=${macro.gold}
    - Macro Headlines: {'; '.join(macro.top_headlines[:2])}

    === 4. SENTIMENT & INSTITUTIONAL FOOTPRINT ===
    - Crowd/News Sentiment: {sent.sentiment_label} (Score: {sent.sentiment_score})
    - Retail Euphoria Warning: {sent.retail_euphoria_flag} (Triggered if sentiment euphoric while RSI overbought)
    - Institutional Holding: {inst.institutional_ownership_pct}% | Insider Holding: {inst.insider_ownership_pct}%
    - Short Float: {inst.short_float_pct}% | Signal: {inst.institutional_signal}

    === 5. PRE-CALCULATED QUANTITATIVE RISK PARAMETERS ===
    - Entry Price: ₹/{risk.entry_price}
    - Algorithmic Hard Stop Loss (1.8x ATR): ₹/{risk.stop_loss_price}
    - Target Price Tier 1: ₹/{risk.target_price_1}
    - Risk-to-Reward Ratio: {risk.risk_reward_ratio_1}:1 (Minimum Required: 2.5:1)
    - Fixed Fractional Position: {risk.position_size_shares} shares (Risking {risk.risk_pct_selected}% of capital)

    === INSTITUTIONAL DECISION RULES ===
    1. If Volatility Kill-Switch is TRUE or Altman Z-score is in 'Distress (< 1.81)', ACTION MUST BE 'AVOID' or 'HOLD'.
    2. If Retail Euphoria is TRUE, treat high RSI as an immediate exhaustion risk and enforce caution.
    3. Do NOT approve a BUY unless the Risk-to-Reward ratio is at least 2.5:1.
    4. Target Price Ladder must contain 2 or 3 distinct asymmetric profit targets.
    5. Provide a rigorous, hedge-fund caliber thesis breakdown across Technical, Fundamental, Macro, and Sentiment.
    6. List 2 to 4 concrete, falsifiable kill-switch conditions that would instantly invalidate the trade.
    """

    models_to_try = [model_name, "gemini-flash-lite-latest", "gemini-3.1-flash-lite", "gemini-flash-latest"]
    # De-duplicate while preserving order
    unique_models = []
    for m in models_to_try:
        if m and m not in unique_models:
            unique_models.append(m)

    for current_model in unique_models:
        try:
            response = client.models.generate_content(
                model=current_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_json_schema=AlphaShieldRecommendation.model_json_schema(),
                    temperature=0.15,
                ),
            )
            return AlphaShieldRecommendation.model_validate_json(response.text)
        except Exception as err:
            continue

    print("[!] All Gemini models busy. Falling back to algorithmic rule engine.")
    return _generate_algorithmic_fallback(tech, fund, macro, sent, inst, risk)




def _generate_algorithmic_fallback(
    tech: TechnicalSnapshot,
    fund: FundamentalAudit,
    macro: MacroSnapshot,
    sent: SentimentSnapshot,
    inst: InstitutionalSnapshot,
    risk: RiskAllocation
) -> AlphaShieldRecommendation:
    """Algorithmic rule engine when API key is not supplied or during connection downtime."""
    # Kill switch conditions
    kill_switches = []
    if macro.volatility_kill_switch_active:
        kill_switches.append(f"VIX spike to {macro.vix} triggers automatic risk-off cash posture.")
    if fund.altman_zone == "Distress (< 1.81)":
        kill_switches.append(f"Altman Z-Score ({fund.altman_z_score}) flags severe financial distress.")
    if sent.retail_euphoria_flag:
        kill_switches.append("Retail euphoria divergence against overbought RSI(14) > 70.")
    if tech.current_price < tech.ema_200:
        kill_switches.append("Price trading below 200-day long-term structural EMA.")

    # Action logic
    if macro.volatility_kill_switch_active or fund.altman_zone == "Distress (< 1.81)":
        action = "AVOID"
        conviction = 0.85
        regime = "DEFENSIVE"
    elif sent.retail_euphoria_flag or tech.rsi_14 > 72:
        action = "HOLD"
        conviction = 0.65
        regime = "NEUTRAL"
    elif (
        tech.current_price > tech.ema_20 > tech.ema_50
        and tech.rsi_14 > 45
        and tech.rsi_14 < 68
        and risk.asymmetric_rr_passed
        and fund.altman_zone != "Distress (< 1.81)"
    ):
        action = "BUY"
        conviction = 0.78
        regime = "EXPANSION"
    elif tech.current_price < tech.ema_50 and tech.macd < tech.macd_signal:
        action = "SELL"
        conviction = 0.72
        regime = "DEFENSIVE"
    else:
        action = "HOLD"
        conviction = 0.50
        regime = "NEUTRAL"

    # Targets
    target_1 = risk.target_price_1
    target_2 = round(target_1 + (tech.atr_14 * 2.0), 2)
    target_3 = round(target_2 + (tech.atr_14 * 3.0), 2)

    entry_low = round(tech.current_price * 0.992, 2)
    entry_high = round(tech.current_price * 1.008, 2)

    return AlphaShieldRecommendation(
        ticker=tech.symbol,
        action=action,
        conviction_score=conviction,
        risk_regime=regime,
        recommended_entry_range=(entry_low, entry_high),
        hard_stop_loss=risk.stop_loss_price,
        target_price_ladder=[target_1, target_2, target_3],
        max_recommended_allocation_pct=round(min(risk.portfolio_allocation_pct, 15.0), 2) if action == "BUY" else 0.0,
        risk_reward_ratio=risk.risk_reward_ratio_1,
        multi_factor_thesis={
            "Technical": f"Price at ₹{tech.current_price}. EMA 20={tech.ema_20}, RSI={tech.rsi_14}, Volume surge={tech.volume_surge_ratio}x.",
            "Fundamental": f"Altman Z={fund.altman_z_score} ({fund.altman_zone}), Piotroski F-Score={fund.piotroski_f_score}/9.",
            "Macro": f"Regime: {macro.macro_regime}. VIX at {macro.vix}, 10Y-2Y yield spread at {macro.yield_spread_10y_2y}%.",
            "Sentiment": f"{sent.sentiment_label} (Euphoria flag: {sent.retail_euphoria_flag}). Institutional holding: {inst.institutional_ownership_pct}%."
        },
        primary_kill_switches=kill_switches if kill_switches else [
            f"Close below hard stop ₹{risk.stop_loss_price}",
            "Daily volume breakdown below 50% of 20-day ADV",
            "Sudden macroeconomic VIX surge above 25.0"
        ]
    )

